# Milestone 1: Project Setup + RAG Agent with LangGraph

## What You'll Build
A LangGraph-powered FAQ agent that answers clinic questions using RAG (Retrieval-Augmented Generation) with PDF documents stored in a Chroma vector database.

## Architecture
```
User Question
    |
    v
[LangGraph StateGraph]  (graph/faq_graph.py)
    |
    +--> faq_agent node  (agents/faq_agent.py)
    |        |
    |        +--> tools_condition (has tool calls?)
    |        |        |
    |        |     YES: invoke search_clinic_knowledge tool
    |        |        |
    |        |        +--> RAG Retriever (Chroma DB) --> return docs
    |        |        |
    |        |        +--> back to faq_agent with results
    |        |
    |        NO: return final answer --> END
```

## Project Structure
```
MAS/
├── cli.py                  # Interactive CLI to test the agent
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore
├── config/
│   ├── __init__.py
│   └── model.py            # Shared LLM + Embeddings (AWS Bedrock)
├── agents/
│   ├── __init__.py
│   └── faq_agent.py        # Node function + tools (agent logic)
├── graph/
│   ├── __init__.py
│   └── faq_graph.py        # StateGraph wiring (graph definition)
├── tools/
│   ├── __init__.py
│   └── rag_tools.py        # RAG search tool
├── rag/
│   ├── __init__.py
│   ├── ingest.py           # PDF loader + Chroma indexer
│   └── retriever.py        # Chroma retriever factory
└── data/
    ├── faq.pdf             # Clinic FAQ
    ├── policy.pdf          # Clinic policies
    └── CLINIC_Info.pdf     # Address, hours, doctors
```

## Step-by-Step Setup

### Step 1: Create the project and install dependencies

```bash
mkdir MAS && cd MAS
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure environment variables

Copy `.env.example` to `.env` and fill in your AWS credentials:
```bash
cp .env.example .env
```

You need:
- AWS credentials with Bedrock access
- Region where Bedrock models are enabled

### Step 3: Create the shared config (`config/model.py`)

This centralizes the LLM and embeddings so all agents use the same models:

```python
from langchain_aws import ChatBedrockConverse, BedrockEmbeddings

embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0")
llm = ChatBedrockConverse(model="global.anthropic.claude-haiku-4-5-20251001-v1:0")
```

**Key concepts:**
- `ChatBedrockConverse` - LangChain wrapper for AWS Bedrock's Converse API
- `BedrockEmbeddings` - Converts text to vectors using Amazon Titan

### Step 4: Create the RAG pipeline

#### 4a. Ingest PDFs (`rag/ingest.py`)

Loads PDF files, splits them into chunks, and stores in Chroma:

```python
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from config.model import embeddings

# Load PDF -> Split into 500-char chunks -> Store in Chroma
```

**Key concepts:**
- `PyPDFLoader` - Extracts text from PDFs
- `RecursiveCharacterTextSplitter` - Splits text into overlapping chunks for better retrieval
- `Chroma` - Vector database that stores embeddings locally

#### 4b. Retriever (`rag/retriever.py`)

Connects to the existing Chroma store and returns a retriever:

```python
from langchain_chroma import Chroma
from config.model import embeddings

vector_store = Chroma(
    collection_name="pdf_chunks",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db"
)

def get_retriever(top_k=5):
    return vector_store.as_retriever(search_kwargs={"k": top_k})
```

### Step 5: Create the RAG tool (`tools/rag_tools.py`)

Wraps the retriever as a LangChain tool that the agent can call:

```python
from langchain.tools import tool
from rag.retriever import get_retriever

retriever = get_retriever()

@tool
def search_clinic_knowledge(query: str) -> str:
    """Search the clinic knowledge base for information about
    policies, FAQ, hours, location, insurance, and services."""
    docs = retriever.invoke(query)
    return "\n\n".join([doc.page_content for doc in docs])
```

**Key concepts:**
- `@tool` decorator - Makes a Python function callable by LangGraph agents
- The docstring becomes the tool description the LLM reads to decide when to use it

### Step 6: Create the agent node (`agents/faq_agent.py`)

The agent node defines the LLM call logic with tools bound:

```python
from langgraph.graph import MessagesState
from config.model import llm
from tools.rag_tools import search_clinic_knowledge

tools = [search_clinic_knowledge]
llm_with_tools = llm.bind_tools(tools)

def faq_node(state: MessagesState):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}
```

**Key concepts:**
- `bind_tools()` - Tells the LLM what tools are available
- The node function takes state, calls LLM, returns updated state
- Agent logic is separated from graph wiring

### Step 7: Wire the graph (`graph/faq_graph.py`)

The graph connects the agent node, tool node, and routing logic:

```python
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from agents.faq_agent import faq_node, tools

builder = StateGraph(MessagesState)
builder.add_node("faq_agent", faq_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "faq_agent")
builder.add_conditional_edges("faq_agent", tools_condition)
builder.add_edge("tools", "faq_agent")

faq_graph = builder.compile()
```

**Key LangGraph concepts:**
- `StateGraph` - Defines a graph where each node transforms shared state
- `MessagesState` - Built-in state schema with a `messages` list
- `ToolNode` - Prebuilt node that executes tool calls from the LLM response
- `tools_condition` - Routes to "tools" node if LLM made tool calls, otherwise to END
- `compile()` - Finalizes the graph into a runnable agent
- **Separation**: Agent logic in `agents/`, graph wiring in `graph/`

### Step 8: Run it

First, ingest the PDFs into Chroma:
```bash
python -m rag.ingest
```

Then start the CLI:
```bash
python cli.py
```

Try asking:
- "What are the clinic hours?"
- "Which doctors work here?"
- "What's the cancellation policy?"
- "Do you accept insurance?"

## What's Next (Milestone 2)
Add Google Calendar integration via Composio MCP Server for appointment booking.
