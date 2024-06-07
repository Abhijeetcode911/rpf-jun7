import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import psycopg2
import os
import uuid
import pypandoc
from dotenv import load_dotenv
from docx import Document
from pinecone_embbeding import fetch_new_text_chunks, embed_and_store
#import comtypes.client
import csv
from io import StringIO

load_dotenv()
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

#for docekr
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
def setup_environment():
    import pypandoc
    try:
        # Ensure Pandoc is available
        _ = pypandoc.get_pandoc_path()
    except OSError:
        # Download Pandoc if it's not installed
        pypandoc.download_pandoc()
setup_environment()
# Call this function early in your application startup

def extract_text_from_docx(file_content):
    doc = Document(io.BytesIO(file_content))
    full_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            image_stream = io.BytesIO(rel.target_part.blob)
            image = Image.open(image_stream)
            ocr_text = pytesseract.image_to_string(image)
            full_text += ocr_text
    full_text = remove_newlines(full_text)
    text_by_page = []
    text_by_page.append((full_text,1))
    return text_by_page

# def extract_text_from_pdf(doc):
#     full_text = ""
#     for page_number in range(len(doc)):
#         page = doc.load_page(page_number)
#         text = page.get_text("text")
#         full_text += text
#         image_list = page.get_images(full=True)
#         for img_index, img in enumerate(image_list):
#             xref = img[0]
#             base_image = doc.extract_image(xref)
#             image_bytes = base_image["image"]
#             image = Image.open(io.BytesIO(image_bytes))
#             ocr_text = pytesseract.image_to_string(image)
#             full_text += ocr_text
#     full_text = remove_newlines(full_text)     
#     return full_text

def remove_newlines(input_string):
    return input_string.replace('\n', '')

# def store_chunks(text_chunks, filename):
#     connection = psycopg2.connect(
#             dbname='rpf',
#             user='postgres',
#             password='12345678',
#             host='localhost',
#         )
#     cursor = connection.cursor()
#     for chunk in text_chunks:
#         chunk_uuid = str(uuid.uuid4())
#         chunk = remove_newlines(chunk)
#         #cursor.execute("INSERT INTO text_chunks (uuid, chunk_text, file_name) VALUES (%s, %s, %s)", (chunk_uuid, chunk, filename))
#         cursor.execute("INSERT INTO  text_chunks (chunk_text, file_name) VALUES (%s, %s)", (chunk, filename))
#     connection.commit()
#     cursor.close()
#     connection.close()
# def store_chunks(text_chunks, filename):
#     connection = psycopg2.connect(
#         dbname='RPF-RAG',
#         user='postgres',
#         password='@bhijeet911',
#         host='localhost',
#     )
#     cursor = connection.cursor()
#     for chunk, page_number in text_chunks:
#         chunk_uuid = str(uuid.uuid4())
#         chunk = chunk.replace('\n', '')
#         cursor.execute(
#             "INSERT INTO text_chunks (uuid, chunk_text, file_name, page_number) VALUES (%s, %s, %s, %s)",
#             (chunk_uuid, chunk, filename, page_number)
#         )
#     connection.commit()
#     cursor.close()
#     connection.close()
def store_chunks(text_chunks, filename):
    connection = psycopg2.connect(
        dbname='RPF-RAG',
        user='postgres',
        password='@bhijeet911',
        host='localhost',
    )
    cursor = connection.cursor()
    
    # Preparing the SQL command to insert data, including a 'processed' column set to False
    sql_command = """
        INSERT INTO text_chunks (uuid, chunk_text, file_name, page_number, processed)
        VALUES (%s, %s, %s, %s, %s)
    """
    
    for chunk, page_number in text_chunks:
        chunk_uuid = str(uuid.uuid4())
        # Remove newline characters from chunk text
        chunk = chunk.replace('\n', '')
        # Execute the SQL command, passing False for the 'processed' column
        cursor.execute(sql_command, (chunk_uuid, chunk, filename, page_number, False))
    
    # Commit changes to the database
    connection.commit()
    # Close the cursor and the connection
    cursor.close()
    connection.close()

# def chunk_text(text, chunk_size=500):
#     return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# def process_file(contents, filename):
#     if filename.endswith('.pdf'):
#         doc = fitz.open("pdf", contents)
#         full_text = extract_text_from_pdf(doc)
#         print(full_text)
#     elif filename.endswith('.docx'):
#         full_text = extract_text_from_docx(contents)
#     else:
#         raise ValueError("Unsupported file format")
   
