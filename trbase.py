import streamlit as st
import PyPDF2
import re
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from langchain_community.llms import HuggingFaceHub  
from langchain_core.prompts import ChatPromptTemplate


# 🔹 CONFIGURAÇÃO DO FIREBASE
if not firebase_admin._apps:
    if os.getenv("STREAMLIT_CLOUD"):
        firebase_credentials = json.loads(st.secrets["FIREBASE"])
        cred = credentials.Certificate(firebase_credentials)
    else:
        cred = credentials.Certificate("firebase_key.json")

    firebase_admin.initialize_app(cred)

db = firestore.client()

# 🔹 CONFIGURAÇÃO DO HUGGING FACE
huggingface_api_token = st.secrets["HUGGINGFACE_API_TOKEN"]
if not huggingface_api_token:
    raise ValueError("A chave da Hugging Face não foi carregada! Verifique o .env ou as variáveis de ambiente.")

def model_hf_hub(model="meta-llama/Meta-Llama-3-8B-Instruct", temperature=0.1):
    return HuggingFaceHub(
        repo_id=model,
        huggingfacehub_api_token=huggingface_api_token,  
        model_kwargs={
            "temperature": temperature,
            "return_full_text": False,
            "max_new_tokens": 512
        }
    )

# 🔹 FUNÇÃO PARA CARREGAR NORMATIVOS DO FIRESTORE
def carregar_normativos():
    try:
        docs = db.collection("normativos").stream()
        normativos = {doc.id: doc.to_dict().get("conteudo", "") for doc in docs}
        return normativos if normativos else {}  
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar normativos: {e}")
        return {}  

# 🔹 EXTRAÇÃO DE TEXTO DE PDF
def extrair_texto_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        return text
    except Exception as e:
        st.error(f"Erro ao ler o PDF: {e}")
        return ""

# 🔹 CARREGAMENTO DE NORMATIVOS
normativos_carregados = carregar_normativos()

# 🔹 CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Validador e Pesquisa de Normativos", page_icon="📜", layout="wide")

# 🔹 Exibir status do banco de dados
if normativos_carregados:
    st.sidebar.success("✅ Normativos salvos no banco de dados!")
    with st.sidebar.expander("📂 **Ver Normativos no Banco**", expanded=False):
        for nome in normativos_carregados.keys():
            st.write(f"- 📜 {nome}")
else:
    st.sidebar.warning("⚠️ Nenhum normativo encontrado. Por favor, faça o upload.")

# 🔹 UPLOAD DE NOVOS NORMATIVOS
uploaded_normativos = st.sidebar.file_uploader("📂 Enviar Normativos (PDF)", accept_multiple_files=True)
if uploaded_normativos:
    for file in uploaded_normativos:
        nome = file.name
        conteudo = extrair_texto_pdf(file)
        db.collection("normativos").document(nome).set({"conteudo": conteudo})

    st.sidebar.success("✅ Normativos salvos no banco de dados!")
    normativos_carregados = carregar_normativos()

# 🔹 UPLOAD DE TR E ETP
uploaded_tr = st.sidebar.file_uploader("📑 Envie o Termo de Referência (PDF)", type="pdf")
uploaded_etp = st.sidebar.file_uploader("📄 Envie o Estudo Técnico Preliminar (PDF)", type="pdf")

# 🔹 ENTRADA DE PESQUISA (CORRIGIDO)
pesquisa_usuario = st.text_input("🔍 Pesquisar nos normativos")

# 🔹 Verifica se o usuário digitou uma pesquisa
if pesquisa_usuario:
    resposta_completa = ""
    fontes_utilizadas = []

    filtro_normativos = {
        "decreto 44330": "Decreto 44330 de 16_03_2023.pdf",
        "lei 14133": "L14133.pdf",
        "instrução normativa 94/22": "Instrução Normativa n94-22.pdf",
        "instrução normativa 65/21": "INSTRUÇÃO NORMATIVA n 65-21.pdf"
    }

    normativo_escolhido = None
    for termo, arquivo in filtro_normativos.items():
        if termo in pesquisa_usuario.lower():
            normativo_escolhido = arquivo
            break

    if normativo_escolhido and normativo_escolhido in normativos_carregados:
        texto_normativo = normativos_carregados[normativo_escolhido]
        prompt_template = ChatPromptTemplate.from_template(
            f"📜 **{normativo_escolhido}**:\n{texto_normativo[:4000]}\n\n"
            f"**Pergunta:** {pesquisa_usuario}\n"
            f"**Resposta:**"
        )
        llm = model_hf_hub()
        resposta = llm(prompt_template.format(input=pesquisa_usuario))
        resposta_completa = f"📜 **Fonte:** {normativo_escolhido}\n\n{resposta}"
        fontes_utilizadas.append(normativo_escolhido)

    st.subheader("🤖 Resposta do Assistente")
    if resposta_completa:
        st.write(resposta_completa)
    else:
        st.warning("❌ Nenhuma informação relevante encontrada nos normativos.")

# 🔹 CONFIGURAÇÃO DO CHECKLIST (NÃO FOI ALTERADO)
st.title("📜 Validador de Termo de Referência e Estudo Técnico Preliminar")
st.write("O sistema verifica se os documentos atendem às exigências legais e normativas.")

