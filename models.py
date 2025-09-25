from langchain.embeddings.base import Embeddings
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
import os
import dotenv

# Load environment variables from a .env file
dotenv.load_dotenv()

def get_llm(model_name: str, temperature: float = 0) -> AzureChatOpenAI:
    """Get Azure OpenAI Chat LLM configured for the new endpoint."""
    return AzureChatOpenAI(
        # Updated to use the specific endpoint from your snippet
        azure_endpoint="https://ai-proxy.lab.epam.com",
        
        # This is the model deployment name
        azure_deployment=model_name,
        
        # Updated to the required API version
        api_version="2024-02-01",
        
        # API Key is loaded from the .env file
        api_key=os.getenv("DIAL_API_KEY"),
        
        temperature=temperature,
        streaming=True
    )

def get_embedding_model() -> Embeddings:
    """Get Azure OpenAI Embedding Model configured for the new endpoint."""
    return AzureOpenAIEmbeddings(
        # Updated to use the specific endpoint from your snippet
        azure_endpoint="https://ai-proxy.lab.epam.com",

        # As suggested in your snippet for embeddings
        model="text-embedding-ada-002",
        azure_deployment="text-embedding-ada-002",
        
        # Updated to the required API version
        api_version="2024-02-01",
        
        # API Key is loaded from the .env file
        api_key=os.getenv("DIAL_API_KEY"),
        
        check_embedding_ctx_length=False
    )