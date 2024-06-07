import psycopg2
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

# Setup Pinecone
api_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key)
index_name = "rpfrag2"
index = pc.Index(name=index_name)

def delete_entries_from_postgresql(file_name):
    """Delete entries from PostgreSQL where the file_name matches the given PDF name."""
    connection = psycopg2.connect(
        dbname='RPF-RAG',
        user='postgres',
        password='@bhijeet911',
        host='localhost',
    )
    cursor = connection.cursor()
    # Deleting text chunks associated with the given PDF, using UUIDs
    cursor.execute("DELETE FROM text_chunks WHERE file_name = %s RETURNING uuid", (file_name,))
    deleted_uuids = [str(row[0]) for row in cursor.fetchall()]
    connection.commit()
    cursor.close()
    connection.close()
    return deleted_uuids

def delete_entries_from_pinecone(uuids):
    """Delete vector entries from Pinecone."""
    if uuids:
        index.delete(ids=uuids)