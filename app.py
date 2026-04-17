import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import urllib.parse
import pytz
import pandas as pd
import requests
import streamlit.components.v1 as components

# Configuração da Página
st.set_page_config(page_title="Radar de Mercado", page_icon="📡", layout="wide")

# --- BANCO DE DADOS DE PROJEÇÕES ---
projecoes = {
    "SELIC_2026": "12,50%",
    "SELIC_2027": "10,50%",
    "FED_PROJ_2026": "3,40%",
    "FED_PROJ_2027": "3,10%"
}

# --- FUNÇÕES DE APOIO ---
def buscar_dominancia():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        return f"{r['data']['market_cap_percentage']['btc']:.1f}%"
    except: return "57.2%"

def format_vol(vol):
    try:
        if pd.isna(vol) or vol == 0: return "$---"
        if vol >= 1e9: return f"${vol/1e9:.1f}B"
        return f"${vol/1e6:.0f}M"
    except: return "$---"

def botao_copiar(label, texto_para_copiar, cor="#FF4B4B"):
    id_html = label.lower().replace(" ", "_")
    html_code = f"""
    <div style="margin-bottom: 10px;">
        <button id="btn_{id_html}" style="width: 100%; background-color: {cor}; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; transition: 0.3s;">
            📋 {label}
        </button>
    </div>
    <script>
    document.getElementById('btn_{id_html}').addEventListener('click', function() {{
        const text = `{texto_para_copiar}`;
        const el = document.createElement('textarea');
        el.value = text;
        document.body.appendChild(el);
        el.select();
        document.execCommand('copy');
        document.body.removeChild(el);
        const btn = document.getElementById('btn_{id_html}');
        const originalText = btn.innerText;
        btn.innerText = '✅ COPIADO!';
        btn.style.backgroundColor = '#28a745';
        setTimeout(function() {{ btn.innerText = originalText; btn.style.backgroundColor = '{cor}'; }}, 2000);
    }});
    </script>
    """
    return components.html(html_code, height=70)

# --- CONFIGURAÇÕES DE ATIVOS ---
macros_tickers = {
    "🌍 DXY": "DX-Y.NYB", "🏦 Treasury 10Y": "^TNX", "😱 VIX": "^VIX",
    "📈 Dow Jones": "YM=F", "🇺🇸 S&P 500": "ES=F", "💻 Nasdaq": "NQ=F",
    "🇧🇷 Ibovespa": "^BVSP", "💵 Dólar Comercial": "USDBRL=X",
    "🛢️ Brent": "BZ=F", "📀 Ouro": "GC=F", "⛽ PETR4": "PETR4.SA", "💎 VALE3": "VALE3.SA"
}

narrativas_config = {
    "🤖 IA": ["NEAR-USD", "FET-USD"],
    "🏢 RWA": ["LINK-USD", "ONDO-USD"],
    "🌐 Web3/L1": ["ETH-USD", "SOL-USD"],
    "📡 DePIN": ["RENDER-USD", "HNT-USD"],
    "🤡 Memes": ["DOGE-USD", "WIF-USD"]
}

# Lista estática das 100 maiores para garantir o Top 3 Global
top_100_tickers = [
    "BTC-USD", "ETH-USD", "USDT-USD", "BNB-USD", "SOL-USD", "XRP-USD", "USDC-USD", "ADA-USD", "STETH-USD", "AVAX-USD",
    "DOGE-USD", "SHIB-USD", "DOT-USD", "LINK-USD", "TRX-USD", "MATIC-USD", "WBTC-USD", "NEAR-USD", "UNI-USD", "LTC-USD",
    "DAI-USD", "ICP-USD", "PEPE-USD", "BCH-USD", "ETC-USD", "RENDER-USD", "FIL-USD", "OKB-USD", "ARB-USD", "APT-USD",
    "HBAR-USD", "IMX-USD", "WHBAR-USD", "KAS-USD", "STX-USD", "OP-USD", "TIA-USD", "GRT-USD", "THETA-USD", "FET-USD",
    "ONDO-USD", "WIF-USD", "FLOKI-USD", "HNT-USD", "BONK-USD", "SUI-USD", "AAVE-USD", "GALA-USD", "LDO-USD", "CORE-USD"
    # Adicione mais conforme desejar para completar as 100
]

links_uteis = {
    "📰 Notícias Cripto": {
        "Portal do Bitcoin (BR)": "https://portaldobitcoin.uol.com.br/",
        "Livecoins (BR)": "https://livecoins.com.br/",
        "CoinTelegraph (Global)": "https://cointelegraph.com/"
    },
    "📊 Ferramentas de Análise": {
        "CME FedWatch (Juros EUA)": "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html",
        "CryptoBubbles (Visualização)": "https://cryptobubbles.net/",
        "CoinGlass (Liquidez & Liquidações)": "https://www.coinglass.com/pt",
        "DefiLlama (Dados DeFi/RWA)": "https://defillama.com/",
        "Kingfisher (Mapas de Liquidez)": "https://thekingfisher.io/"
    },
    "💰 Preços e Liquidez": {
        "CoinMarketCap": "https://coinmarketcap.com/",
        "DexScreener (Moedas Novas)": "https://dexscreener.com/",
        "Whale Alert (Baleias)": "https://whale-alert.io/"
    }
}

# --- INTERFACE ---
st.title("📡 Radar de Mercado")
c1, c2, c3, c4 = st.columns(4)
with c1: btn_macro = st.button('🏛️ MACRO', use_container_width=True)
with c2: btn_radar = st.button('🎯 CRIPTO', use_container_width=True)
with c3: btn_unlock = st.button('🔓 UNLOCKS', use_container_width=True)
with c4: btn_sites = st.button('🔗 SITES', use_container_width=True)

