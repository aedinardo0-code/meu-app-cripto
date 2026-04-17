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

# --- BANCO DE DADOS (DADOS REAIS E CONFIGURAÇÕES) ---
# Atualize estes valores manualmente quando houver novas reuniões do COPOM ou FED
projecoes = {
    "SELIC_2026": "12,50%", "SELIC_2027": "10,50%",
    "FED_PROJ_2026": "3,40%", "FED_PROJ_2027": "3,10%"
}

# Lista de Favoritas Atualizada (100% Real via Yahoo Finance)
lista_favoritas = [
    "BTC-USD", "ETH-USD", "XRP-USD", "XLM-USD", "SOL-USD", 
    "AVAX-USD", "LINK-USD", "ALGO-USD", "SUI-USD",
    "BNB-USD", "POL-USD", "ADA-USD"
]

# Narrativas com Emojis Temáticos
narrativas_config = {
    "🤖 IA": ["NEAR-USD", "FET-USD"],
    "🏢 RWA": ["LINK-USD", "ONDO-USD"],
    "🌐 WEB3/L1": ["ETH-USD", "SOL-USD"],
    "📡 DEPIN": ["RENDER-USD", "HNT-USD"],
    "🤡 MEMES": ["DOGE-USD", "WIF-USD"]
}

# Tickers do Mercado Tradicional (Macro)
macros_tickers = {
    "🌍 DXY": "DX-Y.NYB", "🏦 Treasury 10Y": "^TNX", "😱 VIX": "^VIX",
    "📈 Dow Jones": "YM=F", "🇺🇸 S&P 500": "ES=F", "💻 Nasdaq": "NQ=F",
    "🇧🇷 Ibovespa": "^BVSP", "💵 Dólar Comercial": "USDBRL=X",
    "🛢️ Brent": "BZ=F", "📀 Ouro": "GC=F", "⛽ PETR4": "PETR4.SA", "💎 VALE3": "VALE3.SA"
}

# Central de Links Úteis
links_uteis = {
    "🔥 Liquidez & Gráficos": {
        "CoinMarketCap": "https://coinmarketcap.com",
        "CoinGecko": "https://www.coingecko.com",
        "Mapa de Liquidação (Coinglass)": "https://www.coinglass.com/pt/pro/futures/LiquidationHeatMap",
        "Crypto Bubbles (Bolinhas)": "https://cryptobubbles.net",
        "Preços TradingView": "https://br.tradingview.com/markets/cryptocurrencies/prices-all/",
        "DexScreener": "https://dexscreener.com",
        "DefiLlama": "https://defillama.com"
    },
    "🐋 On-Chain & Unlocks": {
        "Whale Alert (Baleias)": "https://whale-alert.io",
        "Token Unlocks (Oficial)": "https://token.unlocks.app",
        "DEXTools": "https://www.dextools.io"
    },
    "📰 Notícias Brasil": {
        "LiveCoins": "https://livecoins.com.br",
        "Portal do Bitcoin": "https://portaldobitcoin.uol.com.br"
    }
}

# --- FUNÇÕES DE APOIO ---
def buscar_dominancias():
    """Busca dominância real via API pública da CoinGecko"""
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        btc = f"{r['data']['market_cap_percentage']['btc']:.1f}%"
        eth = f"{r['data']['market_cap_percentage']['eth']:.1f}%"
        return btc, eth
    except:
        return "N/A", "N/A"

def format_vol(vol):
    """Formata volumes grandes para leitura humana"""
    try:
        if pd.isna(vol) or vol == 0: return "$---"
        if vol >= 1e9: return f"${vol/1e9:.1f}B"
        return f"${vol/1e6:.0f}M"
    except:
        return "$---"

