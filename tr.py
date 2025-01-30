import streamlit as st
import PyPDF2
import re

# Configuração da Página
st.set_page_config(page_title="Validador de TR e ETP", page_icon="📜", layout="wide")

st.title("📜 Validador de Termo de Referência e Estudo Técnico Preliminar")
st.write("O sistema verifica se o Termo de Referência (TR) e o Estudo Técnico Preliminar (ETP) atendem às exigências legais e normativas.")

# Upload dos documentos normativos e do TR/ETP para análise
st.sidebar.header("📂 Enviar Documentos")

uploaded_normativos = st.sidebar.file_uploader(
    "Envie os normativos para base de conhecimento (PDF)", accept_multiple_files=True
)

uploaded_tr = st.sidebar.file_uploader("📑 Envie o Termo de Referência (PDF)", type="pdf")
uploaded_etp = st.sidebar.file_uploader("📄 Envie o Estudo Técnico Preliminar (PDF)", type="pdf")

# Função para extrair texto de PDFs
def extrair_texto_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
    except Exception as e:
        st.error(f'Erro ao ler o PDF: {e}')
        return ""
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# Processa os normativos
if uploaded_normativos:
    base_conhecimento = ""
    for file in uploaded_normativos:
        base_conhecimento += extrair_texto_pdf(file)
    st.sidebar.success("Normativos carregados!")

# Verifica o Termo de Referência
if uploaded_tr:
    tr_texto = extrair_texto_pdf(uploaded_tr)
    st.success("Termo de Referência carregado! Analisando...")

    # Checklist dos itens obrigatórios conforme a Lei e INs
    checklist_tr = {
        "Definição do Objeto": bool(re.search(r"(Definição do Objeto|Objeto da Contratação)", tr_texto, re.IGNORECASE)),
        "Justificativa": bool(re.search(r"(Justificativa)", tr_texto, re.IGNORECASE)),
        "Fundamentação Legal": bool(re.search(r"(Fundamentação Legal|Base Legal|Fundamentação)", tr_texto, re.IGNORECASE)),
        "Especificações Técnicas": bool(re.search(r"(Especificações Técnicas)", tr_texto, re.IGNORECASE)),
        "Critérios de Aceitação": bool(re.search(r"(Critérios de Aceitação)", tr_texto, re.IGNORECASE)),
        "Pesquisa de Preços": bool(re.search(r"(Pesquisa de Preços|Estimativa de Custos)", tr_texto, re.IGNORECASE)),
    }

    # Exibir checklist do TR
    st.subheader("📋 Checklist do Termo de Referência")
    for item, presente in checklist_tr.items():
        st.write(f"- {item}: {'✅ Presente' if presente else '❌ Ausente'}")

# Verifica o Estudo Técnico Preliminar
if uploaded_etp:
    etp_texto = extrair_texto_pdf(uploaded_etp)
    st.success("Estudo Técnico Preliminar carregado! Analisando...")

    # Checklist dos itens obrigatórios conforme normativas
    checklist_etp = {
        "Introdução": bool(re.search(r"(Introdução)", etp_texto, re.IGNORECASE)),
        "Descrição da Necessidade": bool(re.search(r"(Descrição da Necessidade)", etp_texto, re.IGNORECASE)),
        "Definição e Especificação dos Requisitos": bool(re.search(r"(Definição e Especificação dos Requisitos|Definição e Especificação das Necessidades e Requisitos)", etp_texto, re.IGNORECASE)),
        "Justificativa da Solução Escolhida": bool(re.search(r"(Justificativa da Solução Escolhida|Justificativa do Cenário Escolhido)", etp_texto, re.IGNORECASE)),
        "Pesquisa de Preços": bool(re.search(r"(Pesquisa de Preços)", etp_texto, re.IGNORECASE)),
        "Alternativas Analisadas": bool(re.search(r"(Alternativas Analisadas|Alternativas de Mercado)", etp_texto, re.IGNORECASE)),
        "Viabilidade Técnica e Econômica": bool(re.search(r"(Viabilidade Técnica e Econômica)", etp_texto, re.IGNORECASE)),
    }

    # Exibir checklist do ETP
    st.subheader("📋 Checklist do Estudo Técnico Preliminar")
    for item, presente in checklist_etp.items():
        st.write(f"- {item}: {'✅ Presente' if presente else '❌ Ausente'}")

# Geração do relatório final
if uploaded_tr or uploaded_etp:
    st.subheader("📄 Conclusão")
    tr_ok = all(checklist_tr.values()) if uploaded_tr else True
    etp_ok = all(checklist_etp.values()) if uploaded_etp else True

    if tr_ok and etp_ok:
        st.success("O Termo de Referência e o Estudo Técnico Preliminar estão completos e podem seguir para a próxima etapa. ✅")
    else:
        st.error("O Termo de Referência ou o Estudo Técnico Preliminar precisam ser corrigidos antes de seguir. ❌")
        if uploaded_tr:
            faltantes_tr = [item for item, presente in checklist_tr.items() if not presente]
            if faltantes_tr:
                st.write("Itens ausentes no Termo de Referência (TR):")
                for item in faltantes_tr:
                    st.write(f"- ❌ {item}")
        if uploaded_etp:
            faltantes_etp = [item for item, presente in checklist_etp.items() if not presente]
            if faltantes_etp:
                st.write("Itens ausentes no Estudo Técnico Preliminar (ETP):")
                for item in faltantes_etp:
                    st.write(f"- ❌ {item}")
