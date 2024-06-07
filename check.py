import psycopg2
import os 
from dotenv import load_dotenv
load_dotenv()
def fetch_data():
    connection = psycopg2.connect(
        dbname='RPF-RAG',
        user='postgres',
        password='@bhijeet911',
        host='localhost',
    )
    cursor = connection.cursor()
    
    # SQL to fetch data
    cursor.execute("SELECT * FROM text_chunks")
    #cursor.execute("SELECT * FROM qa_library ")
    records = cursor.fetchall()
    
    for record in records:
        print(record)
    
    cursor.close()
    connection.close()

fetch_data() 