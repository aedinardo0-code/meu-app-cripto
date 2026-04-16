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

if st.button('🚀 GERAR RELATÓRIO AGORA', use_container_width=True):
    with st.spinner('Coletando dados...'):
        agora_br = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
        criptos = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD", "POL-USD", "ADA-USD", "DOT-USD", "LINK-USD", "DOGE-USD"]
        macros = ["USDBRL=X", "BZ=F", "GC=F", "SI=F", "^TNX"]
        b3 = ["^BVSP", "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]
        globais = ["YM=F", "ES=F", "NQ=F"]
        
        dados = yf.download(criptos + macros + b3 + globais, period="35d", interval="1d", progress=False)['Close']
        fng_real = buscar_fear_greed_real()
        dom_real = buscar_dominancia_real()

        msg = f"📡 *PANORAMA GLOBAL & CRIPTO* \n🕒 {agora_br}\n\n"
        rsi_v, rsi_s = calcular_rsi(dados["BTC-USD"])
        if rsi_v: msg += f"📈 RSI Bitcoin (14D): {rsi_v:.2f} ({rsi_s})\n"
        msg += f"🌡️ Fear & Greed Index: {fng_real}\n"
        msg += f"📉 Dominância BTC: {dom_real}\n\n"

        msg += "🪙 *Principais Criptos:*\n"
        for nome, t in {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD"}.items():
            col = dados[t].dropna()
            p_at, p_ant = col.iloc[-1], col.iloc[-2]
            var = ((p_at - p_ant) / p_ant) * 100
            msg += f"{'💹' if var >= 0 else '📉'} {nome}: US$ {p_at:,.2f} ({var:+.2f}%)\n"

        msg += status_mercados_horarios()

        st.success("Relatório Gerado!")
        st.text_area("Texto formatado:", value=msg, height=300)
        
        link_zap = f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}"
        st.link_button("📲 ENVIAR PARA WHATSAPP", link_zap, use_container_width=True)
