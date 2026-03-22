"""
Streamlit UI for HealthFirst Medical Clinic
Imports the LangGraph graph directly (no API calls).
Run: streamlit run app.py
"""
import uuid
import streamlit as st
from graph.workflow import build_faq_only_workflow

# --- Page Config ---
st.set_page_config(
    page_title="HealthFirst Medical Clinic",
    page_icon="🏥",
    layout="centered",
)

# --- Session State Init ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state.messages = []
if "graph" not in st.session_state:
    st.session_state.graph = build_faq_only_workflow()

graph = st.session_state.graph

# --- Sidebar ---
with st.sidebar:
    st.title("HealthFirst Clinic")
    st.caption("Multi-Agent Appointment System")

    st.divider()

    st.subheader("Session Info")
    st.text(f"Thread: {st.session_state.thread_id}")

    if st.button("New Conversation"):
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.subheader("Try asking:")
    st.markdown("""
    - What are your clinic hours?
    - Which doctors work here?
    - What's the cancellation policy?
    - Do you accept insurance?
    - How do I book an appointment?
    - Where is the clinic located?
    """)

    st.divider()
    st.caption("Powered by LangGraph + AWS Bedrock")

# --- Main Chat Area ---
st.title("HealthFirst Medical Clinic")
st.caption("Ask me anything about our clinic, doctors, policies, and services.")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Type your question..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent response
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = graph.invoke(
                {"messages": [("user", prompt)]},
                config,
            )
            response = result["messages"][-1].content
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
