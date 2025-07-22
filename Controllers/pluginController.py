from typing import Optional
from io import BytesIO
import os
from docx import Document
from Model.pluginModel import Model
import fitz  
import re
from fastapi import HTTPException, status
from sentence_transformers import SentenceTransformer
from Model.WoocommerceBotModel import get_Woo_model_response
from Model.FAQBotModel import get_FAQ_model_response
import re

async def generate_embeddings(text:str):
    model =SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(text)
    print("embedding generation complete")
    print(embeddings)
    return embeddings

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])

def convert_response_to_html(text_response: str) -> str:
    """
    Converts a plain text/markdown response to HTML format.
    
    Args:
        text_response (str): The plain text response from the LLM
        
    Returns:
        str: HTML formatted response
    """
    if not text_response:
        return ""
    
    # Split text into lines
    lines = text_response.split('\n')
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        
        if not line:  # Empty line
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append('<br>')
            continue
            
        # Check if line starts with bullet point (- or *)
        if re.match(r'^[-*]\s', line):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            
            # Extract content after bullet point
            content = re.sub(r'^[-*]\s', '', line)
            
            # Make text between ** bold
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            
            html_lines.append(f'    <li>{content}</li>')
            
        else:  # Regular paragraph
            if in_list:
                html_lines.append('</ul>')
                in_list = False
                
            # Make text between ** bold
            line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            
            # Wrap in paragraph tags
            html_lines.append(f'<p>{line}</p>')
    
    # Close any remaining list
    if in_list:
        html_lines.append('</ul>')
    
    return '\n'.join(html_lines)

def split_text(text, max_chunk_size=500, overlap=50):
    sentences = re.split(r'(?<=[.!?]) +', text)  # split on sentences
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chunk_size:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = " ".join(current_chunk.split()[-overlap:]) + " " + sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks



async def getchunks(text: str, site_id: str):
    chunks = split_text(text)
    document = []
    collection = Model()

    if collection is None:
        print("Connection not established")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not established."
        )

    try:
        delete_result = collection.delete_many({"site_id": site_id, "for": "blogSites"})
        print(f"Deleted {delete_result.deleted_count} existing chunks for site_id: {site_id}")
    except Exception as e:
        print(f"Failed to delete existing chunks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear existing chunks: {str(e)}"
        )

    for i, chunk in enumerate(chunks):
        print("Chunking...")
        vector = await generate_embeddings(chunk)
        embedding = vector.tolist()
        doc = {
            "site_id": site_id,
            "for":"blogSites",
            "chunk_number": i,
            "text": chunk,
            "embeddings": embedding
        }
        document.append(doc)

    if not document:
        print("No chunks were generated")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No chunks were generated from the text."
        )

    # Insert new chunks
    try:
        collection.insert_many(document)
        print(f"Inserted {len(document)} chunks into MongoDB.")
        return {"message": f"Inserted {len(document)} chunks into database."}
    except Exception as e:
        print(f"Failed to insert documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to insert documents into database: {str(e)}"
        )



# CHAT PROCESSING OF THE PLUGIN


