import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import MessagesPlaceholder

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI  # Import para ChatGPT
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

import torch

print("PyTorch version:", torch.__version__)
print("CUDA disponível:", torch.cuda.is_available())

from langchain_huggingface import ChatHuggingFace
from langchain_community.llms import HuggingFaceHub

# Configuração do Token diretamente
huggingface_api_token = "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"
openai_api_token = "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"

if not huggingface_api_token:
    raise ValueError("Token do Hugging Face não foi carregado!")
else:
    print("Token do Hugging Face carregado com sucesso!")

if not openai_api_token:
    raise ValueError("Token do OpenAI não foi carregado!")
else:
    print("Token do OpenAI carregado com sucesso!")

# Configurações do Streamlit
st.set_page_config(page_title="Seu assistente virtual 🤖", page_icon="🤖")
st.title("Seu assistente virtual 🤖")

model_class = "openai"  # Configurável: "hf_hub", "ollama", "openai"

def model_hf_hub(model="meta-llama/Meta-Llama-3-8B-Instruct", temperature=0.1):
    llm = HuggingFaceHub(
        repo_id=model,
        huggingfacehub_api_token=huggingface_api_token,
        model_kwargs={
            "temperature": temperature,
            "return_full_text": False,
            "max_new_tokens": 1024,
        }
    )
    return llm

def model_ollama(model="phi3", temperature=0.1):
    llm = ChatOllama(model=model, temperature=temperature)
    return llm

def model_openai(model="gpt-4", temperature=0.7):
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=openai_api_token  # Passando o token diretamente
    )
    return llm

def model_response(user_query, chat_history, model_class):
    if not isinstance(model_class, str):
        raise ValueError(f"model_class deve ser uma string. Valor recebido: {model_class}")

    print(f"Processando com model_class: {model_class}")

    if model_class == "hf_hub":
        llm = model_hf_hub()
    elif model_class == "ollama":
        llm = model_ollama()
    elif model_class == "openai":
        llm = model_openai()
    else:
        raise ValueError(f"model_class inválido: {model_class}")

    # Definição dos prompts
    system_prompt = """
        Você é um assistente prestativo e está respondendo perguntas gerais. Responda em {language}.
    """
    language = "português"

    user_prompt = "{input}"

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", user_prompt)
    ]) 

    # Criação da chain
    chain = prompt_template | llm | StrOutputParser()

    # Retorno da resposta
    return chain.stream({
        "chat_history": chat_history,
        "input": user_query,
        "language": language
    })

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [AIMessage(content="Olá, Leandro. Sou o seu Jarvis Pessoal! Como posso te ajudar hoje?")]

for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.write(message.content)

user_query = st.chat_input("Digite sua mensagem aqui...")

if user_query:
    # Processamento do input do usuário
    st.session_state.chat_history.append(HumanMessage(content=user_query))

    # Exibição da mensagem do usuário
    with st.chat_message("Human"):
        st.markdown(user_query)

    # Gerar resposta
    with st.chat_message("AI"):
        resp = model_response(user_query, st.session_state.chat_history, model_class)
        st.write(resp)
        st.session_state.chat_history.append(AIMessage(content=resp))
