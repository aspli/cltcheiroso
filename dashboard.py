import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração inicial da página
st.set_page_config(page_title="Inteligência de Vendas ITB", layout="wide", page_icon="📊")

# 2. Carregamento dos dados com Cache (para o app ficar super rápido)
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("ranking_vendas_inthebox.csv")
        return df
    except FileNotFoundError:
        st.error("Arquivo 'ranking_vendas_inthebox.csv' não encontrado. Rode o extrator primeiro!")
        return pd.DataFrame()

df = carregar_dados()

if not df.empty:
    st.title("📊 Dashboard de Vendas Estimadas - In The Box")
    st.markdown("Visão geral de popularidade baseada no volume de avaliações extraídas da plataforma Yourviews.")
    st.divider()

    # 3. Métricas Principais (KPIs)
    col1, col2, col3 = st.columns(3)
    
    total_perfumes = len(df)
    total_avaliacoes = df['Avaliacoes'].sum()
    total_vendas_estimadas = df['Vendas_Estimadas'].sum()
    
    col1.metric("Total de Perfumes Mapeados", total_perfumes)
    col2.metric("Total de Avaliações Extraídas", f"{total_avaliacoes:,}")
    col3.metric("Volume de Vendas Estimadas", f"{total_vendas_estimadas:,}")

    st.divider()

    # 4. Gráfico do Top 15 Mais Vendidos
    st.subheader("🏆 Top 15 Perfumes Mais Populares")
    
    # Pega os 15 primeiros (como o df já foi salvo ordenado, basta dar head)
    top_15 = df.head(15).sort_values(by='Vendas_Estimadas', ascending=True) 
    
    # Usando Plotly para um gráfico interativo bonito
    fig = px.bar(
        top_15, 
        x='Vendas_Estimadas', 
        y='Perfume', 
        orientation='h',
        text='Vendas_Estimadas',
        color='Vendas_Estimadas',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        xaxis_title="Vendas Estimadas",
        yaxis_title="",
        coloraxis_showscale=False,
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # 5. Tabela Completa Interativa
    st.subheader("📋 Base de Dados Completa")
    
    # Barra de pesquisa
    pesquisa = st.text_input("🔍 Pesquisar perfume específico:")
    
    if pesquisa:
        df_filtrado = df[df['Perfume'].str.contains(pesquisa, case=False, na=False)]
    else:
        df_filtrado = df
        
    # Exibe a tabela interativa onde você pode clicar nas colunas para ordenar
    st.dataframe(
        df_filtrado[['Perfume', 'Avaliacoes', 'Vendas_Estimadas']], 
        use_container_width=True,
        hide_index=True
    )