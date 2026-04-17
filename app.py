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

# --- BANCO DE DADOS ATUALIZADO ---
projecoes = {
    "SELIC_2026": "12,50%", "SELIC_2027": "10,50%",
    "FED_PROJ_2026": "3,40%", "FED_PROJ_2027": "3,10%"
}

lista_favoritas = ["BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "LINK-USD", "ALGO-USD", "SUI-USD"]

narrativas_config = {
    "🤖 IA": ["NEAR-USD", "FET-USD"],
    "🏢 RWA": ["LINK-USD", "ONDO-USD"],
    "🌐 WEB3/L1": ["ETH-USD", "SOL-USD"],
    "📡 DEPIN": ["RENDER-USD", "HNT-USD"],
    "🤡 MEMES": ["DOGE-USD", "WIF-USD"]
}

macros_tickers = {
    "🌍 DXY": "DX-Y.NYB", "🏦 Treasury 10Y": "^TNX", "😱 VIX": "^VIX",
    "📈 Dow Jones": "YM=F", "🇺🇸 S&P 500": "ES=F", "💻 Nasdaq": "NQ=F",
    "🇧🇷 Ibovespa": "^BVSP", "💵 Dólar Comercial": "USDBRL=X",
    "🛢️ Brent": "BZ=F", "📀 Ouro": "GC=F", "⛽ PETR4": "PETR4.SA", "💎 VALE3": "VALE3.SA"
}

links_uteis = {
    "📊 Análise & On-Chain": {
        "CoinMarketCap": "https://coinmarketcap.com",
        "DexScreener": "https://dexscreener.com",
        "Coinglass": "https://www.coinglass.com",
        "DefiLlama": "https://defillama.com"
    },
    "📅 Eventos & Notícias": {
        "CryptoPanic": "https://cryptopanic.com",
        "Token Unlocks": "https://token.unlocks.app",
        "Investing.com": "https://br.investing.com",
        "Cointelegraph": "https://br.cointelegraph.com"
    }
}

# --- FUNÇÕES DE APOIO ---
def buscar_dominancias():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        btc = f"{r['data']['market_cap_percentage']['btc']:.1f}%"
        eth = f"{r['data']['market_cap_percentage']['eth']:.1f}%"
        return btc, eth
    except: return "57.3%", "10.9%"

def format_vol(vol):
    try:
        if pd.isna(vol) or vol == 0: return "$---"
        if vol >= 1e9: return f"${vol/1e9:.1f}B"
        return f"${vol/1e6:.0f}M"
    except: return "$---"

def botao_copiar(label, texto_para_copiar, cor="#FF4B4B", key=None):
    id_html = f"btn_{key}" if key else label.lower().replace(" ", "_")
    html_code = f"""
    <div style="margin-bottom: 10px;">
        <button id="{id_html}" style="width: 100%; background-color: {cor}; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px;">
            📋 {label}
        </button>
    </div>
    <script>
    document.getElementById('{id_html}').addEventListener('click', function() {{
        const text = `{texto_para_copiar}`;
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
st.title("📡 Radar de Mercado")

btn_macro = st.button('🏛️ MACRO', use_container_width=True)
btn_radar = st.button('🎯 CRIPTO', use_container_width=True)
btn_unlock = st.button('🔓 UNLOCKS', use_container_width=True)
btn_sites = st.button('🔗 SITES', use_container_width=True)

# --- 1. BOTÃO MACRO ---
if btn_macro:
    with st.spinner('Acessando dados globais...'):
        dados = yf.download(list(macros_tickers.values()), period="5d", interval="1d", progress=False)['Close']
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        msg = f"📡 *PANORAMA MACRO GLOBAL*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        
        # EUA
        for nome, ticker in list(macros_tickers.items())[:6]:
            p, var = dados[ticker].iloc[-1], ((dados[ticker].iloc[-1]/dados[ticker].iloc[-2])-1)*100
            msg += f"{'💹' if var>=0 else '📉'} {nome}: {p:,.2f} ({var:+.2f}%)\n"
        msg += f"🏛️ *Projeção FED:* 2026: {projecoes['FED_PROJ_2026']} | 2027: {projecoes['FED_PROJ_2027']}\n\n"
        
        # Brasil
        for nome, ticker in list(macros_tickers.items())[6:]:
            p, var = dados[ticker].iloc[-1], ((dados[ticker].iloc[-1]/dados[ticker].iloc[-2])-1)*100
            msg += f"{'💹' if var>=0 else '📉'} {nome}: {p:,.2f} ({var:+.2f}%)\n"
        msg += f"🏛️ *Projeção SELIC:* 2026: {projecoes['SELIC_2026']} | 2027: {projecoes['SELIC_2027']}\n"
        
        st.text_area("Relatório Macro:", msg, height=350)
        c1, c2 = st.columns(2)
        with c1: botao_copiar("Copiar Macro", msg, key="copy_m")
        with c2: st.link_button("📲 WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

# --- 2. BOTÃO CRIPTO ---
if btn_radar:
    with st.spinner('Sincronizando Favoritas...'):
        ativos_narrativas = [item for sublist in narrativas_config.values() for item in sublist]
        todos_ativos = list(set(lista_favoritas + ativos_narrativas))
        data = yf.download(todos_ativos, period="5d", interval="1d", progress=False)
        precos, volumes = data['Close'], data['Volume'].iloc[-1]
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        dom_btc, dom_eth = buscar_dominancias()
        
        msg = f"📡 *RADAR CRIPTO & ECOSSISTEMAS*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        msg += "💎 *FAVORITAS*\n"
        for ticker in lista_favoritas:
            p, var = precos[ticker].iloc[-1], ((precos[ticker].iloc[-1]/precos[ticker].iloc[-2])-1)*100
            simbolo = ticker.replace('-USD','')
            emoji = "💹" if var >= 0 else "📉"
            
            if simbolo == "BTC": msg += f"📊 *Bitcoin*: US$ {p:,.2f} ({var:+.2f}%)\n∟ 🍕 Dom: {dom_btc}\n"
            elif simbolo == "ETH": msg += f"⟠ *Ethereum*: US$ {p:,.2f} ({var:+.2f}%)\n∟ 🍕 Dom: {dom_eth}\n"
            else: msg += f"{emoji} **{simbolo}**: US$ {p:,.4f} ({var:+.2f}%)\n"

        msg += "\n🏆 **NARRATIVAS (VOLUME)**"
        for narra, ativos in narrativas_config.items():
            p_n = narra.split(); msg += f"\n\n{p_n[0]} ***{p_n[1]}***:"
            for i, ticker in enumerate(ativos):
                p, var_t = precos[ticker].iloc[-1], ((precos[ticker].iloc[-1]/precos[ticker].iloc[-2])-1)*100
                nome_m = ticker.replace('-USD',''); emoji_t = "💹" if var_t >= 0 else "📉"
                msg += f"\n {i+1}º **{nome_m}**: US$ {p:,.2f} ({var_t:+.2f}%){' ⚡' if var_t > 3 else ''}\n    ∟ Vol: {format_vol(volumes[ticker])}"
        
        st.text_area("Relatório Cripto:", msg, height=450)
        c1, c2 = st.columns(2)
        with c1: botao_copiar("Copiar Radar", msg, key="copy_c")
        with c2: st.link_button("📲 WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

# --- 3. BOTÃO UNLOCKS (ATUALIZADO) ---
if btn_unlock:
    hoje = datetime.now().date()
    # Dados atualizados conforme calendário de Abril/Maio 2026
    unlocks_data = [
        {"m": "ARB", "d": "2026-04-20", "q": "92.6M"},
        {"m": "STRK", "d": "2026-05-15", "q": "64M"},
        {"m": "OP", "d": "2026-05-29", "q": "31.3M"},
        {"m": "AXS", "d": "2026-05-18", "q": "6M"}
    ]
    msg = f"🔓 *RADAR DE DESBLOQUEIOS*\n🕒 {hoje.strftime('%d/%m/%Y')}\n\n"
    for i in unlocks_data:
        dt = datetime.strptime(i['d'], "%Y-%m-%d").date()
        faltam = (dt - hoje).days
        msg += f"{'🚨' if faltam <= 7 else '📅'} *{i['m']}*: {dt.strftime('%d/%m/%Y')} | Qtd: {i['q']}\n   ∟ Faltam: {faltam} dias\n\n"
    st.text_area("Próximos Unlocks:", msg, height=250)
    c1, c2 = st.columns(2)
    with c1: botao_copiar("Copiar Unlocks", msg, key="copy_u")
    with c2: st.link_button("📲 WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

# --- 4. BOTÃO SITES ---
if btn_sites:
    st.subheader("🔗 Central de Ferramentas")
    for cat, sites in links_uteis.items():
        with st.expander(f"**{cat}**", expanded=True):
            for nome, url in sites.items(): st.markdown(f"🔗 [{nome}]({url})")

# --- APOIO E PAGAMENTOS ---
st.markdown("---")
st.subheader("🚀 Apoie o Projeto")
col_p1, col_p2 = st.columns(2)
with col_p1:
    pix_link = "00020126580014BR.GOV.BCB.PIX0136841f1261-6e84-4132-9fcf-7e6eda71bb9e5204000053039865802BR5924Antonio Edinardo Pereira6009SAO PAULO62140510wgb2JUeYe963046375"
    botao_copiar("Copiar Código PIX", pix_link, cor="#00b5a4", key="pay_pix")
with col_p2:
    botao_copiar("Copiar Binance ID", "511081814", cor="#F3BA2F", key="pay_bin")
