import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import tempfile
import os
import sqlite3
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tokens de API
HUGGINGFACE_API_TOKEN = "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"
OPENAI_API_TOKEN = "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"

if not HUGGINGFACE_API_TOKEN or not OPENAI_API_TOKEN:
    raise ValueError("Configure os tokens de API para Hugging Face e OpenAI.")

# Configuração do Streamlit
st.set_page_config(page_title="Converse com documentos 📚", page_icon="📚")
st.title("Sou seu assistente virtual 📚")

# Configurar banco de dados SQLite
def setup_database():
    conn = sqlite3.connect("pdf_knowledge_base.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            file_name TEXT,
            page_number INTEGER,
            content TEXT
        )
    ''')
    conn.commit()
    return conn

# Salvar documentos no banco de dados
def save_to_database(docs, file_name, conn):
    cursor = conn.cursor()
    for doc in docs:
        content = doc.page_content
        page_number = doc.metadata.get("page", -1)
        cursor.execute('''
            INSERT INTO documents (file_name, page_number, content)
            VALUES (?, ?, ?)
        ''', (file_name, page_number, content))
    conn.commit()
    logger.info(f"{len(docs)} documentos salvos no banco de dados.")

# Carregar ou criar retriever FAISS
def load_or_create_retriever(uploads, conn):
    if os.path.exists("vectorstore/db_faiss"):
        logger.info("Carregando índice FAISS existente...")
        vectorstore = FAISS.load_local(
            "vectorstore/db_faiss", 
            embeddings=HuggingFaceEmbeddings(model_name="BAAI/bge-m3"),
            allow_dangerous_deserialization=True  # Habilitar desserialização
        )
        return vectorstore.as_retriever(search_type="mmr", search_kwargs={'k': 3, 'fetch_k': 4})
    else:
        return config_retriever(uploads, conn)

# Configurar retriever para novos uploads
def config_retriever(uploads, conn):
    docs = []
    temp_dir = tempfile.TemporaryDirectory()
    for file in uploads:
        temp_filepath = os.path.join(temp_dir.name, file.name)
        with open(temp_filepath, "wb") as f:
            f.write(file.getvalue())
        loader = PyPDFLoader(temp_filepath)
        loaded_docs = loader.load()
        docs.extend(loaded_docs)

        # Salvar no banco de dados SQLite
        save_to_database(loaded_docs, file.name, conn)
    
    if docs:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
        vectorstore = FAISS.from_documents(splits, embeddings)
        vectorstore.save_local('vectorstore/db_faiss')

        logger.info("Índice FAISS criado com sucesso.")
        return vectorstore.as_retriever(search_type="mmr", search_kwargs={'k': 3, 'fetch_k': 4})
    else:
        st.warning("Nenhum documento válido foi processado.")
        return None

# Modelo GPT-4
def model_openai():
    return ChatOpenAI(model="gpt-4", temperature=0.9, openai_api_key=OPENAI_API_TOKEN)

# Gerar resposta usando os documentos e GPT-4
def generate_response(query, retriever, conn):
    if retriever:
        docs = retriever.get_relevant_documents(query)
        if docs:
            context = "\n".join([doc.page_content for doc in docs])
            prompt = f"Contexto:\n{context}\n\nPergunta:\n{query}\n\nResponda de forma clara e objetiva em português."
            model = model_openai()
            return model.predict(prompt)
    
    logger.info("Nenhum contexto encontrado nos documentos. Usando GPT-4 sem contexto.")
    model = model_openai()
    return model.predict(f"Pergunta:\n{query}\n\nResponda de forma clara e objetiva em português.")

# Configurar banco de dados
conn = setup_database()

# Interface do Streamlit
uploads = st.sidebar.file_uploader("Envie arquivos PDF", type=["pdf"], accept_multiple_files=True)

if uploads:
    st.session_state.retriever = load_or_create_retriever(uploads, conn)

# Verificar conteúdo do banco de dados SQLite
if st.sidebar.button("Ver dados do banco"):
    with st.expander("Conteúdo do Banco de Dados"):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                st.write(f"ID: {row[0]}, Arquivo: {row[1]}, Página: {row[2]}, Conteúdo: {row[3][:200]}...")
        else:
            st.write("O banco de dados está vazio.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [AIMessage(content="Olá! Como posso ajudar você hoje?")]

for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.write(message.content)

user_query = st.chat_input("Digite sua pergunta aqui...")

if user_query:
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    with st.chat_message("Human"):
        st.write(user_query)

    retriever = st.session_state.get("retriever", None)
    if retriever is None:
        response = "Nenhum retriever configurado. Carregue documentos para criar a base de conhecimento."
    else:
        response = generate_response(user_query, retriever, conn)

    st.session_state.chat_history.append(AIMessage(content=response))
    with st.chat_message("AI"):
        st.write(response)
