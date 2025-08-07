import os
import faiss
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings  # Updated import
from openai import OpenAI
from dotenv import load_dotenv
import logging

load_dotenv()

# Configuration - UPDATED MODEL NAMES
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"  # Better alternative
LLM_MODEL = "anthropic/claude-3-haiku"  # Verified working model on OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize clients
embedding_model = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    encode_kwargs={"normalize_embeddings": True}
)

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Document storage
doc_store = {}
index = None


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Save temporary file
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext != "pdf":
            raise HTTPException(400, "Only PDF files are currently supported")

        temp_path = "temp.pdf"
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Load and chunk document
        loader = PyPDFLoader(temp_path)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)

        # Generate embeddings
        texts = [chunk.page_content for chunk in chunks]
        embeddings = embedding_model.embed_documents(texts)

        # Create FAISS index
        dimension = len(embeddings[0])
        global index
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings).astype("float32"))

        # Store document
        doc_id = len(doc_store)
        doc_store[doc_id] = {
            "chunks": chunks,
            "embeddings": embeddings
        }

        return {
            "doc_id": doc_id,
            "chunk_count": len(chunks),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(500, f"Document processing error: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/query")
async def query_document(doc_id: int, query: str):
    if doc_id not in doc_store or index is None:
        raise HTTPException(404, "Document not found or not indexed")

    try:
        # Semantic search
        query_embedding = embedding_model.embed_query(query)
        D, I = index.search(np.array([query_embedding]).astype("float32"), 3)

        # Build context
        context = "\n\n".join(
            doc_store[doc_id]["chunks"][idx].page_content
            for idx in I[0]
        )

        # Generate response - UPDATED PROMPT ENGINEERING
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert document analyst. Answer questions based strictly on the provided context.

                    Rules:
                    1. Be concise (1-2 sentences max)
                    2. If the answer isn't in the context, say "I couldn't find this information in the document"
                    3. Never hallucinate details"""
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}"
                }
            ],
            temperature=0.1,  # Keep responses factual
            max_tokens=500
        )

        return {
            "answer": response.choices[0].message.content,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(500, f"Query processing error: {str(e)}")