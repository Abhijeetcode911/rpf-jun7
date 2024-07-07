import psycopg2
import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

load_dotenv()

api_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key)

# Connect to the existing index
index_name = "rpfrag2"
#if index_name not in pc.list_indexes().names():
   # pc.create_index(
   #     name=index_name,
   #     dimension=768,
    #    metric='cosine',
     #   spec=ServerlessSpec(
      #      cloud='azure',
       #     region='eastus'
        #)
   # )

index = pc.Index(name=index_name)
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

def fetch_new_text_chunks():
    connection = psycopg2.connect(
        dbname='RPF-RAG',
        user='postgres',
        password='password',
        host='localhost',
    )
    cursor = connection.cursor()
    cursor.execute("SELECT uuid, chunk_text FROM text_chunks WHERE processed = FALSE")
    text_chunks = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return text_chunks

def embed_and_store(text_chunks):
    batch_size = 32
    connection = psycopg2.connect(
        dbname='RPF-RAG',
        user='postgres',
        password='password',
        host='localhost',
    )
    cursor = connection.cursor()

    for i in range(0, len(text_chunks), batch_size):
        batch = text_chunks[i:i+batch_size]
        uuids = [str(chunk[0]) for chunk in batch]
        texts = [chunk[1] for chunk in batch]
        embeddings = model.encode(texts, show_progress_bar=True)

        items = [(uuid, emb.tolist() if hasattr(emb, 'tolist') else emb) for uuid, emb in zip(uuids, embeddings)]
        index.upsert(vectors=items)

        # Ensure UUIDs are properly cast when passed to SQL query
        cursor.execute(
            "UPDATE text_chunks SET processed = TRUE WHERE uuid = ANY(%s::uuid[])",
            (uuids,)
        )
    
    connection.commit()
    cursor.close()
    connection.close()
