from langchain.tools import tool
from rag.retriever import get_retriever

retriever = get_retriever()

@tool
def search_clinic_knowledge(query: str) -> str:
    """Search the clinic knowledge base for information about
    policies, FAQ, hours, location, insurance, and services."""
    docs = retriever.invoke(query)
    return "\n\n".join([doc.page_content for doc in docs])