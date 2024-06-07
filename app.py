from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse,FileResponse
from typing import List
from extract_text_store import *
from pinecone_embbeding import *
from remove import delete_entries_from_pinecone,delete_entries_from_postgresql
from query import *
from fastapi.middleware.cors import CORSMiddleware
from model_response import *
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
#from save_qna import *
import os
import logging
import uuid
import pandas as pd
import numpy as np


from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionAnswer(BaseModel):
    question: str
    answer: str

        
def validate_file(file: UploadFile):
    # Validate file extension
    if not (file.filename.endswith('.pdf') or file.filename.endswith('.docx')):
        raise HTTPException(status_code=400, detail="File must be a PDF or DOCX")

# async def handle_file(content: bytes, filename: str):
#     try:
#         if filename.endswith('.pdf'):
#             print("sent")
#             process_file(content, filename)
#         elif filename.endswith('.docx'):
#             process_file(content, filename)
#     except Exception as e:
#         # Log the error or handle it as needed
#         print(f"Error processing file {filename}: {e}")
async def handle_file(content: bytes, filename: str):
    try:
        process_file(content, filename)
    except Exception as e:
        print(f"Error processing file {filename}: {e}")

# get request to check ping
@app.get("/")
async def ping():
    return "App running successfully!"

# @app.post("/upload-files/")
# async def upload_file(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
#     responses = []
#     for file in files:
#         validate_file(file)  # Validate each file before processing
#         content = await file.read()  # Read file content immediately
#         background_tasks.add_task(handle_file, content, file.filename)  # Pass the read content
#         responses.append(f"{file.filename} is being processed")
#     return {"message": "Files are being processed", "details": responses}

# @app.post("/upload-files/")
# async def upload_file(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
#     responses = []
   
#     for file in files:
#         validate_file(file)  # Validate each file before processing
#         content = await file.read()  # Read file content immediately    
       
#         # Save file to disk
#         save_path = f"./static/files/{file.filename}"
#         os.makedirs(os.path.dirname(save_path), exist_ok=True)
#         with open(save_path, 'wb') as f:
#             f.write(content)
       
#         # Pass the content to the background task
        
#         background_tasks.add_task(handle_file, content, file.filename)
      
#         responses.append(f"{file.filename} is being processed")

#     return {"message": "Files are being processed!", "details": responses}

# @app.post("/upload-files/")
# async def upload_file(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
#     responses = []
    
#     for file in files:

#         content = await file.read()  # Read file content immediately    
       
#         # Save file to disk
#         save_path = f"./static/files/{file.filename}"
#         os.makedirs(os.path.dirname(save_path), exist_ok=True)
#         with open(save_path, 'wb') as f:
#             f.write(content)
       
