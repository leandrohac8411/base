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
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f'Erro ao ler o PDF: {e}')
        return ""

# Processa os normativos
if 'base_conhecimento' not in st.session_state:
    st.session_state['base_conhecimento'] = ""
    st.session_state['normativos_carregados'] = False

if uploaded_normativos:
    st.session_state['base_conhecimento'] = "".join(extrair_texto_pdf(file) for file in uploaded_normativos)
    st.session_state['normativos_carregados'] = True
    st.sidebar.success("Normativos carregados e salvos!")

elif st.session_state['normativos_carregados']:
    st.sidebar.info("Normativos já carregados na base de conhecimento.")
else:
    st.sidebar.warning("Nenhum normativo encontrado. Por favor, faça o upload.")

# Verifica se os documentos foram carregados
if not uploaded_tr and not uploaded_etp:
    st.warning("Nenhum Termo de Referência ou Estudo Técnico Preliminar foi carregado. Por favor, faça o upload dos documentos.")

# Lista de perguntas do checklist do Tribunal de Contas
checklist_tc = {
    "1. Foi elaborado o Estudo Técnico Preliminar da Contratação?": "Estudo Técnico Preliminar",
    "2. O ETP contempla a descrição da necessidade, estimativa do quantitativo e do valor?": "Descrição da necessidade|Estimativa do quantitativo|Estimativa do valor",
    "3. O ETP contempla todos os elementos do art. 11 da IN SGD nº 94/2022?": "(definição e especificação das necessidades|análise comparativa de soluções|análise comparativa de custos|estimativa do custo total|declaração da viabilidade da contratação)",
    "4. Foi elaborado Termo de Referência conforme exigências legais?": "Termo de Referência",
    "5. A definição do objeto está clara e sem especificações restritivas?": "Definição do Objeto",
}

# Lista de requisitos da Lei 14.133 e IN 94/2022
checklist_lei = {
    "6. O TR contém a definição clara do objeto?": "Definição do Objeto",
    "7. O TR contém justificativa detalhada da contratação?": "Justificativa",
    "8. O TR contém fundamentação legal adequada?": "Fundamentação Legal|Base Legal|Fundamentação",
    "9. O TR contém especificações técnicas detalhadas?": "Especificações Técnicas",
    "10. O TR contém critérios de aceitação bem definidos?": "Critérios de Aceitação",
    "11. O TR contém pesquisa de preços conforme a legislação?": "Pesquisa de Preços|Estimativa de Custos",
}

# Função para verificar checklist
def verificar_checklist(texto, checklist):
    resultados = {}
    for pergunta, referencia in checklist.items():
        resultados[pergunta] = bool(re.search(referencia, texto, re.IGNORECASE))
    return resultados

# Verifica o TR e o ETP
checklist_resultados_tr, checklist_resultados_etp = {}, {}
if uploaded_tr:
    tr_texto = extrair_texto_pdf(uploaded_tr)
    st.success("Termo de Referência carregado! Analisando...")
    checklist_resultados_tr = verificar_checklist(tr_texto, checklist_lei)

if uploaded_etp:
    etp_texto = extrair_texto_pdf(uploaded_etp)
    st.success("Estudo Técnico Preliminar carregado! Analisando...")
    checklist_resultados_etp = verificar_checklist(etp_texto, checklist_tc)

# Exibir checklist do Tribunal de Contas e da Lei 14.133/2021 e IN 94/2022
if uploaded_tr:
    st.subheader("📋 Checklist do Tribunal de Contas e Legislação - Termo de Referência")
    for pergunta, presente in checklist_resultados_tr.items():
        st.write(f"- {pergunta}: {'✅ Presente' if presente else '❌ Ausente'}")

if uploaded_etp:
    st.subheader("📋 Checklist do Tribunal de Contas - Estudo Técnico Preliminar")
    for pergunta, presente in checklist_resultados_etp.items():
        st.write(f"- {pergunta}: {'✅ Presente' if presente else '❌ Ausente'}")
