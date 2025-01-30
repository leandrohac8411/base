import streamlit as st
from huggingface_hub import InferenceApi
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
MODEL_REPO_ID = "tiiuae/falcon-7b-instruct"  # Modelo atualizado

if not HUGGINGFACE_API_TOKEN:
    raise ValueError("Configure o token de API do Hugging Face.")

# Configuração do cliente Hugging Face
hf_client = InferenceApi(repo_id=MODEL_REPO_ID, token=HUGGINGFACE_API_TOKEN)

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
            allow_dangerous_deserialization=True
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

# Gerar resposta usando os documentos e o modelo gpt-4o-mini-realtime
def generate_response(query, retriever, conn):
    if retriever:
        docs = retriever.get_relevant_documents(query)
        if docs:
            context = "\n".join([doc.page_content for doc in docs])
            prompt = f"Contexto:\n{context}\n\nPergunta:\n{query}\n\nResponda de forma clara e objetiva em português."
            try:
                response = hf_client(prompt)
                logger.info("Resposta gerada com sucesso pelo modelo.")
                return response.get("generated_text", "Sem resposta gerada pelo modelo.")
            except Exception as e:
                logger.error(f"Erro ao gerar resposta com contexto: {e}")
                return "Ocorreu um erro ao processar sua solicitação. Verifique os logs para mais detalhes."
    
    logger.info("Nenhum contexto encontrado nos documentos. Usando GPT-4o-mini-realtime sem contexto.")
    prompt = f"Pergunta:\n{query}\n\nResponda de forma clara e objetiva em português."
    try:
        response = hf_client(prompt)
        logger.info("Resposta gerada com sucesso pelo modelo sem contexto.")
        return response.get("generated_text", "Sem resposta gerada pelo modelo.")
    except Exception as e:
        logger.error(f"Erro ao gerar resposta sem contexto: {e}")
        return "Ocorreu um erro ao processar sua solicitação. Verifique os logs para mais detalhes."

# Configurar banco de dados
conn = setup_database()

# Interface do Streamlit
uploads = st.sidebar.file_uploader("Envie arquivos PDF", type=["pdf"], accept_multiple_files=True)

if uploads:
    st.info("Processando os documentos enviados...")
    retriever = load_or_create_retriever(uploads, conn)
    if retriever:
        st.session_state.retriever = retriever
        st.success("Base de conhecimento criada com sucesso!")
    else:
        st.error("Não foi possível criar a base de conhecimento. Verifique os documentos enviados.")

# Garantir que o retriever está configurado antes de processar perguntas
retriever = st.session_state.get("retriever", None)
if retriever is None:
    st.warning("Nenhum retriever configurado. Carregue documentos para criar a base de conhecimento.")

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
    st.session_state.chat_history = []

for message in st.session_state.chat_history:
    if "AI" in message:
        with st.chat_message("AI"):
            st.write(message["AI"])
    elif "Human" in message:
        with st.chat_message("Human"):
            st.write(message["Human"])

user_query = st.chat_input("Digite sua pergunta aqui...")

if user_query:
    st.session_state.chat_history.append({"Human": user_query})
    with st.chat_message("Human"):
        st.write(user_query)

    if retriever is None:
        response = "Nenhum retriever configurado. Carregue documentos para criar a base de conhecimento."
    else:
        response = generate_response(user_query, retriever, conn)

    st.session_state.chat_history.append({"AI": response})
    with st.chat_message("AI"):
        st.write(response)
