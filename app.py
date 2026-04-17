import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import urllib.parse
import pytz
import pandas as pd
import requests
import streamlit.components.v1 as components

# Configuração da Página
st.set_page_config(page_title="Radar de Mercado", page_icon="📈", layout="wide")

# --- BANCO DE DADOS DE PROJEÇÕES (Atualize aqui quando o Focus ou FED mudar) ---
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

# --- CONFIGURAÇÕES DE ATIVOS E LINKS ---
macros_sentimento = {"🌍 DXY": "DX-Y.NYB", "🏦 Treasury 10Y": "^TNX", "😱 VIX": "^VIX"}
macros_eua = {"📈 Dow Jones": "YM=F", "🇺🇸 S&P 500": "ES=F", "💻 Nasdaq": "NQ=F"}
macros_br = {"🇧🇷 Ibovespa": "^BVSP", "💵 Dólar Comercial": "USDBRL=X"}
macros_commodities = {"🛢️ Brent": "BZ=F", "📀 Ouro": "GC=F", "⛽ PETR4": "PETR4.SA", "💎 VALE3": "VALE3.SA"}

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

# --- INTERFACE PRINCIPAL ---
st.title("📡 Radar de Mercado")
c1, c2, c3, c4 = st.columns(4)
with c1: btn_macro = st.button('🏛️ MACRO', use_container_width=True)
with c2: btn_radar = st.button('🎯 CRIPTO', use_container_width=True)
with c3: btn_unlock = st.button('🔓 UNLOCKS', use_container_width=True)
with c4: btn_sites = st.button('🔗 SITES', use_container_width=True)

# --- LÓGICA BOTÃO 1: MACRO ---
if btn_macro:
    with st.spinner('Acessando dados globais...'):
        todos_tickers = {**macros_sentimento, **macros_eua, **macros_br, **macros_commodities}
        dados = yf.download(list(todos_tickers.values()), period="5d", interval="1d", progress=False)['Close']
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        
        msg = f"📡 *PANORAMA MACRO GLOBAL*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        
        msg += "🇺🇸 *MERCADO EUA & JUROS*\n"
        for nome, ticker in {**macros_sentimento, **macros_eua}.items():
            p = dados[ticker].iloc[-1]
            if not pd.isna(p):
                var = ((p/dados[ticker].iloc[-2])-1)*100
                msg += f"{'💹' if var>=0 else '📉'} {nome}: {p:,.2f} ({var:+.2f}%)\n"
        msg += f"🏛️ Projeção FED (Dot Plot): 2026: {projecoes['FED_PROJ_2026']} | 2027: {projecoes['FED_PROJ_2027']}\n\n"

        msg += "🇧🇷 *MERCADO BRASIL (B3)*\n"
        for nome, ticker in {**macros_br, **macros_commodities}.items():
            p = dados[ticker].iloc[-1]
            if not pd.isna(p):
                var = ((p/dados[ticker].iloc[-2])-1)*100
                msg += f"{'💹' if var>=0 else '📉'} {nome}: {p:,.2f} ({var:+.2f}%)\n"
        msg += f"🏛️ Projeção SELIC (Focus): 2026: {projecoes['SELIC_2026']} | 2027: {projecoes['SELIC_2027']}\n"
        
        st.text_area("Cópia Macro:", msg, height=500)

