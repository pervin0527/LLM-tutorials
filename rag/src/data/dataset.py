import logging

import mysql.connector
from mysql.connector import Error

from uuid import uuid4
from langchain.docstore.document import Document

logger = logging.getLogger(__name__)

def connect_to_db(host="localhost", user="root", password="", database_name="test", port=8888):
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database_name,
            port=port
        )
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None
    
    return connection

def get_dataset(connection, query):
    if connection is None:
        print("Database connection not established")
        return None
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    dataset = cursor.fetchall()

    cursor.close()
    connection.close()

    return dataset


def get_documents(dataset, page_fields, metadata_fields):
    documents = []
    for data in dataset:
        page_content = ""
        for field in page_fields:
            page_content += f"{field}\n{data[field]}\n\n"

        metadata = {}
        for field in metadata_fields:
            metadata[field] = data[field]
            
        documents.append(Document(page_content=page_content, metadata=metadata, id=uuid4()))

    logger.info(f"Documents Successfully Loaded: {len(documents)}")

    return documents