import streamlit as st
import yfinance as yf
from datetime import datetime
import urllib.parse
import pytz
import pandas as pd
import requests

st.set_page_config(page_title="Radar de Mercado", page_icon="📈")

# --- FUNÇÕES DE BUSCA ---
def buscar_dominancia():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        return f"{r['data']['market_cap_percentage']['btc']:.1f}%"
    except: return "57.2%"

def calcular_rsi(serie, periodo=14):
    try:
        delta = serie.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        status = "🔴 Sobrecompra" if val >= 70 else "🟢 Sobrevenda" if val <= 30 else "⚪ Neutro"
        return val, status
    except: return 0, "Erro"

def status_mercados():
    tz = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(tz)
    minutos = agora.hour * 60 + agora.minute
    dia = agora.weekday()
    txt = "\n🕒 *Status dos Mercados (Brasília)*\n"
    if dia >= 5: return txt + "🛑 Fim de semana: Mercados *FECHADOS*."
    h = {"🇧🇷 B3": (600, 1080, "10h-18h"), "🇺🇸 EUA": (600, 1020, "10h-17h"), "🏮 Ásia": (1260, 240, "21h-04h")}
    for m, (ab, fc, hr) in h.items():
        aberto = ab <= minutos < fc if ab < fc else minutos >= ab or minutos < fc
        txt += f"{m}: {'🟢 Aberto' if aberto else '🔴 Fechado'} ({hr})\n"
    return txt

# --- INTERFACE ---
st.title("📡 Radar de Mercado")
col1, col2 = st.columns(2)
with col1: btn_geral = st.button('🚀 RELATÓRIO GERAL', use_container_width=True)
with col2: btn_radar = st.button('🎯 RADAR CRIPTO', use_container_width=True)

# LISTAS DE ATIVOS
criptos_top = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD", "ADA-USD", "DOGE-USD", "LINK-USD", "ALGO-USD", "THETA-USD", "INJ-USD", "TIA-USD", "ARB-USD"]
macros = {"💵 Dólar": "USDBRL=X", "🛢️ Petróleo": "BZ=F", "📀 Ouro": "GC=F", "⚪ Prata": "SI=F", "🇧🇷 Ibovespa": "^BVSP", "⛽ Petrobras": "PETR4.SA", "💎 Vale": "VALE3.SA", "🏦 Itaú": "ITUB4.SA", "📈 Dow Jones": "YM=F", "🇺🇸 S&P 500": "ES=F", "💻 Nasdaq": "NQ=F"}

if btn_geral:
    with st.spinner('Gerando Panorama Completo...'):
        dados = yf.download(criptos_top + list(macros.values()), period="35d", interval="1d", progress=False)['Close']
        agora = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
        
        # 1. Cabeçalho e Técnica (Sem Fear & Greed)
        rsi_v, rsi_s = calcular_rsi(dados["BTC-USD"])
        msg = f"📡 *PANORAMA GLOBAL & CRIPTO* \n🕒 {agora}\n\n📊 *Análise Técnica & Sentimento*\n📈 RSI Bitcoin (14D): {rsi_v:.2f} ({rsi_s})\n📉 Dominância BTC: {buscar_dominancia()}\n\n"
        
        # 2. Mercado Cripto Principais
        msg += "🪙 *Mercado Cripto: Principais*\n"
        for c in ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD"]:
            p, var = dados[c].iloc[-1], ((dados[c].iloc[-1]/dados[c].iloc[-2])-1)*100
            msg += f"{'💹' if var>=0 else '📉'} {c.replace('-USD','')}: US$ {p:,.2f} ({var:+.2f}%)\n"
        
        # 3. Top Performances e Baixas
        variacoes = ((dados[criptos_top].iloc[-1] / dados[criptos_top].iloc[-2]) - 1) * 100
        top_altas = variacoes.nlargest(3)
        top_baixas = variacoes.nsmallest(3)
        
        msg += "\n⬆️ *Top 3 Performance (24h)*\n"
        for t, v in top_altas.items(): msg += f"🟩 {t.replace('-USD','')}: US$ {dados[t].iloc[-1]:,.4f} ({v:+.2f}%)\n"
        
        msg += "\n⬇️ *Top 3 Baixas (24h)*\n"
        for t, v in top_baixas.items(): msg += f"🟥 {t.replace('-USD','')}: US$ {dados[t].iloc[-1]:,.4f} ({v:+.2f}%)\n"
        
        # 4. Macro e Commodities
        msg += "\n———————————————\n\n⚒️ *Macro, Bolsa & Commodities*\n"
        for nome, ticker in macros.items():
            p, var = dados[ticker].iloc[-1], ((dados[ticker].iloc[-1]/dados[ticker].iloc[-2])-1)*100
            sufixo = "pts" if ticker in ["^BVSP", "YM=F", "ES=F", "NQ=F"] else ""
            msg += f"{nome}: {p:,.2f}{sufixo} ({var:+.2f}%)\n"
            
        msg += status_mercados()
        st.text_area("Cópia:", msg, height=400)
        st.link_button("📲 ENVIAR PARA WHATSAPP", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

if btn_radar:
    with st.spinner('Radar Rápido...'):
        dados_c = yf.download(["BTC-USD", "ETH-USD", "SOL-USD", "ALGO-USD"], period="35d", progress=False)['Close']
        rsi_v, rsi_s = calcular_rsi(dados_c["BTC-USD"])
        msg_r = f"🎯 *RADAR CRIPTO*\n📈 RSI BTC: {rsi_v:.2f} ({rsi_s})\n\n"
        for c in dados_c.columns:
            p, var = dados_c[c].iloc[-1], ((dados_c[c].iloc[-1]/dados_c[c].iloc[-2])-1)*100
            msg_r += f"{'🟢' if var>=0 else '🔴'} {c.replace('-USD','')}: US$ {p:,.2f} ({var:+.2f}%)\n"
        st.text_area("Radar:", msg_r, height=200)
        st.link_button("📲 ENVIAR RADAR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_r)}", use_container_width=True)
