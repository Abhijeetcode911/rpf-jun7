import psycopg2
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import numpy as np
from openai import OpenAI
import pandas as pd
from dotenv import load_dotenv
import os
from model_response import process_and_stream_all
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
import json
load_dotenv()
from io import BytesIO

api_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key)
index = pc.Index(name="rpfrag2")

# Initialize the Sentence Transformers Model
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

def search_similar_items(query_text, top_k=5):
    # Embed the query text
    query_embedding = model.encode([query_text])[0]
    
    # Convert numpy array to list if necessary
    if isinstance(query_embedding, np.ndarray):
        query_embedding = query_embedding.tolist()

    # Printing the type and part of the vector for troubleshooting
    print(f"Query vector type: {type(query_embedding)}, Example values: {query_embedding[:5]}")
    
    # Ensure the query embedding is properly formatted as a list of floats
    if not all(isinstance(x, float) for x in query_embedding):
        raise ValueError("Vector contains non-float values")

    try:
        # Submitting the query
        search_results = index.query(vector=[query_embedding], top_k=top_k)      
        ids = [hit['id'] for hit in search_results['matches']]
        print(ids)
        return ids
    except Exception as e:
        print(f"Error during query: {str(e)}")
        return []

def fetch_text_chunks(ids):
    # Ensure connection details such as database name, user, password, and host are correctly specified
    connection = psycopg2.connect(
        dbname='RPF-RAG',
        user='postgres',
        password='@bhijeet911',
        host='localhost',
    )
    cursor = connection.cursor()
    
    # Updated query to select the page_number as well
    query = "SELECT chunk_text, file_name, page_number FROM text_chunks WHERE uuid = ANY(%s::uuid[])"
    cursor.execute(query, (ids,))
    chunks = cursor.fetchall()
    cursor.close()
    connection.close()
    
    # Extracting chunk_text, file_name, and page_number from the fetched rows
    chunk_texts = [chunk[0] for chunk in chunks]
    pdf_names = [chunk[1] for chunk in chunks]
    page_numbers = [chunk[2] for chunk in chunks]

    return chunk_texts, pdf_names, page_numbers


    return chunk_texts, pdf_names

def process_query_and_get_results(query_text):
    # Search for similar items
    similar_ids = search_similar_items(query_text)
  
    # Fetch corresponding text chunks from PostgreSQL
    text_chunks = fetch_text_chunks(similar_ids)


    # Append query and chunks for output
    results = {'query': query_text, 'results': text_chunks}
    
    return results

# Retrieve API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

# def is_question(prompt,top_p=0.9, length=10, temperature=1, model_name='gpt-4-turbo'):
#     messages = [{'role': 'system',
#                  'content': 'You have to identify the sentence as an query or not. if it a query then return "1" else "0"'},
#                 {'role': 'user', 'content': prompt.lower()}]

#     response = client.chat.completions.create(
#         model=model_name,
#         messages=messages,
#         temperature=temperature,
#         max_tokens=length,
#         top_p=top_p,
 
#         # Set stream parameter to True
#     )

#     return response.choices[0].message.content

def is_question(prompt,top_p=0.9, length=4096, temperature=0, model_name='gpt-4-turbo'):
    messages = [{'role': 'system',
                 'content': """You are a bot which helps companies in answering prposal based queries. You need to read the text thoroughly. You are given a list of sentences, you have to read each sentence and identify if the sentence asks for details related to a proposal or not. Analyze each setnence very carefully, if there is a slight chance that it's a question/detail asked, add it to the json string. The sentence could be a question or could be a sentence asking for details about something. Add all these sentences/questions and return in a json string. If a question doesn't make much sense, but if it looks like a question, still add it in the json string. Donot return anything apart from what's in the text provided, donot try to answer any question.
            Example:
            Given : [“what are the security measure”, “it is a good idea to have it on filed”,”what things is on the list”,”we can use FFTT service”]
            Return [“what are the security measure”,“what things is on the list”]
                """},
                {'role': 'user', 'content': prompt}]

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=length,
        top_p=top_p,
 
        # Set stream parameter to True
    )

    return response.choices[0].message.content

def remove_newlines(input_string):
    return input_string.replace('\n', '')
# def extract_questions_from_excel(file_path):
#     # Load all sheets from the Excel file
#     xls = pd.ExcelFile(file_path)
#     questions = []

#     # Iterate over all sheets
#     for sheet_name in xls.sheet_names:
#         df = pd.read_excel(xls, sheet_name=sheet_name)
        
#         # Iterate over all cells in the DataFrame
#         for col in df.columns:
#             for item in df[col]:
#                 if pd.notna(item):  # Check if the cell is not NaN
#                     if is_question(str(item)) == "1":  # Convert to string in case the input is not
#                         questions.append(item)

#     return questions


# def extract_questions_from_excel(file_path):
#     # Load all sheets from the Excel file
#     xls = pd.ExcelFile(file_path)
#     questions = []

#     # Iterate over all sheets
#     for sheet_name in xls.sheet_names:
#         df = pd.read_excel(xls, sheet_name=sheet_name)
        
#         # Iterate over all cells in the DataFrame
#         for col in df.columns:
#             for item in df[col]:
#                 if pd.notna(item):  # Check if the cell is not NaN
#                     if is_question(str(item)) == "1":  # Convert to string in case the input is not
#                         questions.append(item)