async def chunking_function(documents, userquery ,chat_history):
    """Processes a document and retrieves surrounding chunks for enhanced context."""
    print("Processing document with chunking function:", documents)

    combined_context = ""
    if not documents:
        return f"User query: {userquery}\n\nNo relevant context found."

    relevant_chunk = documents[0]  
    site_id = relevant_chunk['site_id']

    current_chunk_number_raw = relevant_chunk.get('chunk_number')
    current_chunk_number = None
    if isinstance(current_chunk_number_raw, dict) and '$numberInt' in current_chunk_number_raw:
        current_chunk_number = int(current_chunk_number_raw['$numberInt'])
    elif isinstance(current_chunk_number_raw, (int, str)) and str(current_chunk_number_raw).isdigit():
        current_chunk_number = int(current_chunk_number_raw)

    if current_chunk_number is None:
        combined_context = relevant_chunk['text']
    else:
        combined_context += f"{relevant_chunk['text']}\n\n"
        previous_chunk_number = current_chunk_number - 1
        if previous_chunk_number >= 1:
            previous_chunk = await fetch_chunk_from_db(site_id, str(previous_chunk_number))
            if previous_chunk:
                combined_context = f"{previous_chunk['text']}\n\n" + combined_context

        next_chunk_number = current_chunk_number + 1
        next_chunk = await fetch_chunk_from_db(site_id, str(next_chunk_number))
        if next_chunk:
            combined_context += f"{next_chunk['text']}"

    final_prompt = f"User query: {userquery} with the chat history: {chat_history}\n\nContext from relevant and surrounding chunks:\n{combined_context}"

    print("Combined prompt for LLM:", final_prompt)
    results = get_FAQ_model_response(userquery, final_prompt)
    print("THE FINAL RESULTS       " , results)
    return results

# for fetching a chunk from the database
async def fetch_chunk_from_db(site_id, chunk_number):

    print(f"Fetching chunk with site_id: {site_id} and chunk_number: {chunk_number} from DB...")
    return None


async def woocommerce_function(documents,userquery, chat_history):
    """Processes a list of documents from the WooCommerce product data."""
    print("Processing WooCommerce products with woocommerce function:", documents)
    results = []
    combined_str = "" 

    for doc in documents:
        print("Processing ID:", doc.get('id'))
        combined_str += (
            f"ID: {doc.get('id', 'N/A')}\n"
            f"Name: {doc.get('name')}\n"
            f"Description: {doc.get('description', 'No description available')}\n"
            f"Short Description: {doc.get('short_description', 'No Short description available')}"
            f"Price: {doc.get('price')}\n"
            f"Stock Status: {doc.get('stock_status', 'Unknown')}\n"
            f"Permalink: {doc.get('permalink', 'No permalink available')}\n"
            "\n--------------------\n"
        )
    
    print("Combined product data:\n", combined_str)
    results = get_Woo_model_response(userquery, combined_str, chat_history)
    
    return results  # Return a list of results



async def generate_embeddings(text:str):
    model =SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(text)
    print("embedding generation complete")
    print(embeddings)
    return embeddings

async def response_generator(chat_text: str, site_id: str, chat_history: list = None):
    client = Model()

    chat_embedding = await generate_embeddings(chat_text)


    vector = [float(x) for x in chat_embedding]

    print("Performing vector search...")
    print("site_id:", site_id)
    print("Query Vector (first 5 elements):", vector[:5]) 
    print("About to execute client.aggregate()...")
    try:
        results = list(client.aggregate([
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embeddings",
                    "queryVector": vector,
                    "numCandidates": 100,
                    "limit": 5,
                    "filter": { 
                        "site_id": {"$eq": site_id}  
                    }
                }
            }
        ]))
        print("Vector search call finished.")
        print("Vector search complete. Results:")
    except Exception as e:
        print(f"Error during vector search: {e}")
        return ["Error during vector search."] 

    print("Results:")
    responses = []
    if results:  
        best_match = results[0]
        best_match_id = str(best_match["_id"])
        best_match["id"] = best_match_id
        print("Best match ID")

        if "for" in best_match and best_match["for"] == "blogSites":
            chunked_data_response = await chunking_function([best_match], chat_text,chat_history) # Corrected call
            responses.append(chunked_data_response)
        elif "for" in best_match and best_match["for"] == "WooCommerce":
            woocommerce_products = [result for result in results if "for" in result and result["for"] == "WooCommerce"]
            woocommerce_data_response = await woocommerce_function(woocommerce_products, chat_text,chat_history)
            responses.append(woocommerce_data_response)
        else:
            responses.append(f"Error: Unknown 'for' value in best match: {best_match.get('for', 'N/A')}. Best Match: {best_match}")
    else:
        responses.append("No matching results found.") 

    print("Final responses:", responses[0])
    return responses

