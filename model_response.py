from openai import OpenAI 
import asyncio
from dotenv import load_dotenv
import os
import json
load_dotenv()

# Retrieve API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

async def stream_llm_response(prompt, top_p=0.8, length=4000, temperature=0, model_name="gpt-4-turbo"):
    Instruction = """
    You have given an input JSON(Example input)  object with a query and 5 data elements(chunk,pdf_name,page_number) process the JSON object and return the answer and relevant chunks as the JSON object shown below(Example output). Keep in mind that the relevant chunk can be from 0 to 5 hence mention the output object accordingly. 
    If the answer is not found in the chunks then
    Return 
    { "relevant_chunks": [], "answer": "No relevant information was found in the provided data." }

    Example input: { "query": "Placeholder text for a query", "data": [ { "chunk": "Placeholder text for the first research finding or topic summary.", "pdf_name": "placeholder_for_pdf_name_1.pdf", "page_number": "placeholder_page_number_1" }, { "chunk": "Placeholder text summarizing a study on the impact of new materials or techniques.", "pdf_name": "placeholder_for_pdf_name_2.pdf", "page_number": "placeholder_page_number_2" }, { "chunk": "Placeholder text discussing revolutionary changes or improvements in a certain field.", "pdf_name": "placeholder_for_pdf_name_3.pdf", "page_number": "placeholder_page_number_3" }, { "chunk": "Placeholder text regarding regulations or standards affecting industry practices.", "pdf_name": "placeholder_for_pdf_name_4.pdf", "page_number": "placeholder_page_number_4" }, { "chunk": "Placeholder text on future trends and innovations in a broad context.", "pdf_name": "placeholder_for_pdf_name_5.pdf", "page_number": "placeholder_page_number_5" } ] }


    Example output: { "relevant_chunks": [ { "chunk": "Placeholder text 1.", "pdf_name": "placeholder_for_pdf_name_1.pdf", "page_number": "placeholder_page_number_1", "useful_sentences": [ "Placeholder sentence 1.", "Placeholder sentence 2" ] }, { "chunk": "Placeholder text 2", "pdf_name": "placeholder_for_pdf_name_2.pdf", "page_number": "placeholder_page_number_2", "useful_sentences": [ "Placeholder sentence 1 for second chuk.", "Placeholder sentence 2 for second chunk" ] } ], "answer": "for the answer" }
"""

   
    messages = [
        {
            'role': 'system',
            'content': Instruction
        },
        {
            'role': 'user',
            'content': prompt
        }
    ]
    #print("yes")
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=length,
        top_p=top_p,
        # stream=True,
        seed=12345
    )
    #print("response", response)
    return response.choices[0].message.content


def gpt4_response(prompt,top_p=0.9, length=750, temperature=0, model_name="gpt-4-turbo"):
    messages = [{'role': 'system',
                 'content': 'You are a QnA chatbot, you have been provided user query and revelevnt information related to the query. Based on the information provide answer to the query. Donot make things up, only answer from the relevant information provided, if something can not be answered based on the relevant information, say that you cannot answer it. Answer comprehensively but make it as concise as possible. Answer only what is asked. Donot return the user query as part of the answer.'},
                {'role': 'user', 'content': prompt.lower()}]

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=length,
        top_p=top_p,
 
        # Set stream parameter to True
    )

    return response.choices[0].message.content


# Function to process and stream responses for all results
def process_and_stream_all(result):
        #print("Querying model for result:", result)
        return  stream_llm_response(result)