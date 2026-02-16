import os
import logging
from typing import List

import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from tqdm import tqdm  

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_SOURCE_DIR = os.path.join(BASE_DIR, "../raw_files")

CHROMA_HOST = os.getenv("CHROMA_HOST", "nutrition_facts_chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
COLLECTION_NAME = "nutrition_knowledge"

EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEVICE = "cpu" 

CHUNK_SIZE = 800  
CHUNK_OVERLAP = 150  


def get_chroma_client():
    """ChromaDB sunucusuna bağlanır ve istemciyi döndürür."""
    logger.info(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
    try:
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=Settings(allow_reset=True, anonymized_telemetry=False),
        )
        # Bağlantı testi
        client.heartbeat()
        logger.info("Successfully connected to ChromaDB.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {e}")
        raise


def setup_collection(client: chromadb.HttpClient, reset: bool = True):
    """Koleksiyonu hazırlar. Reset=True ise eski veriyi siler."""
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.warning(f"Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            pass  

    return client.get_or_create_collection(COLLECTION_NAME)


def load_and_process_pdfs(directory: str) -> List[Document]:
    """PDF dosyalarını bulur, metni okur ve metadata ile zenginleştirir."""
    if not os.path.exists(directory):
        logger.error(f"Directory not found: {directory}")
        return []

    pdf_files = [f for f in os.listdir(directory) if f.endswith(".pdf")]

    if not pdf_files:
        logger.warning("No PDF files found in the directory.")
        return []

    logger.info(f"Found {len(pdf_files)} PDF files. Starting processing...")

    processed_docs = []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""], 
        length_function=len,
    )

    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        file_path = os.path.join(directory, pdf_file)
        try:
            loader = PyMuPDFLoader(file_path)
            raw_docs = loader.load()

            for doc in raw_docs:
                doc.metadata["source"] = pdf_file
                doc.metadata["page"] = doc.metadata.get("page", 0) + 1
                doc.metadata["category"] = "clinical_guideline"

            chunks = text_splitter.split_documents(raw_docs)
            processed_docs.extend(chunks)

        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {e}")

    logger.info(f"Total chunks created: {len(processed_docs)}")
    return processed_docs


def main():
    try:
        client = get_chroma_client()
    except Exception:
        return

    setup_collection(client, reset=True)

    logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    embedding_function = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": DEVICE},
        encode_kwargs={"normalize_embeddings": True},  
    )

    docs = load_and_process_pdfs(PDF_SOURCE_DIR)

    if not docs:
        logger.warning("No documents to ingest. Exiting.")
        return

    logger.info("Uploading vectors to ChromaDB...")

    BATCH_SIZE = 100  
    total_batches = (len(docs) // BATCH_SIZE) + 1

    for i in tqdm(range(0, len(docs), BATCH_SIZE), desc="Uploading Batches"):
        batch = docs[i : i + BATCH_SIZE]
        if batch:
            Chroma.from_documents(
                client=client,
                documents=batch,
                embedding=embedding_function,
                collection_name=COLLECTION_NAME,
            )

    logger.info("Ingestion Complete! RAG Pipeline is ready.")


if __name__ == "__main__":
    main()
