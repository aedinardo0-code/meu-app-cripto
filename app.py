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
        serie_limpa = serie.dropna()
        if len(serie_limpa) < periodo: return 0, "Dados Insuficientes"
        delta = serie_limpa.diff()
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
    mercados_abertos = {}
    for m, (ab, fc, hr) in h.items():
        aberto = ab <= minutos < fc if ab < fc else minutos >= ab or minutos < fc
        txt += f"{m}: {'🟢 Aberto' if aberto else '🔴 Fechado'} ({hr})\n"
        mercados_abertos[m] = aberto
    return txt, mercados_abertos

# --- INTERFACE ---
st.title("📡 Radar de Mercado")
col1, col2 = st.columns(2)
with col1: btn_geral = st.button('🚀 RELATÓRIO GERAL', use_container_width=True)
with col2: btn_radar = st.button('🎯 RADAR CRIPTO', use_container_width=True)

# LISTAS DE ATIVOS
criptos_top = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD", "ADA-USD", "DOGE-USD", "LINK-USD", "ALGO-USD", "THETA-USD", "INJ-USD", "TIA-USD", "ARB-USD"]
macros = {"💵 Dólar": "USDBRL=X", "🛢️ Petróleo": "BZ=F", "📀 Ouro": "GC=F", "⚪ Prata": "SI=F", "🇧🇷 Ibovespa": "^BVSP", "⛽ Petrobras": "PETR4.SA", "💎 Vale": "VALE3.SA", "🏦 Itaú": "ITUB4.SA", "📈 Dow Jones": "YM=F", "🇺🇸 S&P 500": "ES=F", "💻 Nasdaq": "NQ=F"}

if btn_geral:
    with st.spinner('Validando dados em tempo real...'):
        dados = yf.download(criptos_top + list(macros.values()), period="30d", interval="1d", progress=False)['Close']
        agora_br = datetime.now(pytz.timezone('America/Sao_Paulo'))
        txt_horarios, status_map = status_mercados()
        
        rsi_v, rsi_s = calcular_rsi(dados["BTC-USD"])
        msg = f"📡 *PANORAMA GLOBAL & CRIPTO* \n🕒 {agora_br.strftime('%d/%m/%Y %H:%M')}\n\n📊 *Análise Técnica & Sentimento*\n📈 RSI Bitcoin (14D): {rsi_v:.2f} ({rsi_s})\n📉 Dominância BTC: {buscar_dominancia()}\n\n"
        
        msg += "🪙 *Mercado Cripto: Principais*\n"
        for c in ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD"]:
            p, var = dados[c].iloc[-1], ((dados[c].iloc[-1]/dados[c].iloc[-2])-1)*100
            msg += f"{'💹' if var>=0 else '📉'} {c.replace('-USD','')}: US$ {p:,.2f} ({var:+.2f}%)\n"
        
        variacoes = ((dados[criptos_top].iloc[-1] / dados[criptos_top].iloc[-2]) - 1) * 100
        msg += f"\n⬆️ *Top Performance*: {variacoes.idxmax().replace('-USD','')} ({variacoes.max():+.2f}%)\n"
        
        msg += "\n———————————————\n\n⚒️ *Macro, Bolsa & Commodities*\n"
        for nome, ticker in macros.items():
            # Verifica se é B3 e se o mercado está fechado
            es_b3 = any(x in ticker for x in [".SA", "^BVSP"])
            if es_b3 and not status_map["🇧🇷 B3"]:
                msg += f"{nome}: 🔴 FECHADO\n"
            else:
                p = dados[ticker].iloc[-1]
                var = ((dados[ticker].iloc[-1]/dados[ticker].iloc[-2])-1)*100
                if pd.isna(p) or p == dados[ticker].iloc[-2]: # Se o preço não mudou nada, mercado provavelmente parado
                     msg += f"{nome}: 🔴 FECHADO\n"
                else:
                    sufixo = "pts" if ticker in ["^BVSP", "YM=F", "ES=F", "NQ=F"] else ""
                    msg += f"{nome}: {p:,.2f}{sufixo} ({var:+.2f}%)\n"
            
        msg += txt_horarios
        st.text_area("Cópia:", msg, height=400)
        st.link_button("📲 ENVIAR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

if btn_radar:
    with st.spinner('Radar Cripto 24h...'):
        dados_c = yf.download(criptos_top, period="30d", progress=False)['Close']
        rsi_v, rsi_s = calcular_rsi(dados_c["BTC-USD"])
        msg_r = f"🎯 *RADAR CRIPTO*\n📈 RSI BTC: {rsi_v:.2f} ({rsi_s})\n\n"
        for c in ["BTC-USD", "ETH-USD", "SOL-USD", "ALGO-USD"]:
            p, var = dados_c[c].iloc[-1], ((dados_c[c].iloc[-1]/dados_c[c].iloc[-2])-1)*100
            msg_r += f"{'🟢' if var>=0 else '🔴'} {c.replace('-USD','')}: US$ {p:,.2f} ({var:+.2f}%)\n"
        st.info("Cripto funciona 24h - Dados sempre atuais.")
        st.text_area("Radar:", msg_r, height=200)
        st.link_button("📲 ENVIAR RADAR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_r)}", use_container_width=True)
