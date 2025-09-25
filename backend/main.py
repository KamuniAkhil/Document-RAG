import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA

# Import your custom util functions
from models import get_llm, get_embedding_model

def extract_pdf_text(pdf_path: str) -> str:
    """Extracts all text from a PDF file."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def create_embeddings_from_pdf(pdf_path: str):
    """Reads PDF, creates embeddings dynamically, and returns a retriever."""
    text = extract_pdf_text(pdf_path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)

    embeddings_model = get_embedding_model()
    batch_size = 200

    docs = []
    vectors = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        print(f"Embedding batch {i // batch_size + 1} of size {len(batch)}")
        batch_vectors = embeddings_model.embed_documents(batch)
        docs.extend(batch)
        vectors.extend(batch_vectors)

    faiss_store = FAISS.from_embeddings(
        text_embeddings=list(zip(docs, batch_vectors)), # Corrected argument
        embedding=embeddings_model
    )

    return faiss_store.as_retriever(search_kwargs={"k": 4})

def build_qa_system(retriever):
    """Builds a RetrievalQA chain using your Azure LLM."""
    # Updated to use the correct model deployment name from your snippet
    llm = get_llm(model_name="anthropic.claude-sonnet-4-20250514-v1:0")

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff", # Changed for simplicity and efficiency
        return_source_documents=True
    )
    return qa_chain

if __name__ == "__main__":
    # Ensure you have a PDF file for testing
    pdf_path = r"C:\Users\KamuniAkhil\Downloads\dspy.pdf" 

    if not os.path.exists(pdf_path):
        print(f"Error: The file was not found at {pdf_path}")
    else:
        print(">>> Creating embeddings from PDF...")
        retriever = create_embeddings_from_pdf(pdf_path)

        print(">>> Building Q&A system...")
        qa = build_qa_system(retriever)

        print("\n✅ PDF loaded. You can now ask questions!")

        while True:
            query = input("\nYour Question (or 'exit'): ")
            if query.lower() in ["exit", "quit"]:
                break

            result = qa.invoke({"query": query}) # Use invoke for newer LangChain versions
            print("\nAnswer:", result["result"])
            print("\nSource Documents:")
            for doc in result["source_documents"]:
                print("-", doc.page_content[:100] + "...") # Print snippet of source