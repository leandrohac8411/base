import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint
from langchain_community.llms import HuggingFaceHub
import tempfile
import os
import time
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.qa_with_retrieval import RetrievalQA
from langchain.chains import StuffDocumentsChain
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Streamlit
st.set_page_config(page_title="Converse com documentos 📚", page_icon="📚")
st.title("Converse com documentos 📚")

# Configurar tokens
def get_huggingface_token():
    return os.getenv("HUGGINGFACEHUB_API_TOKEN", "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")

HUGGINGFACE_API_TOKEN = get_huggingface_token()
if not HUGGINGFACE_API_TOKEN:
    st.error("Token do Hugging Face não configurado! Configure no arquivo .env ou diretamente no código.")
    st.stop()

model_class = "hf_hub"  # Configurável: "hf_hub", "openai"

# Provedores de modelos
def model_hf_hub(model="meta-llama/Meta-Llama-3-8B-Instruct", temperature=0.1):
    return HuggingFaceHub(
        repo_id=model,
        huggingfacehub_api_token=HUGGINGFACE_API_TOKEN,  # Token configurado aqui
        model_kwargs={
            "temperature": temperature,
            "return_full_text": False,
            "max_new_tokens": 512,
        },
    )

def model_openai(model="gpt-4o-mini", temperature=0.1):
    return ChatOpenAI(
        model=model,
        temperature=temperature
    )

# Indexação e recuperação
def config_retriever(uploads):
    docs = []
    temp_dir = tempfile.TemporaryDirectory()
    for file in uploads:
        temp_filepath = os.path.join(temp_dir.name, file.name)
        with open(temp_filepath, "wb") as f:
            f.write(file.getvalue())
        loader = PyPDFLoader(temp_filepath)
        try:
            docs.extend(loader.load())
        except Exception as e:
            st.error(f"Erro ao processar {file.name}: {str(e)}")

    if not docs:
        st.warning("Nenhum documento válido foi processado.")
        return None

    # Divisão em pedaços de texto
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    # Embedding
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    vectorstore = FAISS.from_documents(splits, embeddings)
    vectorstore.save_local('vectorstore/db_faiss')

    return vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 3, "fetch_k": 4})

# Configuração da chain
def config_rag_chain(model_class, retriever):
    if model_class == "hf_hub":
        llm = model_hf_hub()
    elif model_class == "openai":
        llm = model_openai()
    else:
        raise ValueError(f"model_class inválido: {model_class}")

    qa_prompt_template = """Você é um assistente virtual prestativo e está respondendo perguntas gerais. 
    Use os seguintes pedaços de contexto recuperado para responder à pergunta. 
    Se você não sabe a resposta, apenas diga que não sabe. Mantenha a resposta concisa. 
    Responda em português. 

    Pergunta: {input} 
    Contexto: {context}"""

    qa_prompt = PromptTemplate.from_template(qa_prompt_template)
    qa_chain = StuffDocumentsChain(llm=llm, prompt=qa_prompt)
    return RetrievalQA(retriever=retriever, combine_documents_chain=qa_chain)

# Interface do Streamlit
uploads = st.sidebar.file_uploader("Envie arquivos PDF", type=["pdf"], accept_multiple_files=True)

if not uploads:
    st.info("Por favor, envie algum arquivo para continuar")
    st.stop()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [AIMessage(content="Olá, sou o seu assistente virtual! Como posso ajudar você?")]

if "retriever" not in st.session_state:
    st.session_state.retriever = config_retriever(uploads)

# Validar retriever
retriever = st.session_state.retriever
if not retriever:
    st.error("Nenhum retriever configurado. Carregue documentos para criar a base de conhecimento.")
    st.stop()

for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.write(message.content)

user_query = st.chat_input("Digite sua mensagem aqui...")

if user_query:
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    with st.chat_message("Human"):
        st.markdown(user_query)

    rag_chain = config_rag_chain(model_class, retriever)

    start = time.time()
    result = rag_chain.run(user_query)
    end = time.time()

    resp = result or "Desculpe, não consegui encontrar uma resposta."
    st.write(resp)

    st.session_state.chat_history.append(AIMessage(content=resp))
    with st.chat_message("AI"):
        st.write(f"Resposta gerada em {end - start:.2f} segundos.")
