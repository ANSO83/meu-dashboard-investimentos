import pandas as pd
import sqlite3
import requests
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime

# Conectar a um banco de dados SQLite
conn = sqlite3.connect("investimentos.db")
cursor = conn.cursor()

# Criar a tabela de investimentos (se ainda não existir)
cursor.execute('''
CREATE TABLE IF NOT EXISTS investimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    acao TEXT,
    ativo TEXT,
    corretora TEXT,
    quantidade REAL,
    preco REAL,
    total REAL
)
''')

# Criar a tabela para armazenar histórico de cotações
cursor.execute('''
CREATE TABLE IF NOT EXISTS historico_cotacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ativo TEXT,
    data TEXT,
    abertura REAL,
    alta REAL,
    baixa REAL,
    fechamento REAL,
    volume REAL
)
''')

# Criar tabela para acompanhamento diário do patrimônio
cursor.execute('''
CREATE TABLE IF NOT EXISTS patrimonio_diario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    patrimonio_total REAL
)
''')
conn.commit()

def buscar_cotacao_binance(simbolo):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={simbolo}"
    response = requests.get(url)
    if response.status_code == 200:
        return float(response.json()["price"])
    else:
        print("Erro ao buscar cotação.")
        return None

def calcular_patrimonio_total():
    df = pd.read_sql_query("SELECT ativo, quantidade FROM investimentos", conn)
    patrimonio_total = 0
    for _, row in df.iterrows():
        cotacao = buscar_cotacao_binance(row["ativo"] + "USDT")
        if cotacao:
            patrimonio_total += row["quantidade"] * cotacao
    cursor.execute("INSERT INTO patrimonio_diario (data, patrimonio_total) VALUES (?, ?)",
                   (datetime.now().strftime('%Y-%m-%d'), patrimonio_total))
    conn.commit()
    print(f"Patrimônio total atualizado: {patrimonio_total:.2f}")

def exibir_patrimonio_diario():
    df = pd.read_sql_query("SELECT * FROM patrimonio_diario", conn)
    return df

def plotar_evolucao_patrimonio(df):
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values("data")
    st.line_chart(df.set_index("data"))

def main():
    st.title("Dashboard de Investimentos")
    st.sidebar.header("Opções")

    if st.sidebar.button("Atualizar Patrimônio"):
        calcular_patrimonio_total()
        st.sidebar.success("Patrimônio atualizado!")

    st.header("Evolução do Patrimônio")
    df_patrimonio = exibir_patrimonio_diario()
    st.dataframe(df_patrimonio)
    plotar_evolucao_patrimonio(df_patrimonio)

if __name__ == "__main__":
    main()
    conn.close()