#     text_chunks = chunk_text(full_text)
#     store_chunks(text_chunks, filename)
#     text_chunks= fetch_new_text_chunks()
#     embed_and_store(text_chunks)

# def process_file(contents, filename):
#     if filename.endswith('.pdf'):
#         # Convert PDF pages to images and merge into a single PDF
#         contents = convert_pdf_to_image_pdf(contents)
#         doc = fitz.open("pdf", contents)
#         full_text = extract_text_from_pdf_image(doc)
#         print(full_text)
#     elif filename.endswith('.docx'):
#         full_text = extract_text_from_docx(contents)
#     else:
#         raise ValueError("Unsupported file format")
    
#     # Placeholder for your additional text processing functions
#     text_chunks = chunk_text(full_text)
#     store_chunks(text_chunks, filename)
#     text_chunks = fetch_new_text_chunks()
#     embed_and_store(text_chunks)

# def docx_to_pdf(docx_path, pdf_path):
#     # Create a COM object to interact with Microsoft Word
#     word = comtypes.client.CreateObject('Word.Application')
#     word.Visible = False  # Run Word in the background

#     # Open the DOCX file
#     doc = word.Documents.Open(docx_path)
#     try:
#         # Save the document as PDF
#         doc.SaveAs(pdf_path, FileFormat=17)  # 17 corresponds to the PDF format in Word
#     finally:
#         # Clean up: close the document and quit Word
#         doc.Close()
#         word.Quit()
#     return pdf_path


# def extract_text_from_pdf_image(doc):
#     full_text = ""
#     for page_number in range(len(doc)):
#         page = doc.load_page(page_number)
#         pix = page.get_pixmap()
#         image = Image.open(io.BytesIO(pix.tobytes("png")))
#         ocr_text = pytesseract.image_to_string(image)
#         full_text += ocr_text
#     full_text = full_text.replace('\n', ' ')     
#     return full_text

def process_file(contents, filename):
    if filename.endswith('.pdf'):
        contents = convert_pdf_to_image_pdf(contents)
        doc = fitz.open("pdf", contents)
        text_chunks = extract_text_from_pdf_image(doc)
    elif filename.endswith('.docx'):
        text_chunks = extract_text_from_docx(contents)
    else:
        raise ValueError("Unsupported file format")
    
    store_chunks(text_chunks, filename)
    text_chunks = fetch_new_text_chunks()
    embed_and_store(text_chunks)

def extract_text_from_pdf_image(doc):
    text_by_page = []
    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        text = page.get_text("text")
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            ocr_text = pytesseract.image_to_string(image)
            text += ocr_text
            text = remove_newlines(text)
        text_by_page.append((text, page_number + 1))
    return text_by_page

def convert_pdf_to_image_pdf(contents):
    doc = fitz.open("pdf", contents)
    merged_doc = fitz.open()  # Create a new PDF document
    
    for page in doc:
        pix = page.get_pixmap()  # Render page to an image
        img_pdf = fitz.open()  # Create a new PDF to hold this image
        # Convert the pixmap to a PDF page
        img_pdf.new_page(width=pix.width, height=pix.height)
        page = img_pdf[0]
        page.insert_image(page.rect, pixmap=pix)
        merged_doc.insert_pdf(img_pdf)  # Insert the single-image PDF into the merged document
        img_pdf.close()

    img_pdf_bytes = io.BytesIO()
    merged_doc.save(img_pdf_bytes)
    merged_doc.close()
    doc.close()
    return img_pdf_bytes.getvalue()



def process_csv_file(content, filename):
    # Decode the content (which is in bytes) to a string
    content_string = content.decode('utf-8')
    
    # Use StringIO to simulate a file object for csv.reader
    csv_file = StringIO(content_string)
    
    # Create a CSV reader object
    reader = csv.reader(csv_file)
    
    # Initialize a list to store text chunks from the first column
    text_chunks = []
    
    # Iterate over rows in the CSV file
    for row in reader:
        if row:  # Ensure the row is not empty
            text_chunks.append((remove_newlines(row[0]),0))  # Add the first column to text_chunks
    
    # For demonstration, print the text_chunks
    print(f"Processed {filename}:")
    print(len(text_chunks))

    store_chunks(text_chunks, filename)
    text_chunks = fetch_new_text_chunks()
    embed_and_store(text_chunks)

    # Implement further logic as needed
    # For example, you can store these chunks somewhere or perform additional processing