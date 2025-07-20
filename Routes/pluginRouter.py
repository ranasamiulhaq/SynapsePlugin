from fastapi import APIRouter,Request,File,UploadFile,HTTPException,Form
from Controllers.pluginController import extract_text_from_docx,extract_text_from_pdf,getchunks,response_generator
from Controllers.apiController import process_woocommerce_products

import os


router=APIRouter()

@router.post('/doc')
async def getdoc(file: UploadFile = File(...) , site_id:str=Form(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    contents = await file.read()
    print(f"Received site_id: {site_id}")

    try:
        if ext == '.txt':
            text = contents.decode('utf-8')
        elif ext == '.pdf':
            text = extract_text_from_pdf(contents)
        elif ext == '.docx':
            text = extract_text_from_docx(contents)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    return await getchunks(text,site_id)


@router.post('/manual')
async def upload_manual(
    site_id: str = Form(...),
    manual_faq: str = Form(...)
):
    if not manual_faq.strip():
        raise HTTPException(status_code=400, detail="Manual FAQ content cannot be empty.")

    print(f"Received manual FAQ content: {manual_faq[:500]}...")

    result = await getchunks(manual_faq, site_id)
    return result

@router.post("/api")
async def receive_and_process_products(request: Request):
    """
    Receives WooCommerce product data from the WordPress plugin,
    processes it (generates embeddings and stores in the database).
    """
    return await process_woocommerce_products(request)

@router.post('/chat')
async def post_chat(request: Request):
    data = await request.json()
    site_id = data.get("site_id")
    message = data.get("message")
    chat_history = data.get("chat_history") 

    if not site_id or not message:
        return {"error": "Both 'site_id' and 'message' are required."}

    try:
        response_data = await response_generator(message, site_id, chat_history)
        return {"response": response_data} 
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}