checklist_tr = {
    "Definição do Objeto": "Definição do Objeto|Objeto da Contratação|Objeto",
    "Justificativa": "Justificativa|Descrição da Necessidade",
    "Fundamentação Legal": "Fundamentação Legal|Base Legal|Fundamentação",
    "Especificações Técnicas": "Especificações Técnicas|Especificações do Objeto|Das Especificações do Objeto",
    "Critérios de Aceitação": "Critérios de Aceitação|Aceite",
    "Modelo de Execução do Objeto": "Modelo de Execução do Objeto|Condições de execução|Obrigações da Contatada|Obrigações da Contratante",
    "Modelo de Gestão do Contrato": "Modelo de Gestão do Contrato|Preposto|Fiscalização",
    "Pesquisa de Preços": "Pesquisa de Preços|Estimativa de Custos|Estimativa de Preços|Preços Referenciais",
    "Resultados Esperados": "Resultados Esperados|Metas|Impactos Esperados",
    "Classificação de Bem Comum": "Classificação de Bem Comum|Classificação|Bem Comum",
    "Garantia": "Garantia|Assistência Técnica|Vigência Contratual|Vigência",
    "Garantia Contratual": "Garantia Contratual",
    "Critérios de Medição e Pagamento": "Critérios de Medição e Pagamento|Pagamento|Do Pagamento",
    "Parcelamento do Objeto": "Parcelamento do Objeto|Parcelamento|Do Parcelamento",
}

checklist_etp = {
    "Introdução": "Introdução|Objeto",
    "Descrição da Necessidade": "Descrição da Necessidade|Motivação|Justificativa|Detalhes|Descrição|Necessidade da Contratação",
    "Definição e Especificação dos Requisitos": "Definição e Especificação dos Requisitos|Definição e Especificação das Necessidades e Requisitos|Especificação do Objeto|Descrição da Solução",
    "Alternativas de Mercado": "Alternativas de Mercado|Alternativas do Mercado|Levantamento de Mercado",
    "Detalhamento da Solução": "Detalhamento da Solução|Solução",
    "Justificativa da Solução Escolhida": "Justificativa da Solução Escolhida|Justificativa do Cenário Escolhido|Justificativa Final",
    "Pesquisa de Preços": "Pesquisa de Preços|Estimativa de Custos|Estimativa do Custo Total",
    "Alternativas Analisadas": "Alternativas Analisadas|Alternativas de Mercado|Fontes",
    "Viabilidade Técnica e Econômica": "Viabilidade Técnica e Econômica|Declaração de Viabilidade|Viabilidade da Contratação",
}

# 🔹 Função para verificar checklist
def verificar_checklist(texto, checklist):
    return {pergunta: bool(re.search(referencia, texto, re.IGNORECASE)) for pergunta, referencia in checklist.items()}

# 🔹 Definir listas vazias antes da verificação
faltantes_tr, faltantes_etp = [], []

# 🔹 Verifica o TR e o ETP separadamente
if uploaded_tr:
    tr_texto = extrair_texto_pdf(uploaded_tr)
    st.success("📑 Termo de Referência carregado! Analisando...")
    checklist_resultados_tr = verificar_checklist(tr_texto, checklist_tr)
    faltantes_tr = [item for item, presente in checklist_resultados_tr.items() if not presente]

if uploaded_etp:
    etp_texto = extrair_texto_pdf(uploaded_etp)
    st.success("📄 Estudo Técnico Preliminar carregado! Analisando...")
    checklist_resultados_etp = verificar_checklist(etp_texto, checklist_etp)
    faltantes_etp = [item for item, presente in checklist_resultados_etp.items() if not presente]

# 🔹 Exibir checklist do TR
if uploaded_tr:
    st.subheader("📋 Checklist do Termo de Referência")
    for pergunta, presente in checklist_resultados_tr.items():
        st.write(f"- {pergunta}: {'✅ Presente' if presente else '❌ Ausente'}")

# 🔹 Exibir checklist do ETP
if uploaded_etp:
    st.subheader("📋 Checklist do Estudo Técnico Preliminar")
    for pergunta, presente in checklist_resultados_etp.items():
        st.write(f"- {pergunta}: {'✅ Presente' if presente else '❌ Ausente'}")
        
# 🔹 Geração do relatório final separando TR e ETP
if uploaded_tr or uploaded_etp:
    st.subheader("📄 Conclusão")
    
    if faltantes_tr:
        st.write("🚨 **Itens ausentes no Termo de Referência (TR):**")
        for item in faltantes_tr:
            st.write(f"- ❌ {item}")

    if faltantes_etp:
        st.write("🚨 **Itens ausentes no Estudo Técnico Preliminar (ETP):**")
        for item in faltantes_etp:
            st.write(f"- ❌ {item}")

    if not faltantes_tr and not faltantes_etp:
        st.success("✅ O Termo de Referência e o Estudo Técnico Preliminar estão completos e podem seguir para a próxima etapa.")
    else:
        st.warning("⚠️ O Termo de Referência ou o Estudo Técnico Preliminar precisam ser corrigidos antes de seguir.")
