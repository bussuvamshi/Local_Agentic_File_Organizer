"""
Vector Store Management for LAFO
Manages the local vector database for semantic document routing.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

import faiss
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from config import (
    VECTORSTORE_DIR, 
    VECTORSTORE_METADATA, 
    TARGET_ROOT,
    EMBEDDING_MODEL,
    VECTOR_SEARCH_K
)

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages the vector database for directory taxonomy and semantic search."""
    
    def __init__(self):
        """Initialize the vector store manager."""
        self.vectorstore = None
        self.embeddings = None
        self.metadata = {}
        self.ensure_directories()
        self.load_embeddings()
        
    def ensure_directories(self):
        """Ensure vector store directory exists."""
        Path(VECTORSTORE_DIR).mkdir(parents=True, exist_ok=True)
        
    def load_embeddings(self):
        """Load the embedding model (downloads if necessary)."""
        try:
            logger.info(f"Loading embeddings model: {EMBEDDING_MODEL}")
            self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
            logger.info("✅ Embeddings model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load embeddings: {str(e)}")
            raise
    
    def build_directory_taxonomy(self) -> List[Document]:
        """
        Scan the target root directory and build semantic documents for each folder.
        
        Returns:
            List of Document objects representing the directory structure
        """
        documents = []
        
        if not TARGET_ROOT.exists():
            logger.warning(f"Target root directory does not exist: {TARGET_ROOT}")
            return documents
        
        logger.info(f"Building directory taxonomy from: {TARGET_ROOT}")
        
        # Get all subdirectories
        for folder_path in TARGET_ROOT.rglob("*"):
            if folder_path.is_dir() and folder_path != TARGET_ROOT:
                folder_name = folder_path.name
                relative_path = folder_path.relative_to(TARGET_ROOT)
                relative_path_posix = relative_path.as_posix()
                
                # Create a semantic document for each folder
                doc_content = f"""
Folder Category: {folder_name}
Path: {relative_path_posix}
Description: This is a file category folder in the document organization system.
Category Name: {folder_name}
"""
                
                doc = Document(
                    page_content=doc_content.strip(),
                    metadata={
                        "folder_name": folder_name,
                        "folder_path": relative_path_posix,
                        "absolute_path": str(folder_path),
                        "type": "directory_taxonomy"
                    }
                )
                documents.append(doc)
                logger.info(f"  📁 Added: {folder_name} ({relative_path_posix})")
        
        if not documents:
            logger.warning("No subdirectories found in target root")
        else:
            logger.info(f"✅ Built taxonomy with {len(documents)} categories")
        
        return documents
    
    def initialize_vectorstore(self, force_rebuild: bool = False) -> FAISS:
        """
        Initialize or load the vector store.
        
        Args:
            force_rebuild: If True, rebuild the vectorstore from scratch
            
        Returns:
            FAISS vectorstore instance
        """
        vectorstore_path = Path(VECTORSTORE_DIR) / "index"
        
        # Check if vectorstore exists and should be loaded
        if vectorstore_path.exists() and not force_rebuild:
            try:
                logger.info("Loading existing vector store...")
                self.vectorstore = FAISS.load_local(
                    VECTORSTORE_DIR,
                    self.embeddings,
                    index_name="index",
                    allow_dangerous_deserialization=True
                )
                logger.info("✅ Vector store loaded successfully")
                self.load_metadata()
                return self.vectorstore
            except Exception as e:
                logger.warning(f"Failed to load existing vectorstore: {str(e)}. Rebuilding...")
                force_rebuild = True
        
        # Build vectorstore from directory taxonomy
        if force_rebuild or not vectorstore_path.exists():
            logger.info("Building new vector store...")
            documents = self.build_directory_taxonomy()
            
            if not documents:
                logger.error("Cannot create vectorstore without documents")
                return None
            
            try:
                self.vectorstore = FAISS.from_documents(documents, self.embeddings)
                self.vectorstore.save_local(VECTORSTORE_DIR, index_name="index")
                logger.info("✅ Vector store created and saved")
                
                # Save metadata
                self.save_metadata(documents)
                
                return self.vectorstore
            except Exception as e:
                logger.error(f"❌ Failed to create vectorstore: {str(e)}")
                raise
    
    def save_metadata(self, documents: List[Document]):
        """
        Save directory metadata to JSON file.
        
        Args:
            documents: List of Document objects with directory information
        """
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "total_categories": len(documents),
            "categories": [
                {
                    "folder_name": doc.metadata.get("folder_name"),
                    "folder_path": doc.metadata.get("folder_path"),
                    "absolute_path": doc.metadata.get("absolute_path")
                }
                for doc in documents
            ]
        }
        
        metadata_path = Path(VECTORSTORE_DIR) / VECTORSTORE_METADATA
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✅ Metadata saved to {metadata_path}")
    
    def load_metadata(self):
        """Load directory metadata from JSON file."""
        metadata_path = Path(VECTORSTORE_DIR) / VECTORSTORE_METADATA
        if metadata_path.exists():
            try:
                with open(metadata_path, "r") as f:
                    self.metadata = json.load(f)
                logger.info(f"✅ Metadata loaded: {self.metadata['total_categories']} categories")
            except Exception as e:
                logger.warning(f"Failed to load metadata: {str(e)}")
    
    def search_similar_folders(self, query: str, k: int = VECTOR_SEARCH_K) -> List[Tuple[str, float]]:
        """
        Search for similar folder categories based on query text.
        
        Args:
            query: Document content/text to match against categories
            k: Number of results to return
            
        Returns:
            List of tuples (folder_path, similarity_score)
        """
        if not self.vectorstore:
            logger.error("Vector store not initialized")
            return []
        
        try:
            # Perform similarity search
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            folder_matches = []
            for doc, score in results:
                folder_path = doc.metadata.get("folder_path", "Unknown")
                folder_name = doc.metadata.get("folder_name", "Unknown")
                
                # Convert score to similarity (0-1 range, where 1 is most similar)
                # FAISS returns distance, so we convert: similarity = 1 / (1 + distance)
                similarity = 1 / (1 + score)
                
                folder_matches.append((folder_path, similarity, folder_name))
            
            logger.debug(f"Found {len(folder_matches)} similar folders for query")
            return folder_matches
        
        except Exception as e:
            logger.error(f"Error during similarity search: {str(e)}")
            return []
    
    def get_all_categories(self) -> Dict[str, str]:
        """
        Get all available folder categories.
        
        Returns:
            Dictionary mapping folder_path to folder_name
        """
        if not self.metadata:
            self.load_metadata()
        
        categories = {}
        for cat in self.metadata.get("categories", []):
            categories[cat["folder_path"]] = cat["folder_name"]
        
        return categories
    
    def refresh_from_filesystem(self):
        """Refresh the vector store by rescanning the filesystem."""
        logger.info("Refreshing vector store from filesystem...")
        self.initialize_vectorstore(force_rebuild=True)
        logger.info("✅ Vector store refreshed")
