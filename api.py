# api.py

import os
import tempfile
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import uvicorn

# We will reuse the functions from your existing files
from main import create_embeddings_from_pdf, build_qa_system

# Initialize the FastAPI app
app = FastAPI(
    title="Document Q&A API",
    description="An API for asking questions to a PDF document using a RAG model.",
)

# Define the response model for better API documentation
class QAResponse(BaseModel):
    answer: str
    source_documents: List[dict]

@app.post("/ask", response_model=QAResponse)
async def ask_question(
    question: str = Form(...), 
    file: UploadFile = File(...)
):
    """
    Accepts a PDF file and a question, returns an answer based on the document.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    try:
        # FastAPI's UploadFile is a "spooled" file. We need to save it to a
        # temporary file on disk so PyPDF2 can read its path.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        print(f"Processing PDF: {file.filename}")
        
        # 1. Create embeddings and retriever from the uploaded PDF
        retriever = create_embeddings_from_pdf(tmp_file_path)
        
        # 2. Build the Q&A chain
        qa_chain = build_qa_system(retriever)
        
        # 3. Get the result
        result = qa_chain.invoke({"query": question})

        # 4. Format the source documents for the response
        sources = [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in result["source_documents"]
        ]

        return {"answer": result["result"], "source_documents": sources}

    except Exception as e:
        # Handle potential errors during processing
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 5. Clean up the temporary file
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

if __name__ == "__main__":
    # This allows you to run the API directly for testing
    uvicorn.run(app, host="0.0.0.0", port=8000)