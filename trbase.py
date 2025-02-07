import streamlit as st
import PyPDF2
import re

st.set_page_config(page_title="Validador de Artefatos 📚", page_icon="📚", layout="wide")
st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>📜 Validador de Artefatos</h1>", unsafe_allow_html=True)

st.sidebar.header("📂 Enviar Documentos")
uploaded_dfd = st.sidebar.file_uploader("📜 Envie o Documento de Formalização da Demanda (DFD)", type="pdf")
uploaded_etp = st.sidebar.file_uploader("📄 Envie o Estudo Técnico Preliminar (ETP)", type="pdf")
uploaded_tr = st.sidebar.file_uploader("📑 Envie o Termo de Referência (TR)", type="pdf")

def extrair_texto_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception as e:
        st.sidebar.error(f'Erro ao ler o PDF: {e}')
        return ""

checklist_dfd = {
    "Justificativa da Necessidade": "Justificativa da Necessidade|Justificativa|Motivação|JUSTIFICATIVA/MOTIVAÇÃO DA DEMANDA",
    "Descrição Sucinta do Objeto": "Descrição Sucinta do Objeto|Objeto da contratação proposta",
    "Quantidade a Ser Contratada": "Quantidade a ser contratada|QTDE. PREVISTA|Quantidade Prevista",
    "Estimativa Preliminar do Valor": "Estimativa Preliminar do Valor|Valor Estimado",
    "Data Pretendida para Conclusão": "Data pretendida para a conclusão|Prazo de Execução",
    "Grau de Prioridade": "Grau de Prioridade",
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

def verificar_checklist(texto, checklist):
    return {pergunta: bool(re.search(referencia, texto, re.IGNORECASE)) for pergunta, referencia in checklist.items()}

col1, col2, col3 = st.columns(3)

with col1:
    st.header("📋 Resultado do DFD")
    faltantes_dfd = []
    if uploaded_dfd:
        dfd_texto = extrair_texto_pdf(uploaded_dfd)
        checklist_resultados_dfd = verificar_checklist(dfd_texto, checklist_dfd)
        for pergunta, presente in checklist_resultados_dfd.items():
            st.write(f"- {pergunta}: {'✅ Presente' if presente else '❌ Ausente'}")
            if not presente:
                faltantes_dfd.append(pergunta)

with col2:
    st.header("📋 Resultado do ETP")
    faltantes_etp = []
    if uploaded_etp:
        etp_texto = extrair_texto_pdf(uploaded_etp)
        checklist_resultados_etp = verificar_checklist(etp_texto, checklist_etp)
        for pergunta, presente in checklist_resultados_etp.items():
            st.write(f"- {pergunta}: {'✅ Presente' if presente else '❌ Ausente'}")
            if not presente:
                faltantes_etp.append(pergunta)

with col3:
    st.header("📋 Resultado do TR")
    faltantes_tr = []
    if uploaded_tr:
        tr_texto = extrair_texto_pdf(uploaded_tr)
        checklist_resultados_tr = verificar_checklist(tr_texto, checklist_tr)
        for pergunta, presente in checklist_resultados_tr.items():
            st.write(f"- {pergunta}: {'✅ Presente' if presente else '❌ Ausente'}")
            if not presente:
                faltantes_tr.append(pergunta)

if uploaded_dfd or uploaded_etp or uploaded_tr:
    st.subheader("📄 Conclusão")
    if faltantes_dfd:
        st.write("🚨 **Itens ausentes no Documento de Formalização da Demanda (DFD):**")
        for item in faltantes_dfd:
            st.write(f"- ❌ {item}")
    
    if faltantes_etp:
        st.write("🚨 **Itens ausentes no Estudo Técnico Preliminar (ETP):**")
        for item in faltantes_etp:
            st.write(f"- ❌ {item}")
    
    if faltantes_tr:
        st.write("🚨 **Itens ausentes no Termo de Referência (TR):**")
        for item in faltantes_tr:
            st.write(f"- ❌ {item}")
    
    if not faltantes_dfd and not faltantes_etp and not faltantes_tr:
        st.success("✅ Todos os artefatos estão completos e podem seguir para a próxima etapa.")
    else:
        st.warning("⚠️ Alguns artefatos precisam ser corrigidos antes de seguir.")
