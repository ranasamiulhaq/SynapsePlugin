import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

def get_FAQ_model_response(user_query: str, combined_str: str):
    """
    Gets a response from a language model (OpenRouter) for a user query,
    given relevant document context. This version does NOT use conversation history.

    Args:
        user_query (str): The user's search query.
        combined_str (str): A string containing the combined text from the
                              most relevant document chunk and its neighbors (if found).

    Returns:
        str: The model's response, or None on error.
    """

    prompt = f"""You are a helpful and informative assistant. Your task is to answer the user's query based on the provided document context.

User Query:
{user_query}

Document Context:
{combined_str}

Instructions:
- Keep the conversation tone engaging with the user by responding to greetings only use context if neccessary . 
- Use the information from the "Document Context" to answer the "User Query" as accurately and completely as possible. If the "Context" does not contain the answer, state that you cannot find the answer within the provided information by simply saying "I cannot seem to find information that you are looking for."
- Be concise and avoid unnecessary details or conversational filler.
- Maintain a helpful and neutral tone.
- If the user asks a question that is not directly answerable from the context, do not speculate or make up information.
- If the "Document Context" contains multiple pieces of information, synthesize them to provide a comprehensive answer.
- Pay close attention to any specific instructions or keywords in the "User Query".

**Format Response in HTML:**
   - Format your entire response using proper HTML tags
   - Use <p> tags for paragraphs
   - Use <ul> and <li> tags for lists
   - Use <strong> or <b> tags for bold text
   - Use <a href="url" target="_blank"> tags for clickable links
   - Use <br> tags for line breaks where needed
   - Make the response visually appealing with proper HTML structure

    Example HTML format:
    <p>Here at Store we have several premium men's perfumes available! Based on your needs, I'd recommend trying either:</p>
    <ul>
        <li><strong>Product Name</strong>: Description here. <a href="product_link" target="_blank">View Product</a></li>
        <li><strong>Another Product</strong>: Description here. <a href="product_link" target="_blank">View Product</a></li>
    </ul>
    <p>Would you like more information about any of these products?</p>
    
    
"""

    data = {
        "model": "qwen/qwen3-235b-a22b:free",
        "messages": [
            {"role": "system", "content": "You are a helpful and informative assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500
    }

    print("Sending request to OpenRouter with data:", data)
    response = requests.post(API_URL, json=data, headers=headers)
    print("OpenRouter response status code:", response.status_code)
    response_json = response.json()

    if response.status_code == 200:
        response_text = response_json['choices'][0]['message']['content'].strip()
        print(response_text)
        return response_text
    else:
        print(f"Error: {response.status_code}")
        print("Failed Response")
        return None