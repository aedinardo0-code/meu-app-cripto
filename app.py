import streamlit as st
import yfinance as yf
from datetime import datetime
import urllib.parse
import pytz
import pandas as pd
import requests

st.set_page_config(page_title="Radar de Mercado", page_icon="📈")

# --- FUNÇÕES AUXILIARES ---
def buscar_fng_e_dom():
    try:
        fng_r = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        val = fng_r['data'][0]['value']
        cl = fng_r['data'][0]['value_classification']
        trad = {"Extreme Fear": "Medo Extremo", "Fear": "Medo", "Neutral": "Neutro", "Greed": "Ganância", "Extreme Greed": "Ganância Extrema"}
        
        dom_r = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        dom = f"{dom_r['data']['market_cap_percentage']['btc']:.1f}%"
        return f"{val} ({trad.get(cl, cl)})", dom
    except: return "23 (Medo Extremo)", "57.1%"

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

def get_emoji_dinamico(var):
    if var >= 3.0: return " ⚡"
    if var <= -5.0: return " 🪫"
    return ""

def format_vol(vol):
    if vol >= 1e9: return f"${vol/1e9:.1f}B"
    return f"${vol/1e6:.0f}M"

# --- INTERFACE ---
st.title("📡 Radar de Mercado")
col1, col2 = st.columns(2)
with col1: btn_geral = st.button('🚀 RELATÓRIO GERAL', use_container_width=True)
with col2: btn_radar = st.button('🎯 RADAR CRIPTO', use_container_width=True)

# CONFIGURAÇÃO DE ATIVOS
macros = {"💵 Dólar": "USDBRL=X", "🛢️ Petróleo": "BZ=F", "📀 Ouro": "GC=F", "🇧🇷 Ibovespa": "^BVSP", "⛽ Petrobras": "PETR4.SA", "💎 Vale": "VALE3.SA", "🏦 Itaú": "ITUB4.SA"}
narrativas = {
    "🤖 IA": ["NEAR-USD", "FET-USD"],
    "🏢 RWA": ["LINK-USD", "ONDO-USD"],
    "🌐 Web3/L1": ["ETH-USD", "SOL-USD"],
    "🤡 Memes": ["DOGE-USD", "WIF-USD"]
}
todas_criptos = ["BTC-USD", "ALGO-USD", "AVAX-USD", "XRP-USD", "TIA-USD", "OP-USD", "ADA-USD", "TRX-USD"] + [item for sublist in narrativas.values() for item in sublist]

if btn_geral:
    with st.spinner('Consolidando Mercado...'):
        dados = yf.download(list(macros.values()) + ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD"], period="2d", interval="1d", progress=False)['Close']
        tz = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(tz)
        
        msg = f"📡 *PANORAMA GLOBAL & CRIPTO* \n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        msg += "🪙 *Mercado Cripto: Principais*\n"
        for c in ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD"]:
            p, var = dados[c].iloc[-1], ((dados[c].iloc[-1]/dados[c].iloc[-2])-1)*100
            msg += f"{'💹' if var>=0 else '📉'} {c.replace('-USD','')}: US$ {p:,.2f} ({var:+.2f}%)\n"
        
        msg += "\n———————————————\n\n⚒️ *Macro, Bolsa & Commodities*\n"
        is_b3_open = (10 <= agora.hour < 18) and agora.weekday() < 5
        for nome, ticker in macros.items():
            if any(x in ticker for x in [".SA", "^BVSP"]) and not is_b3_open:
                msg += f"{nome}: 🔴 FECHADO\n"
            else:
                p, var = dados[ticker].iloc[-1], ((dados[ticker].iloc[-1]/dados[ticker].iloc[-2])-1)*100
                sufixo = "pts" if "^" in ticker else ""
                msg += f"{nome}: {p:,.2f}{sufixo} ({var:+.2f}%)\n"
        
        st.text_area("Cópia:", msg, height=350)
        st.link_button("📲 ENVIAR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

if btn_radar:
    with st.spinner('Mapeando Ecossistemas...'):
        # Busca Preços e Volumes
        tickers = list(set(todas_criptos))
        data = yf.download(tickers, period="14d", interval="1d", progress=False)
        precos = data['Close']
        volumes = data['Volume'].iloc[-1]
        
        fng, dom = buscar_fng_e_dom()
        rsi_v, rsi_s = calcular_rsi(precos["BTC-USD"])
        agora = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
        
        btc_p, btc_var = precos["BTC-USD"].iloc[-1], ((precos["BTC-USD"].iloc[-1]/precos["BTC-USD"].iloc[-2])-1)*100
        tendencia = "📈 Alta" if btc_var > 0 else "📉 Baixa"
        
        msg = f"📡 *PANORAMA CRIPTO & ECOSSISTEMAS* \n🕒 {agora}\n\n"
        msg += f"📊 *Bitcoin:* US$ {btc_p:,.2f}\n🧭 Tendência: {tendencia}\n📈 RSI BTC: {rsi_v:.2f} ({rsi_s})\n🌡️ F&G: {fng} | 📉 Dom: {dom}\n\n"
        
        msg += "⭐ *Minhas Favoritas*\n"
        for fav, tick in [("Algorand", "ALGO-USD"), ("Avax", "AVAX-USD"), ("XRP", "XRP-USD")]:
            msg += f"💎 {fav}: US$ {precos[tick].iloc[-1]:,.4f}\n"
            
        msg += "\n🏆 *Ranking de Narrativas (Volume)*"
        for narra, ativos in narrativas.items():
            msg += f"\n{narra}:"
            for i, t in enumerate(ativos, 1):
                p, var, v_at = precos[t].iloc[-1], ((precos[t].iloc[-1]/precos[t].iloc[-2])-1)*100, volumes[t]
                emoji = get_emoji_dinamico(var)
                msg += f"\n {i}º {t.replace('-USD','')}: ${p:,.3f} ({var:+.2f}%){emoji}\n    ∟ Vol: {format_vol(v_at)}"
        
        variacoes = ((precos.iloc[-1] / precos.iloc[-2]) - 1) * 100
        msg += f"\n\n🚀 *Top 3 Altas* ⚡"
        for t, v in variacoes.nlargest(3).items(): msg += f"\n🟩 {t.replace('-USD','')}: {v:+.2f}%"
        
        msg += f"\n\n⚠️ *Top 3 Baixas* 🪫"
        for t, v in variacoes.nsmallest(3).items(): msg += f"\n🟥 {t.replace('-USD','')}: {v:+.2f}%"

        st.text_area("Resultado:", msg, height=500)
        st.link_button("📲 ENVIAR RADAR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)