# --- BOTÃO 1: MACRO ---
if btn_macro:
    with st.spinner('Acessando dados globais...'):
        dados = yf.download(list(macros_tickers.values()), period="5d", interval="1d", progress=False)['Close']
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        msg = f"📡 *PANORAMA MACRO GLOBAL*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        msg += "🇺🇸 *MERCADO EUA & JUROS*\n"
        for nome, ticker in list(macros_tickers.items())[:6]:
            p = dados[ticker].iloc[-1]
            var = ((p/dados[ticker].iloc[-2])-1)*100
            msg += f"{'💹' if var>=0 else '📉'} {nome}: {p:,.2f} ({var:+.2f}%)\n"
        msg += f"🏛️ Projeção FED (Dot Plot): 2026: {projecoes['FED_PROJ_2026']} | 2027: {projecoes['FED_PROJ_2027']}\n\n"
        msg += "🇧🇷 *MERCADO BRASIL (B3)*\n"
        for nome, ticker in list(macros_tickers.items())[6:]:
            p = dados[ticker].iloc[-1]
            var = ((p/dados[ticker].iloc[-2])-1)*100
            msg += f"{'💹' if var>=0 else '📉'} {nome}: {p:,.2f} ({var:+.2f}%)\n"
        msg += f"🏛️ Projeção SELIC (Focus): 2026: {projecoes['SELIC_2026']} | 2027: {projecoes['SELIC_2027']}\n"
        st.text_area("Copiar Relatório Macro:", msg, height=400)

# --- BOTÃO 2: CRIPTO ---
if btn_radar:
    with st.spinner('Analisando Top 100 & Narrativas...'):
        # Puxa dados de todas as moedas de uma vez para ganhar velocidade
        all_assets = list(set(top_100_tickers + [item for sublist in narrativas_config.values() for item in sublist]))
        data = yf.download(all_assets, period="5d", interval="1d", progress=False)
        precos = data['Close']
        volumes = data['Volume'].iloc[-1]
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        
        msg = f"📡 *RADAR CRIPTO & ECOSSISTEMAS*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        msg += f"📊 *Market Leader: Bitcoin*\n💵 US$ {precos['BTC-USD'].iloc[-1]:,.2f} ({((precos['BTC-USD'].iloc[-1]/precos['BTC-USD'].iloc[-2])-1)*100:+.2f}%)\n🍕 Dom: {buscar_dominancia()}\n\n"
        
        msg += "🏆 *Ranking de Narrativas (Volume)*"
        for narra, ativos in narrativas_config.items():
            msg += f"\n\n*{narra}:*"
            for i, ticker in enumerate(ativos):
                p = precos[ticker].iloc[-1]
                var_t = ((precos[ticker].iloc[-1]/precos[ticker].iloc[-2])-1)*100
                msg += f"\n {i+1}º {ticker.replace('-USD','')}: US$ {p:,.2f} ({var_t:+.2f}%){' ⚡' if var_t > 3 else ''}\n    ∟ Vol: {format_vol(volumes[ticker])}"
        
        # Lógica Top 3 Global (Entre as 100 maiores)
        variacoes_global = ((precos[top_100_tickers].iloc[-1] / precos[top_100_tickers].iloc[-2]) - 1) * 100
        msg += "\n\n🚀 *TOP 3 ALTAS GLOBAL (Top 100)* ⚡"
        for t, v in variacoes_global.nlargest(3).items(): msg += f"\n🟩 {t.replace('-USD','')}: {v:+.2f}% ⚡"
        msg += "\n\n⚠️ *TOP 3 BAIXAS GLOBAL (Top 100)* 🪫"
        for t, v in variacoes_global.nsmallest(3).items(): msg += f"\n🟥 {t.replace('-USD','')}: {v:+.2f}% 🪫"
        st.text_area("Copiar Radar Cripto:", msg, height=500)

# --- BOTÃO 3: UNLOCKS ---
if btn_unlock:
    hoje = datetime.now().date()
    # Dados de exemplo (No seu código real, você pode alimentar isso via API ou manual)
    dados_unlock = [{"m": "ARB", "d": "2026-04-20", "q": "92M"}, {"m": "OP", "d": "2026-04-29", "q": "31M"}, {"m": "SUI", "d": "2026-05-03", "q": "34M"}]
    msg = f"🔓 *RADAR DE DESBLOQUEIOS (40 DIAS)*\n🕒 {hoje.strftime('%d/%m/%Y')}\n\n"
    for i in dados_unlock:
        dt = datetime.strptime(i['d'], "%Y-%m-%d").date()
        faltam = (dt - hoje).days
        msg += f"{'🚨' if faltam <= 7 else '📅'} *{i['m']}*: {dt.strftime('%d/%m/%Y')}\n   ∟ Faltam: {faltam} dias | Qtd: {i['q']}\n\n"
    st.text_area("Copiar Agenda de Unlocks:", msg, height=300)

# --- BOTÃO 4: SITES ---
if btn_sites:
    st.subheader("🔗 Central de Ferramentas & Notícias")
    c_l1, c_l2 = st.columns(2)
    for i, (cat, sites) in enumerate(links_uteis.items()):
        with (c_l1 if i % 2 == 0 else c_l2):
            with st.expander(f"**{cat}**", expanded=True):
                for nome, url in sites.items(): st.markdown(f"🔗 [{nome}]({url})")

# --- APOIO ---
st.markdown("---")
st.subheader("🚀 Apoie o Projeto")
cp1, cp2 = st.columns(2)
with cp1: botao_copiar("Copiar PIX", "SUA_CHAVE_PIX", cor="#00b5a4")
with cp2: botao_copiar("Copiar Binance ID", "511081814", cor="#F3BA2F")
