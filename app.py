import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import urllib.parse
import pytz
import pandas as pd
import streamlit.components.v1 as components

# Configuração da Página
st.set_page_config(page_title="Radar de Mercado", page_icon="📡", layout="wide")

# --- BANCO DE DADOS ATUALIZADO ---
lista_favoritas = ["BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "LINK-USD", "ALGO-USD", "SUI-USD"]

narrativas_config = {
    "IA": ["NEAR-USD", "FET-USD"],
    "RWA": ["LINK-USD", "ONDO-USD"],
    "WEB3/L1": ["ETH-USD", "SOL-USD"],
    "DEPIN": ["RENDER-USD", "HNT-USD"],
    "MEMES": ["DOGE-USD", "WIF-USD"]
}

# --- SEÇÃO DE SITES (REFORMULADA) ---
links_uteis = {
    "📊 Análise & Liquidez": {
        "Mapa de Liquidação (Coinglass)": "https://www.coinglass.com/pt/pro/futures/LiquidationHeatMap",
        "CryptoBubbles (Bolinhas)": "https://cryptobubbles.net",
        "Preços em Tempo Real (TradingView)": "https://br.tradingview.com/markets/cryptocurrencies/prices-all/",
        "DexScreener": "https://dexscreener.com",
        "DefiLlama": "https://defillama.com"
    },
    "🐋 Monitoramento": {
        "Whale Alert (Baleias)": "https://whale-alert.io",
        "Token Unlocks (Oficial)": "https://token.unlocks.app"
    },
    "📰 Notícias Brasil": {
        "LiveCoins": "https://livecoins.com.br",
        "Portal do Bitcoin": "https://portaldobitcoin.uol.com.br",
        "CoinTelegraph Brasil": "https://br.cointelegraph.com"
    }
}

# --- UNLOCKS PRÓXIMOS 60 DIAS (MANUAL) ---
# Dados projetados para 2026 baseados em cronogramas de emissão
dados_unlocks = [
    {"moeda": "SOL", "data": "22/04/2026", "valor": "$230M", "tipo": "Stake Rewards"},
    {"moeda": "ARB", "data": "16/05/2026", "valor": "$65M", "tipo": "Team/Investors"},
    {"moeda": "STRK", "data": "15/05/2026", "valor": "$32M", "tipo": "Ecosystem"},
    {"moeda": "SUI", "data": "03/05/2026", "valor": "$105M", "tipo": "Series A/B"},
    {"moeda": "OP", "data": "30/05/2026", "valor": "$54M", "tipo": "Core Contrib"},
    {"moeda": "IMX", "data": "12/05/2026", "valor": "$48M", "tipo": "Ecosystem"}
]

# --- FUNÇÕES ---
def format_vol(vol):
    try:
        if pd.isna(vol) or vol == 0: return "$---"
        if vol >= 1e9: return f"${vol/1e9:.1f}B"
        return f"${vol/1e6:.0f}M"
    except: return "$---"

def botao_copiar(label, texto_para_copiar, cor="#FF4B4B", key=None):
    id_html = f"btn_{key}" if key else label.lower().replace(" ", "_")
    texto_limpo = texto_para_copiar.replace("\n", "\\n").replace("'", "\\'")
    html_code = f"""
    <div style="margin-bottom: 10px;">
        <button id="{id_html}" style="width: 100%; background-color: {cor}; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px;">
            📋 {label}
        </button>
    </div>
    <script>
    document.getElementById('{id_html}').addEventListener('click', function() {{
        const text = '{texto_limpo}';
        const el = document.createElement('textarea');
        el.value = text; document.body.appendChild(el);
        el.select(); document.execCommand('copy');
        document.body.removeChild(el);
        const btn = document.getElementById('{id_html}');
        btn.innerText = '✅ COPIADO!'; btn.style.backgroundColor = '#28a745';
        setTimeout(function() {{ btn.innerText = '📋 {label}'; btn.style.backgroundColor = '{cor}'; }}, 2000);
    }});
    </script>
    """
    return components.html(html_code, height=70)

# --- INTERFACE ---
st.markdown("<h1 style='text-align: center;'>📡 Radar de Mercado</h1>", unsafe_allow_html=True)

c_nav = st.columns(4)
btn_macro = c_nav[0].button('🏛️ MACRO', use_container_width=True)
btn_radar = c_nav[1].button('🎯 CRIPTO', use_container_width=True)
btn_unlock = c_nav[2].button('🔓 UNLOCKS', use_container_width=True)
btn_sites = c_nav[3].button('🔗 SITES', use_container_width=True)

# --- LÓGICA DO RADAR CRIPTO ---
if btn_radar:
    with st.spinner('Sincronizando...'):
        ativos_todos = list(set(lista_favoritas + [item for sub in narrativas_config.values() for item in sub]))
        data = yf.download(ativos_todos, period="5d", interval="1d", progress=False)
        precos, volumes = data['Close'], data['Volume'].iloc[-1]
        agora = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
        
        msg = f"📡 RADAR CRIPTO & ECOSSISTEMAS\n🕒 {agora}\n\n"
        msg += "💎 FAVORITAS\n"
        for ticker in lista_favoritas:
            try:
                p = precos[ticker].iloc[-1]
                v = ((p / precos[ticker].iloc[-2]) - 1) * 100
                simb = ticker.split('-')[0]
                emoji = "💹" if v >= 0 else "📉"
                msg += f"{emoji} {simb}: US$ {p:,.2f} ({v:+.2f}%)\n"
            except: continue

        msg += "\n🏆 NARRATIVAS (VOL 24H)"
        for narra, ativos in narrativas_config.items():
            msg += f"\n\n🔹 {narra}:"
            for t in ativos:
                try:
                    p = precos[t].iloc[-1]
                    var_t = ((p / precos[t].iloc[-2]) - 1) * 100
                    msg += f"\n {t.split('-')[0]}: US$ {p:,.2f} ({var_t:+.2f}%) | Vol: {format_vol(volumes[t])}"
                except: continue
        
        st.text_area("Texto Limpo:", msg, height=400)
        c1, c2 = st.columns(2)
        with c1: botao_copiar("Copiar Radar", msg, key="c_clean")
        with c2: st.link_button("📲 WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

# --- LÓGICA DO UNLOCKS (MANUAL) ---
if btn_unlock:
    agora = datetime.now().strftime('%d/%m/%Y')
    msg = f"🔓 RADAR DE DESBLOQUEIOS (60 DIAS)\n🕒 Ref: {agora}\n\n"
    for item in dados_unlocks:
        msg += f"📅 {item['moeda']}: {item['data']} | Val: {item['valor']} ({item['tipo']})\n"
    
    st.markdown("### 🔓 Próximos Desbloqueios")
    st.text_area("Texto Unlocks:", msg, height=250)
    botao_copiar("Copiar Desbloqueios", msg, key="u_copy")

# --- LÓGICA DO SITES (SISTEMA DE BOTÕES) ---
if btn_sites:
    st.markdown("---")
    st.markdown("<h2 style='text-align: center;'>🔗 Central de Ferramentas</h2>", unsafe_allow_html=True)
    for cat, sites in links_uteis.items():
        st.subheader(cat)
        cols = st.columns(2)
        for i, (nome, url) in enumerate(sites.items()):
            cols[i % 2].link_button(nome, url, use_container_width=True)

# --- APOIO ---
st.markdown("---")
st.markdown("<h3 style='text-align: center;'>🚀 Apoie o Radar</h3>", unsafe_allow_html=True)
c_pix1, c_pix2 = st.columns(2)
with c_pix1: botao_copiar("Copiar PIX", "00020126580014BR.GOV.BCB.PIX0136841f1261-6e84-4132-9fcf-7e6eda71bb9e5204000053039865802BR5924Antonio Edinardo Pereira6009SAO PAULO62140510wgb2JUeYe963046375", "#00b5a4", "p1")
with c_pix2: botao_copiar("Copiar Binance ID", "511081814", "#F3BA2F", "p2")
