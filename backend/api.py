import os
import tempfile
from typing import List, Dict
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import uvicorn

# Import the functions from your existing files
from main import create_embeddings_from_pdf, build_qa_system
from langchain.schema.retriever import BaseRetriever

# --- In-Memory Cache ---
# This dictionary will store the created retrievers.
# In a production environment, you'd replace this with a more robust
# solution like Redis or another database.
vector_store_cache: Dict[str, BaseRetriever] = {}

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Document Q&A API",
    description="An API to upload a PDF and ask multiple questions about it.",
)

# --- Pydantic Models for Request and Response ---
class UploadResponse(BaseModel):
    message: str
    document_id: str

class AskRequest(BaseModel):
    document_id: str
    question: str

class QAResponse(BaseModel):
    answer: str
    source_documents: List[dict]


# --- API Endpoints ---

@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    1. Upload a PDF.
    2. Process it and create a vector store retriever.
    3. Store the retriever in the cache with the filename as its ID.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")
    
    # Use the filename as the document_id.
    # Note: In a real app, you might want a more robust ID like a UUID.
    document_id = file.filename
    if document_id in vector_store_cache:
        return {"message": "Document already uploaded.", "document_id": document_id}

    try:
        # Save uploaded file to a temporary location to be read
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        print(f"Processing and caching document: {document_id}")
        
        # Create and cache the retriever
        retriever = create_embeddings_from_pdf(tmp_file_path)
        vector_store_cache[document_id] = retriever

        return {"message": "Document processed and ready for questions.", "document_id": document_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")
    finally:
        # Clean up the temporary file
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)


@app.post("/ask", response_model=QAResponse)
async def ask_question(request: AskRequest):
    """
    1. Retrieve a processed document from the cache using its ID.
    2. Ask a question against it.
    """
    document_id = request.document_id
    question = request.question

    if document_id not in vector_store_cache:
        raise HTTPException(status_code=404, detail="Document not found. Please upload it first via the /upload endpoint.")

    try:
        # Get the retriever from the cache
        retriever = vector_store_cache[document_id]
        
        # Build the Q&A chain (this is a lightweight operation)
        qa_chain = build_qa_system(retriever)
        
        # Get the result
        result = qa_chain.invoke({"query": question})

        # Format the source documents for the response
        sources = [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in result["source_documents"]
        ]

        return {"answer": result["result"], "source_documents": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during Q&A: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)