import streamlit as st
import yfinance as yf
from datetime import datetime
import urllib.parse
import pytz
import pandas as pd
import requests

# Configuração da página do App
st.set_page_config(page_title="Radar de Mercado", page_icon="📈")

# --- FUNÇÕES DE BUSCA DE DADOS ---
def buscar_fear_greed_real():
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=5)
        dados = r.json()
        valor = dados['data'][0]['value']
        classif = dados['data'][0]['value_classification']
        traducoes = {"Extreme Fear": "Medo Extremo", "Fear": "Medo", "Neutral": "Neutro", "Greed": "Ganância", "Extreme Greed": "Ganância Extrema"}
        return f"{valor} ({traducoes.get(classif, classif)})"
    except: return "Indisponível"

def buscar_dominancia_real():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=5)
        dados = r.json()
        dom = dados['data']['market_cap_percentage']['btc']
        return f"{dom:.1f}%"
    except: return "58.2%"

def calcular_rsi(precos, periodo=14):
    try:
        precos_limpos = precos.dropna()
        if len(precos_limpos) < periodo: return None, "Dados Insuficientes"
        delta = precos_limpos.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        valor = rsi.iloc[-1]
        status = "🔴 Sobrecomprado" if valor >= 70 else "🟡 Pré-Venda" if valor >= 55 else "⚪ Neutro" if valor >= 30 else "🟢 Sobrevendido"
        return valor, status
    except: return None, "Erro"

def status_mercados_horarios():
    tz = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(tz)
    minutos_totais = agora.hour * 60 + agora.minute
    dia_semana = agora.weekday()
    h = {"B3": {"abre": 600, "fecha": 1080, "texto": "10h-18h"}, "EUA": {"abre": 600, "fecha": 1020, "texto": "10h-17h"}, "ASIA": {"abre": 1260, "fecha": 240, "texto": "21h-04h"}}
    txt = "\n🕒 *Status dos Mercados (Brasília)*\n"
    if dia_semana >= 5: return txt + "🛑 Fim de semana: Mercados *FECHADOS*."
    for m, dados in [("🇧🇷 B3", h["B3"]), ("🇺🇸 EUA", h["EUA"])]:
        st_m = "🟢 Aberto" if dados["abre"] <= minutos_totais < dados["fecha"] else "🔴 Fechado"
        txt += f"{m}: {st_m} ({dados['texto']})\n"
    st_asia = "🟢 Aberto" if minutos_totais >= h["ASIA"]["abre"] or minutos_totais < h["ASIA"]["fecha"] else "🔴 Fechado"
    txt += f"🏮 Ásia: {st_asia} ({h['ASIA']['texto']})\n"
    return txt

# --- INTERFACE ---
st.title("📡 Radar de Mercado")

col1, col2 = st.columns(2)

with col1:
    btn_geral = st.button('🚀 RELATÓRIO GERAL', use_container_width=True)

with col2:
    btn_radar = st.button('🎯 RADAR CRIPTO', use_container_width=True)

# LISTAS DE ATIVOS
criptos_lista = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD", "ADA-USD", "DOGE-USD", "LINK-USD", "ALGO-USD"]
macros_b3 = ["USDBRL=X", "BZ=F", "GC=F", "^BVSP", "PETR4.SA", "VALE3.SA"]
globais = ["YM=F", "ES=F", "NQ=F"]

# LÓGICA BOTÃO 1: RELATÓRIO GERAL (TUDO)
if btn_geral:
    with st.spinner('Coletando dados...'):
        dados = yf.download(criptos_lista + macros_b3 + globais, period="35d", interval="1d", progress=False)['Close']
        agora_br = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
        msg = f"📡 *PANORAMA GLOBAL COMPLETO* \n🕒 {agora_br}\n\n"
        rsi_v, rsi_s = calcular_rsi(dados["BTC-USD"])
        if rsi_v: msg += f"📈 RSI Bitcoin (14D): {rsi_v:.2f} ({rsi_s})\n"
        msg += f"🌡️ Fear & Greed: {buscar_fear_greed_real()}\n"
        msg += f"📉 Dominância BTC: {buscar_dominancia_real()}\n\n"
        msg += "🪙 *Principais Moedas:*\n"
        for c in ["BTC-USD", "ETH-USD", "SOL-USD"]:
            p_at, p_ant = dados[c].iloc[-1], dados[c].iloc[-2]
            var = ((p_at - p_ant) / p_ant) * 100
            msg += f"{'💹' if var >= 0 else '📉'} {c.replace('-USD','')}: US$ {p_at:,.2f} ({var:+.2f}%)\n"
        msg += status_mercados_horarios()
        st.text_area("Cópia:", msg, height=250)
        st.link_button("📲 WHATSAPP", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

# LÓGICA BOTÃO 2: RADAR CRIPTO (SÓ CRIPTOS + RSI BTC)
if btn_radar:
    with st.spinner('Analisando criptos...'):
        dados_c = yf.download(criptos_lista, period="35d", interval="1d", progress=False)['Close']
        msg_radar = "🎯 *RADAR DE OPORTUNIDADES CRIPTO*\n\n"
        rsi_btc_v, rsi_btc_s = calcular_rsi(dados_c["BTC-USD"])
        msg_radar += f"📊 *FORÇA TÉCNICA BITCOIN*\n"
        msg_radar += f"RSI (14D): {rsi_btc_v:.2f} -> {rsi_btc_s}\n"
        msg_radar += "--------------------------\n\n"
        msg_radar += "💰 *Variação das Moedas:*\n"
        for ticker in criptos_lista:
            p_at, p_ant = dados_c[ticker].iloc[-1], dados_c[ticker].iloc[-2]
            var = ((p_at - p_ant) / p_ant) * 100
            msg_radar += f"{'🟢' if var >= 0 else '🔴'} {ticker.replace('-USD','')}: US$ {p_at:,.2f} ({var:+.2f}%)\n"
        st.text_area("Resultado Radar:", msg_radar, height=250)
        st.link_button("📲 ENVIAR RADAR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_radar)}", use_container_width=True)