def botao_copiar(label, texto_para_copiar, cor="#FF4B4B", key=None):
    """Componente HTML/JS para copiar texto para o clipboard"""
    id_html = f"btn_{key}" if key else label.lower().replace(" ", "_")
    texto_js = texto_para_copiar.replace("\n", "\\n").replace("'", "\\'")
    html_code = f"""
    <div style="margin-bottom: 10px;">
        <button id="{id_html}" style="width: 100%; background-color: {cor}; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px;">
            📋 {label}
        </button>
    </div>
    <script>
    document.getElementById('{id_html}').addEventListener('click', function() {{
        const text = '{texto_js}';
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

# --- INTERFACE PRINCIPAL ---
st.markdown("<h1 style='text-align: center;'>📡 Radar de Mercado</h1>", unsafe_allow_html=True)

# Barra de Navegação (4 Colunas)
c_nav = st.columns(4)
btn_macro = c_nav[0].button('🏛️ MACRO', use_container_width=True)
btn_radar = c_nav[1].button('🎯 CRIPTO', use_container_width=True)
# Botão Unlocks transformado em Link Direto
c_nav[2].link_button('🔓 UNLOCKS', "https://token.unlocks.app", use_container_width=True)
btn_sites = c_nav[3].button('🔗 SITES', use_container_width=True)

# --- 1. LÓGICA DA SEÇÃO MACRO ---
if btn_macro:
    with st.spinner('Lendo indicadores globais...'):
        dados = yf.download(list(macros_tickers.values()), period="5d", interval="1d", progress=False)['Close']
        agora = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
        
        msg = f"📡 PANORAMA MACRO GLOBAL\n🕒 {agora}\n\n"
        for nome, ticker in macros_tickers.items():
            try:
                p = dados[ticker].iloc[-1]
                v_ant = dados[ticker].iloc[-2]
                var = ((p / v_ant) - 1) * 100
                msg += f"{'💹' if var>=0 else '📉'} {nome}: {p:,.2f} ({var:+.2f}%)\n"
                
                # Inserir projeções específicas abaixo do Nasdaq
                if "Nasdaq" in nome:
                    msg += f"🏛️ Projeção FED: 2026: {projecoes['FED_PROJ_2026']} | 2027: {projecoes['FED_PROJ_2027']}\n"
            except: continue
            
        msg += f"\n🏛️ Projeção SELIC: 2026: {projecoes['SELIC_2026']} | 2027: {projecoes['SELIC_2027']}"
        
        st.text_area("Relatório Macro:", msg, height=350)
        botao_copiar("Copiar Macro", msg, key="m_cp")

# --- 2. LÓGICA DA SEÇÃO CRIPTO ---
if btn_radar:
    with st.spinner('Sincronizando Mercado Real...'):
        ativos_todos = list(set(lista_favoritas + [item for sub in narrativas_config.values() for item in sub]))
        data = yf.download(ativos_todos, period="5d", interval="1d", progress=False)
        precos, volumes = data['Close'], data['Volume']
        dom_btc, dom_eth = buscar_dominancias()
        agora = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
        
        msg = f"📡 RADAR CRIPTO & ECOSSISTEMAS\n🕒 {agora}\n\n"
        msg += "💎 FAVORITAS\n"
        
        for ticker in lista_favoritas:
            try:
                p = precos[ticker].iloc[-1]
                v_ant = precos[ticker].iloc[-2]
                if pd.isna(p): continue
                var = ((p / v_ant) - 1) * 100 if not pd.isna(v_ant) else 0.0
                simb = ticker.split('-')[0]
                
                msg += f"{'💹' if var>=0 else '📉'} {simb}: US$ {p:,.2f} ({var:+.2f}%)\n"
                if simb == "BTC": msg += f"  ∟ Dominância: {dom_btc}\n"
                if simb == "ETH": msg += f"  ∟ Dominância: {dom_eth}\n"
            except: continue

        msg += "\n🏆 NARRATIVAS (VOLUME 24H)"
        for narra, ativos in narrativas_config.items():
            msg += f"\n\n{narra}:"
            for t in ativos:
                try:
                    p = precos[t].iloc[-1]
                    v_ant = precos[t].iloc[-2]
                    if pd.isna(p): continue
                    var_t = ((p / v_ant) - 1) * 100 if not pd.isna(v_ant) else 0.0
                    vol_val = volumes[t].iloc[-1]
                    msg += f"\n {t.split('-')[0]}: US$ {p:,.2f} ({var_t:+.2f}%) | Vol: {format_vol(vol_val)}"
                except: continue
        
        st.text_area("Texto Limpo:", msg, height=450)
        c1, c2 = st.columns(2)
        with c1: botao_copiar("Copiar Radar", msg, key="c_cp")
        with c2: st.link_button("📲 WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

# --- 3. LÓGICA DA SEÇÃO SITES ---
if btn_sites:
    st.markdown("---")
    st.markdown("<h2 style='text-align: center;'>🔗 Central de Ferramentas</h2>", unsafe_allow_html=True)
    for cat, sites in links_uteis.items():
        st.subheader(cat)
        cols = st.columns(2)
        for i, (nome, url) in enumerate(sites.items()):
            cols[i % 2].link_button(nome, url, use_container_width=True)

# --- RODAPÉ / APOIO ---
st.markdown("---")
st.markdown("<h3 style='text-align: center;'>🚀 Apoie o Projeto</h3>", unsafe_allow_html=True)
cp1, cp2 = st.columns(2)
with cp1: botao_copiar("Copiar PIX", "00020126580014BR.GOV.BCB.PIX0136841f1261-6e84-4132-9fcf-7e6eda71bb9e5204000053039865802BR5924Antonio Edinardo Pereira6009SAO PAULO62140510wgb2JUeYe963046375", "#00b5a4", "px")
with cp2: botao_copiar("Binance ID", "511081814", "#F3BA2F", "bid")
