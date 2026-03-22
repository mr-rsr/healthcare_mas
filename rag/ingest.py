#  Load the pdf file and split it into chunks
#  Create a vector store and add the chunks to it

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.model import embeddings
from langchain_chroma import Chroma
import glob

def load_pdf(file_path):
    """Load a PDF file and return the documents."""
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    return documents

def split_text(documents):
    """ Split the documents into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=20,
        length_function=len
    )
    docs = text_splitter.split_documents(documents)
    return docs

def create_vector_store(docs):
    """ Create a vector store and add the chunks to it."""
    vector_store = Chroma(
        collection_name="pdf_chunks",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
    )
    vector_store.add_documents(docs)
    return vector_store

# runs this block only when script executed directly (not when imported)
if __name__ == "__main__":
    # Get all PDF files from the data folder
    file_paths = glob.glob("data/*.pdf") 
    all_docs = []
    for file_path in file_paths:
        documents = load_pdf(file_path)
        docs = split_text(documents)
        all_docs.extend(docs)
    print(f"Total chunks created: {len(all_docs)}")
    vector_store = create_vector_store(all_docs)
    print("Vector store created and documents added.")