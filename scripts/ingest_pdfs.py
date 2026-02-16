import os
import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "../raw_files")


def main():
    chroma_host = os.getenv("CHROMA_HOST", "nutrition_facts_chroma")
    chroma_port = int(os.getenv("CHROMA_PORT", "8000"))

    print(f"Connecting to ChromaDB at {chroma_host}:{chroma_port}...")

    http_client = chromadb.HttpClient(
        host=chroma_host,
        port=chroma_port,
        settings=Settings(allow_reset=True, anonymized_telemetry=False),
    )

    try:
        http_client.delete_collection("nutrition_knowledge")
        print("Existing collection deleted.")
    except Exception:
        pass

    collection = http_client.get_or_create_collection("nutrition_knowledge")

    pdf_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found.")
        return

    all_documents = []
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file}")
        try:
            loader = PyMuPDFLoader(os.path.join(RAW_DIR, pdf_file))
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = pdf_file
            all_documents.extend(docs)
        except Exception as e:
            print(f"Error reading {pdf_file}: {e}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", ". ", " ", ""]
    )
    splitted_docs = text_splitter.split_documents(all_documents)
    print(f"Total chunks created: {len(splitted_docs)}")

    print("Loading embedding model...")
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    print("Uploading to ChromaDB Server...")

    Chroma.from_documents(
        client=http_client,
        documents=splitted_docs,
        embedding=embedding_function,
        collection_name="nutrition_knowledge",
    )

    print("Ingestion Complete.")


if __name__ == "__main__":
    main()