# --- LÓGICA BOTÃO 2: CRIPTO ---
if btn_radar:
    with st.spinner('Sincronizando Ecossistemas...'):
        tickers_radar = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "AVAX-USD", "DOGE-USD", "LINK-USD", "TRX-USD", "NEAR-USD", "TIA-USD", "FET-USD", "ONDO-USD", "WIF-USD", "RENDER-USD", "HNT-USD"]
        data = yf.download(tickers_radar, period="5d", interval="1d", progress=False)
        precos = data['Close']
        volumes = data['Volume'].iloc[-1]
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        
        msg = f"📡 *RADAR CRIPTO & ECOSSISTEMAS*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        msg += f"📊 *Market Leader: Bitcoin*\n💵 US$ {precos['BTC-USD'].iloc[-1]:,.2f} ({((precos['BTC-USD'].iloc[-1]/precos['BTC-USD'].iloc[-2])-1)*100:+.2f}%)\n🍕 Dom: {buscar_dominancia()}\n\n"
        msg += "🏆 *Ranking de Narrativas (Volume)*"
        
        narrativas_config = {
            "🤖 IA": ["NEAR-USD", "FET-USD"],
            "🏢 RWA": ["LINK-USD", "ONDO-USD"],
            "🌐 Web3/L1": ["ETH-USD", "SOL-USD"],
            "📡 DePIN": ["RENDER-USD", "HNT-USD"],
            "🤡 Memes": ["DOGE-USD", "WIF-USD"]
        }

        for narra, ativos in narrativas_config.items():
            msg += f"\n\n*{narra}:*"
            for i, ticker in enumerate(ativos):
                if ticker in precos.columns:
                    p = precos[ticker].iloc[-1]
                    var_t = ((precos[ticker].iloc[-1]/precos[ticker].iloc[-2])-1)*100
                    raio = " ⚡" if var_t > 3 else ""
                    msg += f"\n {i+1}º {ticker.replace('-USD','')}: US$ {p:,.2f} ({var_t:+.2f}%){raio}\n    ∟ Vol: {format_vol(volumes[ticker])}"
        
        variacoes = ((precos.iloc[-1] / precos.iloc[-2]) - 1) * 100
        msg += "\n\n🚀 *Top 3 Altas* ⚡"
        for t, v in variacoes.nlargest(3).items(): msg += f"\n🟩 {t.replace('-USD','')}: {v:+.2f}% ⚡"
        msg += "\n\n⚠️ *Top 3 Baixas* 🪫"
        for t, v in variacoes.nsmallest(3).items(): msg += f"\n🟥 {t.replace('-USD','')}: {v:+.2f}% 🪫"
            
        st.text_area("Cópia Radar:", msg, height=600)

# --- LÓGICA BOTÃO 3: UNLOCKS ---
if btn_unlock:
    with st.spinner('Verificando Unlocks...'):
        hoje = datetime.now().date()
        dados_reais = [
            {"m": "AXS", "d": datetime(2026, 4, 17).date(), "q": "6.08M"},
            {"m": "ARB", "d": datetime(2026, 4, 20).date(), "q": "92.6M"},
            {"m": "OP", "d": datetime(2026, 4, 29).date(), "q": "31.3M"},
            {"m": "SUI", "d": datetime(2026, 5, 3).date(), "q": "34.6M"},
            {"m": "PYTH", "d": datetime(2026, 5, 20).date(), "q": "2.1B"}
        ]
        msg = f"🔓 *RADAR DE DESBLOQUEIOS (40 DIAS)*\n🕒 Gerado em: {hoje.strftime('%d/%m/%Y')}\n\n"
        for i in sorted(dados_reais, key=lambda x: x['d']):
            if hoje <= i['d'] <= hoje + timedelta(days=40):
                faltam = (i['d'] - hoje).days
                msg += f"{'🚨' if faltam <= 7 else '📅'} *{i['m']}*: {i['d'].strftime('%d/%m/%Y')}\n   ∟ Faltam: {faltam} dias | Qtd: {i['q']}\n\n"
        st.text_area("Cópia Unlocks:", msg, height=400)

# --- LÓGICA BOTÃO 4: SITES (SEM CÓPIA) ---
if btn_sites:
    st.subheader("🔗 Central de Ferramentas & Notícias")
    col_l1, col_l2 = st.columns(2)
    for i, (categoria, sites) in enumerate(links_uteis.items()):
        target = col_l1 if i % 2 == 0 else col_l2
        with target:
            with st.expander(f"**{categoria}**", expanded=True):
                for nome, url in sites.items():
                    st.markdown(f"🔗 [{nome}]({url})")
    st.info("💡 Clique nos nomes acima para abrir os sites em uma nova aba.")

# --- APOIO ---
st.markdown("---")
st.subheader("🚀 Apoie o Projeto")
c_p, c_b = st.columns(2)
with c_p: botao_copiar("Copiar PIX", "SUA_CHAVE_PIX_AQUI", cor="#00b5a4")
with c_b: botao_copiar("Copiar Binance ID", "511081814", cor="#F3BA2F")
