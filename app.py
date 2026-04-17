import streamlit as st
import yfinance as yf
from datetime import datetime
import urllib.parse
import pytz
import pandas as pd
import requests
import streamlit.components.v1 as components

# Configuração da Página
st.set_page_config(page_title="Radar de Mercado", page_icon="📡", layout="wide")

# --- BANCO DE DADOS ---
projecoes = {"SELIC_2026": "12,50%", "SELIC_2027": "10,50%", "FED_PROJ_2026": "3,40%", "FED_PROJ_2027": "3,10%"}
lista_favoritas = ["BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "LINK-USD", "ALGO-USD", "SUI-USD"]

narrativas_config = {
    "IA": ["NEAR-USD", "FET-USD"],
    "RWA": ["LINK-USD", "ONDO-USD"],
    "WEB3/L1": ["ETH-USD", "SOL-USD"],
    "DEPIN": ["RENDER-USD", "HNT-USD"],
    "MEMES": ["DOGE-USD", "WIF-USD"]
}

# SEÇÃO DE SITES ORGANIZADA
links_uteis = {
    "📊 Análise & On-Chain": {
        "CoinMarketCap": "https://coinmarketcap.com",
        "DexScreener": "https://dexscreener.com",
        "Coinglass": "https://www.coinglass.com",
        "DefiLlama": "https://defillama.com",
        "DEXTools": "https://www.dextools.io"
    },
    "🐋 Monitoramento & Liquidez": {
        "Whale Alert (Grandes Carteiras)": "https://whale-alert.io",
        "Kingfisher (Liquidez BTC)": "https://thekingfisher.io",
        "TRDR.io (Orderflow)": "https://trdr.io",
        "Blockchain.com (Large Tx)": "https://www.blockchain.com/explorer/charts/utxo-count"
    },
    "📰 Notícias & Eventos": {
        "CryptoPanic": "https://cryptopanic.com",
        "Token Unlocks": "https://token.unlocks.app",
        "Investing": "https://br.investing.com"
    }
}

# --- FUNÇÕES DE APOIO ---
def format_vol(vol):
    try:
        if pd.isna(vol) or vol == 0: return "$---"
        if vol >= 1e9: return f"${vol/1e9:.1f}B"
        return f"${vol/1e6:.0f}M"
    except: return "$---"

def botao_copiar(label, texto_para_copiar, cor="#FF4B4B", key=None):
    id_html = f"btn_{key}" if key else label.lower().replace(" ", "_")
    # Escapa quebras de linha para o JavaScript não quebrar
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

# Menu principal em colunas para mobile/web
c_nav = st.columns(4)
btn_macro = c_nav[0].button('🏛️ MACRO', use_container_width=True)
btn_radar = c_nav[1].button('🎯 CRIPTO', use_container_width=True)
btn_unlock = c_nav[2].button('🔓 UNLOCKS', use_container_width=True)
btn_sites = c_nav[3].button('🔗 SITES', use_container_width=True)

# --- 1. RADAR CRIPTO (TEXTO LIMPO) ---
if btn_radar:
    with st.spinner('Limpando dados...'):
        ativos_todos = list(set(lista_favoritas + [item for sub in narrativas_config.values() for item in sub]))
        data = yf.download(ativos_todos, period="5d", interval="1d", progress=False)
        precos, volumes = data['Close'], data['Volume'].iloc[-1]
        agora = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
        
        # Montagem do texto sem excesso de asteriscos para o WhatsApp/Cópia
        msg = f"📡 RADAR CRIPTO & ECOSSISTEMAS\n🕒 {agora}\n\n"
        msg += "💎 FAVORITAS\n"
        
        for ticker in lista_favoritas:
            try:
                p = precos[ticker].iloc[-1]
                var = ((p / precos[ticker].iloc[-2]) - 1) * 100
                simbolo = ticker.replace('-USD','')
                emoji = "💹" if var >= 0 else "📉"
                msg += f"{emoji} {simbolo}: US$ {p:,.2f} ({var:+.2f}%)\n"
            except: continue

        msg += "\n🏆 NARRATIVAS (VOL 24H)"
        for narra, ativos in narrativas_config.items():
            msg += f"\n\n🔹 {narra}:"
            for ticker in ativos:
                try:
                    p = precos[ticker].iloc[-1]
                    v_t = ((p / precos[ticker].iloc[-2]) - 1) * 100
                    nome = ticker.replace('-USD','')
                    msg += f"\n {nome}: US$ {p:,.2f} ({v_t:+.2f}%) | Vol: {format_vol(volumes[ticker])}"
                except: continue
        
        st.text_area("Relatório pronto para envio:", msg, height=400)
        c1, c2 = st.columns(2)
        with c1: botao_copiar("Copiar Radar", msg, key="copy_clean")
        with c2: st.link_button("📲 Enviar WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

# --- 2. SITES (MOSTRAR TUDO DE UMA VEZ) ---
if btn_sites:
    st.markdown("---")
    st.markdown("<h2 style='text-align: center;'>🔗 Central de Ferramentas</h2>", unsafe_allow_html=True)
    
    for cat, sites in links_uteis.items():
        st.subheader(cat)
        cols = st.columns(2) # Divide em duas colunas para não ficar uma lista infinita
        for i, (nome, url) in enumerate(sites.items()):
            cols[i % 2].link_button(f"🔗 {nome}", url, use_container_width=True)
    st.markdown("---")

# --- BLOCO MACRO E UNLOCKS (Omitidos aqui para brevidade, mas mantidos no seu original) ---
if btn_macro:
    st.info("Função Macro carregando... (Use seu código original aqui)")

if btn_unlock:
    st.info("Função Unlocks carregando... (Use seu código original aqui)")

# --- APOIO ---
st.markdown("<h3 style='text-align: center;'>🚀 Apoie o Projeto</h3>", unsafe_allow_html=True)
col_p1, col_p2 = st.columns(2)
with col_p1:
    botao_copiar("Copiar PIX", "00020126580014BR.GOV.BCB.PIX0136841f1261-6e84-4132-9fcf-7e6eda71bb9e5204000053039865802BR5924Antonio Edinardo Pereira6009SAO PAULO62140510wgb2JUeYe963046375", cor="#00b5a4", key="p_pix")
with col_p2:
    botao_copiar("Copiar Binance ID", "511081814", cor="#F3BA2F", key="p_bin")
