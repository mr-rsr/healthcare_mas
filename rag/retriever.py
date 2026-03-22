from langchain_chroma import Chroma
from config.model import embeddings

vector_store = Chroma(
    collection_name="pdf_chunks",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db"
)

def get_retriever(top_k=5):
  return vector_store.as_retriever(search_kwargs={"k": top_k})