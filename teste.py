from langchain_huggingface import HuggingFaceEndpoint
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do .env
load_dotenv(dotenv_path="C:/temp/Projeto/.env")

# Token do Hugging Face
api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
if not api_token:
    raise ValueError("Token do Hugging Face não foi carregado!")

# Configuração do modelo Hugging Face
llm_hf = HuggingFaceEndpoint(
    endpoint_url="https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct",
    huggingfacehub_api_token=api_token,
    temperature=0.1,
    max_new_tokens=512,
    return_full_text=False
)

# Configuração do modelo Ollama
llm_ollama = ChatOllama(
    model="phi3",
    temperature=0.1
)

# Definir prompts
system_prompt = "Você é um assistente prestativo e está respondendo perguntas gerais."
user_prompt = "{input}"

# Construir o ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", user_prompt)
])

# Input de exemplo
input_text = "Explique para mim em até 1 parágrafo o conceito de redes neurais, de forma clara e objetiva"

# Teste com Hugging Face
print("== Resposta do Hugging Face ==")
chain_hf = prompt | llm_hf
res_hf = chain_hf.invoke({"input": input_text})
print(res_hf)

print("\n-----\n")

# Teste com Ollama
print("== Resposta do Ollama ==")
chain_ollama = prompt | llm_ollama
res_ollama = chain_ollama.invoke({"input": input_text})
print(res_ollama.content)