#     return questions
#file_path = "query.xlsx"
def extract_text_from_excel(file_content):
    # Use BytesIO to wrap the binary content
    xls = pd.ExcelFile(BytesIO(file_content))
    all_texts = []
    
    # Iterate over all sheets
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Iterate over all cells in the DataFrame
        for col in df.columns:
            for item in df[col]:
                if pd.notna(item):  # Check if the cell is not NaN
                    all_texts.append(str(item).replace('\n', ' '))  # Convert to string, remove newlines, and append to list

    # Serialize the list of strings into a JSON formatted string
    json_text = json.dumps(all_texts)
    return json_text
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
#extract_text_from_excel(file_path)
def remove_newlines(input_string):
    return input_string.replace('\n', '')

def process_questions(questions):
    # Chunk questions into groups of 50
    chunks = [questions[i:i + 50] for i in range(0, len(questions), 50)]
    all_results = []
    for chunk in chunks:
        chunk_result = is_question(str(chunk))
        all_results = all_results + json_string_to_list(chunk_result)
    return all_results

# async def process_all_questions(question):

#     #print("questions",questions)
#     #for question in questions:
#         # Perform the similarity search for each question
#         similar_ids = search_similar_items(question)
#         print("similar_ids",similar_ids)
#         relevant_chunks, pdf_names , page_numbers = fetch_text_chunks(similar_ids)
#         print("relevant_chunks",relevant_chunks)
#         # print("relevant file ",pdf_names)
#         # Convert tuple results to strings if necessary
#         relevant_chunks = [chunk[0] if isinstance(chunk, tuple) else chunk for chunk in relevant_chunks]
#         print("relevant_chunks",relevant_chunks)
#         # Combine the question with its relevant chunks
#         combined_result = f"Query: {question}\n" + "\n".join(relevant_chunks)
#         print("combined_result",combined_result)
#         answer = await process_and_stream_all(combined_result)
#         return answer,page_numbers,pdf_names,relevant_chunks

# async def  process_all_questions(question):
#     similar_ids = search_similar_items(question)
#     print("similar_ids", similar_ids)
#     relevant_chunks, pdf_names, page_numbers = fetch_text_chunks(similar_ids)
#     print("relevant_chunks", relevant_chunks)

#     # Ensure all entries are strings and package data into structured JSON
#     data = []
#     for chunk, pdf_name, page_number in zip(relevant_chunks, pdf_names, page_numbers):
#         data.append({
#             "chunk": chunk[0] if isinstance(chunk, tuple) else chunk,
#             "pdf_name": pdf_name,
#             "page_number": page_number
#         })

#     combined_result = {
#         "query": question,
#         "data": data
#     }
#     json_string = json.dumps(combined_result)
#     #print("combined_result", json.dumps(combined_result, indent=2))
#     answer = await  process_and_stream_all(json_string)
#     #print(answer)
#     data = json.loads(answer)
#     most_relevant_chunk = data['most_relevant_chunk']
#     chunk = most_relevant_chunk['chunk']
#     pdf_name = most_relevant_chunk['pdf_name']
#     page_number = most_relevant_chunk['page_number']
#     most_useful_sentences = most_relevant_chunk['most_useful_sentences']
#     answer = data['answer']
#     print(type(answer))
#     print(type(most_useful_sentences))
#     print(type(pdf_name))
#     pdf_names = [pdf_name] 
#     page_numbers = [page_number]
#     print(type(page_numbers))
#     return answer,page_numbers,pdf_names,most_useful_sentences

async def process_all_questions(question):
    similar_ids = search_similar_items(question)
    print("similar_ids", similar_ids)
    relevant_chunks, pdf_names, page_numbers = fetch_text_chunks(similar_ids)
    print("relevant_chunks", relevant_chunks)

    # Ensure all entries are strings and package data into structured JSON
    data = []
    for chunk, pdf_name, page_number in zip(relevant_chunks, pdf_names, page_numbers):
        data.append({
            "chunk": chunk[0] if isinstance(chunk, tuple) else chunk,
            "pdf_name": pdf_name,
            "page_number": page_number
        })

    combined_result = {
        "query": question,
        "data": data
    }
    json_string = json.dumps(combined_result)
    answer_json = await process_and_stream_all(json_string)

    data = json.loads(answer_json)
    print(data)
    # Adjust for possible empty 'relevant_chunks'
    relevant_chunks = data.get('relevant_chunks', [])
    
    answers = []
    pdf_names = []
    page_numbers = []
    most_useful_sentences = []
    chunk_text = []
    
    # Check if relevant chunks are present
    if relevant_chunks:
            for chunk_info in relevant_chunks:
                chunk_text.append(chunk_info['chunk'])
                pdf_names.append(chunk_info['pdf_name'])
                page_numbers.append(chunk_info['page_number'])
                #most_useful_sentences.append(chunk_info['useful_sentences'])
                answers.append(data['answer'])    
    else:
        answers.append("No relevant information was found in the provided data.")
    for chunk_info in data['relevant_chunks']:
        pdf_name = chunk_info['pdf_name']
        # Check if the file extension is .csv
        if pdf_name.endswith('.csv'):
            # Replace useful_sentences with chunk text for each CSV file
            chunk_info['useful_sentences'] = [chunk_info['chunk']] * len(chunk_info['useful_sentences'])
            most_useful_sentences.append(chunk_info['useful_sentences'])
        else :
            most_useful_sentences.append(chunk_info['useful_sentences'])

    print(type(answers))
    print(type(most_useful_sentences))
    print(type(pdf_names))
    print(type(page_numbers))
    print(answers[0])
    return answers[0], page_numbers, pdf_names, most_useful_sentences

def json_string_to_list(json_string):
    # Deserialize the JSON string into a Python list
    result_list = json.loads(json_string)
    return result_list

#file_path = "query (1).xlsx"
#asyncio.run(process_all_questions(file_path))