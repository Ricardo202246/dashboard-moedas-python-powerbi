# importar as bibliotecas
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import timedelta

# carregar os tickers do arquivo IBOV.csv
@st.cache_data
def carregar_tickers_acoes():
    base_tickers = pd.read_csv("IBOV.csv", sep=";")

    # limpar nome das colunas
    base_tickers.columns = base_tickers.columns.str.strip()

    # limpar os códigos das ações
    base_tickers["Código"] = base_tickers["Código"].astype(str).str.strip()

    # remover vazios e duplicados
    tickers = base_tickers["Código"].dropna().unique().tolist()

    # adicionar .SA para o Yahoo Finance
    tickers = [
        item + ".SA"
        for item in tickers
        if item != "" and item.lower() != "nan"
    ]

    return tickers


# carregar cotações pelo Yahoo Finance
@st.cache_data
def carregar_dados(empresas):
    cotacoes_acao = yf.download(
        empresas,
        start="2010-01-01",
        end="2024-07-01",
        auto_adjust=True
    )

    # pegar somente o preço de fechamento
    cotacoes_acao = cotacoes_acao["Close"]

    # garantir que o índice seja data válida
    cotacoes_acao.index = pd.to_datetime(cotacoes_acao.index, errors="coerce")
    cotacoes_acao = cotacoes_acao[~cotacoes_acao.index.isna()]

    # remover ações sem nenhuma cotação
    cotacoes_acao = cotacoes_acao.dropna(axis=1, how="all")

    return cotacoes_acao


# carregar dados
acoes = carregar_tickers_acoes()
dados = carregar_dados(acoes)

# interface do Streamlit
st.write("""
# App Preço de Ações

O gráfico abaixo representa a evolução do preço das ações ao longo dos anos.
""")

# validação inicial
if dados.empty:
    st.error("Nenhum dado foi carregado. Verifique o arquivo IBOV.csv ou os tickers.")
    st.stop()

# filtros
st.sidebar.header("Filtros")

# filtro de ações
lista_acoes = st.sidebar.multiselect(
    "Escolha as ações para visualizar",
    dados.columns
)

if lista_acoes:
    dados = dados[lista_acoes]

# garantir índice de data válido
dados.index = pd.to_datetime(dados.index, errors="coerce")
dados = dados[~dados.index.isna()]

# remover colunas totalmente vazias
dados = dados.dropna(axis=1, how="all")

if dados.empty:
    st.error("Não existem dados disponíveis para as ações selecionadas.")
    st.stop()

# filtro de datas
data_inicial = dados.index.min().to_pydatetime()
data_final = dados.index.max().to_pydatetime()

intervalo_data = st.sidebar.slider(
    "Selecione o período",
    min_value=data_inicial,
    max_value=data_final,
    value=(data_inicial, data_final),
    step=timedelta(days=1)
)

# aplicar filtro de datas
dados = dados.loc[intervalo_data[0]:intervalo_data[1]]

if dados.empty:
    st.warning("Não existem dados no período selecionado.")
    st.stop()

# gráfico
st.line_chart(dados)

# cálculo de performance
texto_performance_ativos = ""

if len(lista_acoes) == 0:
    lista_acoes = list(dados.columns)

carteira = [1000 for acao in lista_acoes]
total_inicial_carteira = sum(carteira)

for i, acao in enumerate(lista_acoes):
    serie_acao = dados[acao].dropna()

    if len(serie_acao) < 2:
        texto_performance_ativos += f"  \n{acao}: sem dados suficientes"
        carteira[i] = 0
        continue

    performance_ativo = serie_acao.iloc[-1] / serie_acao.iloc[0] - 1
    performance_ativo = float(performance_ativo)

    carteira[i] = carteira[i] * (1 + performance_ativo)

    if performance_ativo > 0:
        texto_performance_ativos += f"  \n{acao}: :green[{performance_ativo:.1%}]"
    elif performance_ativo < 0:
        texto_performance_ativos += f"  \n{acao}: :red[{performance_ativo:.1%}]"
    else:
        texto_performance_ativos += f"  \n{acao}: {performance_ativo:.1%}"

total_final_carteira = sum(carteira)
performance_carteira = total_final_carteira / total_inicial_carteira - 1

if performance_carteira > 0:
    texto_performance_carteira = f"Performance da carteira com todos os ativos: :green[{performance_carteira:.1%}]"
elif performance_carteira < 0:
    texto_performance_carteira = f"Performance da carteira com todos os ativos: :red[{performance_carteira:.1%}]"
else:
    texto_performance_carteira = f"Performance da carteira com todos os ativos: {performance_carteira:.1%}"

st.write(f"""
### Performance dos Ativos

Essa foi a performance de cada ativo no período selecionado:

{texto_performance_ativos}

{texto_performance_carteira}
""")