#         # Pass the content to the background task
#         background_tasks.add_task(process_file, content, file.filename)
#         responses.append(f"{file.filename} is being processed")
#     return {"message": "Files are being processed!", "details": responses}
@app.post("/upload-files/")
async def upload_file(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    responses = []
    
    for file in files:
        content = await file.read()  # Read file content immediately
        filename, file_extension = os.path.splitext(file.filename)

        # Save file to disk
        save_path = f"./static/files/{file.filename}"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(content)

        # Check if the file is a CSV
        if file_extension.lower() == '.csv':
            # Pass the content to a different function specifically for CSV files
            background_tasks.add_task(process_csv_file, content, file.filename)
            responses.append(f"{file.filename} is being processed as a CSV")
        else:
            # Pass the content to the general processing function
            background_tasks.add_task(process_file, content, file.filename)
            responses.append(f"{file.filename} is being processed")

    return {"message": "Files are being processed!", "details": responses}


@app.post("/delete-file/")
async def delete_file(file_name: str):
    """FastAPI endpoint to delete entries associated with a specific PDF from PostgreSQL and Pinecone."""
    if not (file_name.endswith('.pdf') or file_name.endswith('.docx')):
        raise HTTPException(status_code=400, detail="Filename must end with '.pdf' or '.docx")
    
    # Fetch and delete entries from PostgreSQL
    deleted_ids = delete_entries_from_postgresql(file_name)

    # Delete corresponding entries from Pinecone
    delete_entries_from_pinecone(deleted_ids)

    return {"message": f"Entries related to {file_name} have been deleted from both PostgreSQL and Pinecone."}

        
# @app.post("/uploadexcel/")       
# async def create_upload_file(file: UploadFile = File(...)):
#     if not file:
#             raise HTTPException(status_code=400, detail="No file provided")
#     questions = extract_text_from_excel(file.file)
#     questions = process_questions(json_string_to_list(questions))
#     print(type( questions))
#     return {"message": "here are the list of questions ", "details": questions}
@app.post("/uploadexcel/")
async def create_upload_file(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Read the file content into memory
    file_content = await file.read()
    
    # Extract text from the Excel file
    questions = extract_text_from_excel(file_content)
    
    # Assuming process_questions and json_string_to_list are defined
    # Convert JSON string back to list
    question_list = json.loads(questions)
    processed_questions = process_questions(question_list)
    
    print(type(processed_questions))
    return {"message": "Here are the list of questions", "details": processed_questions}

# def extract_text_from_excel(file_path):
   
#     # Load all sheets from the Excel file
#     xls = pd.ExcelFile(file_path)
#     all_texts = []
    
#     # Iterate over all sheets
#     for sheet_name in xls.sheet_names:
#         df = pd.read_excel(xls, sheet_name=sheet_name)
        
#         # Iterate over all cells in the DataFrame
#         for col in df.columns:
#             for item in df[col]:
#                 if pd.notna(item):  # Check if the cell is not NaN
#                     all_texts.append(remove_newlines((str(item))))  # Convert to string and append to list

#     # Serialize the list of strings into a JSON formatted string
#     json_text = json.dumps(all_texts)
#     #print(json_text)
#     return json_text

@app.post("/save-qna/")
async def save_qna(qna: QuestionAnswer):
    print("qna.question",qna.question)
    print("qna.answer",qna.answer)
    text = []
    text.append((qna.question + " " + qna.answer,0))
    store_chunks(text, "savedQnA")
    text_chunks = fetch_new_text_chunks()
    embed_and_store(text_chunks)
    return {"message": "Question and Answer saved successfully"}

class QueryRequest(BaseModel):
    query: str

@app.post("/processquery/")
async def process_query(request_data: QueryRequest):
    query = request_data.query
    if not query:
        raise HTTPException(status_code=400, detail="No query provided")
    
    # Process the query
    try:
        final_response,page_numbers,pdf_names,relevant_chunks = await process_all_questions(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # logging.info(f"Final response: {final_response}, PDF names: {pdf_names}")
    # async def stream(response):
    #     accumulated_response = ''
    #     try:
    #         for chunk in response:
    #             if 'choices' in chunk and chunk['choices']:
    #                 content = chunk['choices'][0].get('delta', {}).get('content', None)
    #                 if content is not None:
    #                     accumulated_response += content
    #                     yield "data: " + content + "\n\n"
    #     except Exception as e:
    #         yield "data: An error occurred: " + str(e) + "\n\n"

    # return StreamingResponse(stream(final_response), media_type='text/event-stream')  
    # return final_response
    
    # Ensure pdf_names contains unique strings
    filtered_pdf_names = [name for name in pdf_names if "savedQnA" not in name]
    print("filterpdf",filtered_pdf_names)
    unique_chunks=list(relevant_chunks)
    page_numbers = list(page_numbers)
    
    logging.info(f"Final response: {final_response}, PDF names: {pdf_names}")
    pdf_urls = [f"http://127.0.0.1:8000/static/files/{pdf_name}" for pdf_name in filtered_pdf_names]

    pdf_data=[
        {"url":pdf_urls[i],"pdf_name":pdf_names[i]}
        for i in range(len(pdf_urls))
    ]
    seen = set()
    unique_pdf_data = []
    for item in pdf_data:
        t = tuple(item.items())
        if t not in seen:
            seen.add(t)
            unique_pdf_data.append(item)
    
    logging.info(f"Unique PDF data: {unique_pdf_data}")

    print("unique_chunks",unique_chunks)
    print("page_numbers",page_numbers)


    chunk_objects = [
        {"chunk": unique_chunks[i], "fileUrl": pdf_urls[i], "pageno": page_numbers[i],"pdfName":pdf_names[i]}
        for i in range(len(pdf_data))
    ]
    print(pdf_names)

   
    # Return JSON response with all PDF URLs
    return JSONResponse(content={
        "id":str(uuid.uuid4()),
        "message": final_response,
        "pdf_data":unique_pdf_data,
        "Chunks":chunk_objects,
        "page":page_numbers,
    })

# Directory where PDF files are stored
PDF_DIRECTORY = "files"

@app.get("/getfile/")
async def get_file(filename: str):
    file_path = os.path.join(PDF_DIRECTORY, filename)
    print("file_path",file_path)


    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(path=file_path, filename=filename, media_type='application/pdf')