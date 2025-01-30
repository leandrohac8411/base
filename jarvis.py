import streamlit as st
import requests
import json
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import AIMessage, HumanMessage
import tempfile
import os

# Configurações da API OpenAI
API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = "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"
HEADERS = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
ID_MODELO = "gpt-4"

# Configurações do Streamlit
st.set_page_config(page_title="Seu Assistente Virtual 🤖", page_icon="🤖")
st.title("Seu Assistente Virtual 🤖")

# Função para enviar requisições ao GPT-4 Mini
def enviar_requisicao_openai(mensagem_usuario):
    body_mensagem = {
        "model": ID_MODELO,
        "messages": [{"role": "user", "content": mensagem_usuario}]
    }

    try:
        requisicao = requests.post(API_URL, headers=HEADERS, data=json.dumps(body_mensagem))

        if requisicao.status_code == 200:
            resposta = requisicao.json()
            conteudo_resposta = resposta["choices"][0]["message"]["content"]
            return conteudo_resposta
        elif requisicao.status_code == 401:
            return "Erro: Chave de API inválida ou sem permissão."
        else:
            return f"Erro na requisição: {requisicao.status_code}\nDetalhes: {requisicao.text}"
    except Exception as e:
        return f"Erro inesperado: {str(e)}"

# Configuração de base de conhecimento
def config_retriever(uploads):
    docs = []
    temp_dir = tempfile.TemporaryDirectory()
    for file in uploads:
        if not file.name.endswith(".pdf"):
            st.error(f"Erro: {file.name} não é um arquivo PDF válido.")
            continue
        temp_filepath = os.path.join(temp_dir.name, file.name)
        with open(temp_filepath, "wb") as f:
            f.write(file.getvalue())
        loader = PyPDFLoader(temp_filepath)
        docs.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    vectorstore = FAISS.from_documents(splits, embeddings)
    vectorstore.save_local('vectorstore/db_faiss')  # Persistente
    return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# Upload de arquivos para base de conhecimento
uploads = st.sidebar.file_uploader("Envie arquivos PDF para análise", type=["pdf"], accept_multiple_files=True)

if "retriever" not in st.session_state:
    st.session_state.retriever = config_retriever(uploads) if uploads else None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [AIMessage(content="Olá, Leandro. Sou o seu Jarvis Pessoal! Como posso te ajudar hoje?")]

# Exibir histórico de conversa
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.write(message.content)

# Entrada do usuário
user_query = st.chat_input("Digite sua mensagem aqui...")

if user_query:
    # Adicionar a mensagem do usuário ao histórico
    st.session_state.chat_history.append(HumanMessage(content=user_query))

    with st.chat_message("Human"):
        st.markdown(user_query)

    # Recuperar contexto, se houver base de conhecimento
    retriever = st.session_state.retriever
    if retriever:
        docs = retriever.get_relevant_documents(user_query)
        context = "\n".join([doc.page_content for doc in docs])
        mensagem_com_contexto = f"Contexto:\n{context}\n\nPergunta: {user_query}"
    else:
        mensagem_com_contexto = user_query

    # Enviar para o GPT-4 Mini
    resposta = enviar_requisicao_openai(mensagem_com_contexto)

    with st.chat_message("AI"):
        st.markdown(resposta)

    # Adicionar a resposta da IA ao histórico
    st.session_state.chat_history.append(AIMessage(content=resposta))

