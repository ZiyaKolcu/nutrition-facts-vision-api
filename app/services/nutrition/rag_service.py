import os
import logging
from typing import List, Optional

import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from app.services.nutrition.reference_service import reference_data_service

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service responsible for Retrieval-Augmented Generation (RAG).
    It connects to the ChromaDB vector store, performs semantic searches
    enriched with reference data, and returns clinical evidence for the LLM.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initializes the connection to ChromaDB and the Embedding Model."""
        logger.info("Initializing RAG Service...")

        self.chroma_host = os.getenv("CHROMA_HOST", "nutrition_facts_chroma")
        self.chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        self.collection_name = "nutrition_knowledge"
        self.model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.device = "cpu"

        try:
            logger.info(f"Loading embedding model: {self.model_name}...")
            self.embedding_function = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={"device": self.device},
                encode_kwargs={"normalize_embeddings": True},
            )

            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port,
                settings=Settings(allow_reset=False, anonymized_telemetry=False),
            )

            self.vector_store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,
            )
            logger.info("RAG Service initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize RAG Service: {e}")

            self.vector_store = None

    async def search_clinical_evidence(self, query_terms: List[str], k: int = 3) -> str:
        """
        Performs a semantic search in the vector database for the given ingredients.

        Args:
            query_terms: A list of ingredient names or E-codes (e.g. ["Sugar", "E102"]).
            k: Number of documents to retrieve.

        Returns:
            A formatted string containing the retrieved clinical evidence with citations.
        """
        if not self.vector_store:
            logger.warning("RAG Service is not initialized. Skipping search.")
            return "No clinical evidence available (Service Unavailable)."

        if not query_terms:
            return ""

        try:
            enriched_queries = []

            for term in query_terms:
                term_cleaned = term.strip()

                if term_cleaned.upper().startswith("E") and any(
                    char.isdigit() for char in term_cleaned
                ):
                    risk_info = reference_data_service.get_additive_risk_info(
                        term_cleaned
                    )
                    if risk_info:
                        enriched_queries.append(risk_info)
                    else:
                        enriched_queries.append(term_cleaned)
                else:
                    enriched_queries.append(term_cleaned)

            full_query_text = ". ".join(enriched_queries)

            results = self.vector_store.similarity_search(full_query_text, k=k)

            if not results:
                return "No specific clinical guidelines found for these ingredients."

            formatted_evidence = []
            for i, doc in enumerate(results):
                source = doc.metadata.get("source", "Unknown Source")
                page = doc.metadata.get("page", "?")

                content = doc.page_content.replace("\n", " ").strip()

                evidence_block = (
                    f"EVIDENCE #{i+1} (Source: {source}, Page: {page}):\n"
                    f'"{content}"'
                )
                formatted_evidence.append(evidence_block)

            return "\n\n".join(formatted_evidence)

        except Exception as e:
            logger.error(f"Error during RAG search: {e}")
            return "Error retrieving clinical evidence."


rag_service = RAGService()
