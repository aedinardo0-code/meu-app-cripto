import streamlit as st
import yfinance as yf
from datetime import datetime
import urllib.parse
import pytz
import pandas as pd
import requests

st.set_page_config(page_title="Radar de Mercado", page_icon="📈")

# --- FUNÇÕES DE APOIO ---
def buscar_dominancia():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        return f"{r['data']['market_cap_percentage']['btc']:.1f}%"
    except: return "57.1%"

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

def format_vol(vol):
    if vol >= 1e9: return f"${vol/1e9:.1f}B"
    return f"${vol/1e6:.0f}M"

# --- INTERFACE ---
st.title("📡 Radar de Mercado")
col1, col2 = st.columns(2)
with col1: btn_geral = st.button('🚀 RELATÓRIO GERAL', use_container_width=True)
with col2: btn_radar = st.button('🎯 RADAR CRIPTO', use_container_width=True)

# LISTAS DE ATIVOS
macros = {
    "💵 Dólar": "USDBRL=X", "🛢️ Petróleo": "BZ=F", "📀 Ouro": "GC=F", "⚪ Prata": "SI=F",
    "🇧🇷 Ibovespa": "^BVSP", "⛽ Petrobras": "PETR4.SA", "💎 Vale": "VALE3.SA", 
    "🏦 Itaú": "ITUB4.SA", "📈 Dow Jones": "YM=F", "🇺🇸 S&P 500": "ES=F", "💻 Nasdaq": "NQ=F"
}

narrativas = {
    "🤖 IA": ["NEAR-USD", "FET-USD"],
    "🏢 RWA": ["LINK-USD", "ONDO-USD"],
    "🌐 Web3/L1": ["ETH-USD", "SOL-USD"],
    "🤡 Memes": ["DOGE-USD", "WIF-USD"]
}

todas_criptos = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD", "ALGO-USD", "TIA-USD", "OP-USD", "ADA-USD", "TRX-USD"] + [a for sub in narrativas.values() for a in sub]

# --- LÓGICA BOTÃO 1 ---
if btn_geral:
    with st.spinner('Gerando Panorama Global...'):
        dados = yf.download(list(macros.values()) + ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD"], period="5d", interval="1d", progress=False)['Close']
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        
        msg = f"📡 *PANORAMA GLOBAL \n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        msg += "🪙 *Mercado Cripto: Principais*\n"
        for c in ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD"]:
            p, var = dados[c].iloc[-1], ((dados[c].iloc[-1]/dados[c].iloc[-2])-1)*100
            msg += f"{'💹' if var>=0 else '📉'} {c.replace('-USD','')}: US$ {p:,.2f} ({var:+.2f}%)\n"
        
        msg += "\n⚒️ *Macro\n"
        for nome, ticker in macros.items():
            p = dados[ticker].iloc[-1]
            if pd.isna(p):
                msg += f"{nome}: 🔴 Fechado\n"
            else:
                var = ((dados[ticker].iloc[-1]/dados[ticker].iloc[-2])-1)*100
                sufixo = "pts" if any(x in ticker for x in ["^", "=F"]) else ""
                msg += f"{nome}: {p:,.2f}{sufixo} ({var:+.2f}%)\n"
        
        st.text_area("Cópia:", msg, height=400)
        st.link_button("📲 ENVIAR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}")

# --- LÓGICA BOTÃO 2 ---
if btn_radar:
    with st.spinner('Mapeando Ecossistemas...'):
        data = yf.download(todas_criptos, period="14d", interval="1d", progress=False)
        precos = data['Close']
        volumes = data['Volume'].iloc[-1]
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        
        rsi_v, rsi_s = calcular_rsi(precos["BTC-USD"])
        btc_p, btc_var = precos["BTC-USD"].iloc[-1], ((precos["BTC-USD"].iloc[-1]/precos["BTC-USD"].iloc[-2])-1)*100
        
        msg = f"📡 *PANORAMA CRIPTO & ECOSSISTEMAS* \n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        msg += f"📊 *Bitcoin:* US$ {btc_p:,.2f}\n🧭 Tendência: {'💹 Alta' if btc_var > 0 else '📉 Baixa'}\n📈 RSI BTC: {rsi_v:.2f} ({rsi_s})\nDominância 🍕 {buscar_dominancia()}\n\n"
        
        msg += "⭐ *Minhas Favoritas*\n"
        for fav, tk in [("Algorand", "ALGO-USD"), ("Avax", "AVAX-USD"), ("XRP", "XRP-USD")]:
            msg += f"💎 {fav}: US$ {precos[tk].iloc[-1]:,.4f}\n"
            
        msg += "\n🏆 *Ranking de Narrativas (Volume)*"
        for narra, ativos in narrativas.items():
            msg += f"\n{narra}:"
            for i, t in enumerate(ativos, 1):
                p, var = precos[t].iloc[-1], ((precos[t].iloc[-1]/precos[t].iloc[-2])-1)*100
                emoji = " ⚡" if var >= 3.0 else ""
                msg += f"\n {i}º {t.replace('-USD','')}: ${p:,.3f} ({var:+.2f}%){emoji}\n    ∟ Vol: {format_vol(volumes[t])}"
        
        variacoes = ((precos.iloc[-1] / precos.iloc[-2]) - 1) * 100
        msg += f"\n\n🚀 *Top 3 Altas* ⚡"
        for t, v in variacoes.nlargest(3).items(): msg += f"\n🟩 {t.replace('-USD','')}: {v:+.2f}% ⚡"
        
        msg += f"\n\n⚠️ *Top 3 Baixas"
        for t, v in variacoes.nsmallest(3).items(): msg += f"\n🟥 {t.replace('-USD','')}: {v:+.2f}% 🪫"

        st.text_area("Cópia Radar:", msg, height=500)
        st.link_button("📲 ENVIAR RADAR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}")
