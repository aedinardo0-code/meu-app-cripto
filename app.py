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
    "SELIC_2026": "12,50%", "SELIC_2027": "10,50%",
    "FED_PROJ_2026": "3,40%", "FED_PROJ_2027": "3,10%"
}

# --- FUNÇÕES DE APOIO ---
def buscar_dominancia():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        return f"{r['data']['market_cap_percentage']['btc']:.1f}%"
    except: return "57.2%"

def buscar_top_100_coingecko():
    try:
        # Busca as top 100 moedas reais por market cap
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=24h"
        data = requests.get(url, timeout=10).json()
        df = pd.DataFrame(data)
        altas = df.nlargest(3, 'price_change_percentage_24h')
        baixas = df.nsmallest(3, 'price_change_percentage_24h')
        return altas, baixas
    except:
        return None, None

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
        <button id="{id_html}" style="width: 100%; background-color: {cor}; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; transition: 0.3s;">
            📋 {label}
        </button>
    </div>
    <script>
    document.getElementById('{id_html}').addEventListener('click', function() {{
        const text = `{texto_para_copiar}`;
        const el = document.createElement('textarea');
        el.value = text;
        document.body.appendChild(el);
        el.select();
        document.execCommand('copy');
        document.body.removeChild(el);
        const btn = document.getElementById('{id_html}');
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
        msg += f"🏛️ Projeção FED: 2026: {projecoes['FED_PROJ_2026']} | 2027: {projecoes['FED_PROJ_2027']}\n\n"
        msg += "🇧🇷 *MERCADO BRASIL (B3)*\n"
        for nome, ticker in list(macros_tickers.items())[6:]:
            p = dados[ticker].iloc[-1]
            var = ((p/dados[ticker].iloc[-2])-1)*100
            msg += f"{'💹' if var>=0 else '📉'} {nome}: {p:,.2f} ({var:+.2f}%)\n"
        msg += f"🏛️ Projeção SELIC: 2026: {projecoes['SELIC_2026']} | 2027: {projecoes['SELIC_2027']}\n"
        st.text_area("Texto do Relatório:", msg, height=300)
        col_m1, col_m2 = st.columns(2)
        with col_m1: botao_copiar("Copiar Relatório", msg, key="macro_copy")
        with col_m2: st.link_button("📲 Enviar p/ WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

# --- BOTÃO 2: CRIPTO ---
if btn_radar:
    with st.spinner('Buscando dados Reais do Top 100...'):
        assets_narra = [item for sublist in narrativas_config.values() for item in sublist] + ["BTC-USD"]
        data_yf = yf.download(assets_narra, period="5d", interval="1d", progress=False)
        precos, volumes = data_yf['Close'], data_yf['Volume'].iloc[-1]
        altas_cg, baixas_cg = buscar_top_100_coingecko()
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        
        msg = f"📡 *RADAR CRIPTO & ECOSSISTEMAS*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        msg += f"📊 *Bitcoin:* US$ {precos['BTC-USD'].iloc[-1]:,.2f} ({((precos['BTC-USD'].iloc[-1]/precos['BTC-USD'].iloc[-2])-1)*100:+.2f}%)\n🍕 Dom: {buscar_dominancia()}\n\n"
        
        msg += "🏆 *Narrativas (Volume)*"
        for narra, ativos in narrativas_config.items():
            msg += f"\n\n*{narra}:*"
            for i, ticker in enumerate(ativos):
                p, var_t = precos[ticker].iloc[-1], ((precos[ticker].iloc[-1]/precos[ticker].iloc[-2])-1)*100
                msg += f"\n {i+1}º {ticker.replace('-USD','')}: US$ {p:,.2f} ({var_t:+.2f}%){' ⚡' if var_t > 3 else ''}\n    ∟ Vol: {format_vol(volumes[ticker])}"
        
        if altas_cg is not None:
            msg += "\n\n🚀 *TOP 3 ALTAS GLOBAL (Top 100)* ⚡"
            for _, row in altas_cg.iterrows():
                msg += f"\n🟩 {row['symbol'].upper()}: {row['price_change_percentage_24h']:+.2f}% ⚡"
            msg += "\n\n⚠️ *TOP 3 BAIXAS GLOBAL (Top 100)* 🪫"
            for _, row in baixas_cg.iterrows():
                msg += f"\n🟥 {row['symbol'].upper()}: {row['price_change_percentage_24h']:+.2f}% 🪫"
        
        st.text_area("Texto do Radar:", msg, height=500)
        col_c1, col_c2 = st.columns(2)
        with col_c1: botao_copiar("Copiar Radar", msg, key="cripto_copy")
        with col_c2: st.link_button("📲 Enviar p/ WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

# --- BOTÃO 3: UNLOCKS ---
if btn_unlock:
    hoje = datetime.now().date()
    dados_unlock = [{"m": "ARB", "d": "2026-04-20", "q": "92M"}, {"m": "OP", "d": "2026-04-29", "q": "31M"}, {"m": "SUI", "d": "2026-05-03", "q": "34M"}]
    msg = f"🔓 *RADAR DE DESBLOQUEIOS (40D)*\n🕒 {hoje.strftime('%d/%m/%Y')}\n\n"
    for i in dados_unlock:
        dt = datetime.strptime(i['d'], "%Y-%m-%d").date()
        faltam = (dt - hoje).days
        msg += f"{'🚨' if faltam <= 7 else '📅'} *{i['m']}*: {dt.strftime('%d/%m/%Y')}\n   ∟ Faltam: {faltam} dias | Qtd: {i['q']}\n\n"
    st.text_area("Texto Unlocks:", msg, height=250)
    col_u1, col_u2 = st.columns(2)
    with col_u1: botao_copiar("Copiar Unlocks", msg, key="unlock_copy")
    with col_u2: st.link_button("📲 Enviar p/ WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

# --- BOTÃO 4: SITES ---
if btn_sites:
    st.subheader("🔗 Central de Ferramentas")
    c_l1, c_l2 = st.columns(2)
    for i, (cat, sites) in enumerate(links_uteis.items()):
        with (c_l1 if i % 2 == 0 else c_l2):
            with st.expander(f"**{cat}**", expanded=True):
                for nome, url in sites.items(): st.markdown(f"🔗 [{nome}]({url})")

# --- APOIO ---
st.markdown("---")
st.subheader("🚀 Apoie o Projeto")
cp1, cp2 = st.columns(2)
with cp1: botao_copiar("Copiar PIX", "SUA_CHAVE_PIX", cor="#00b5a4", key="pix_main")
with cp2: botao_copiar("Copiar Binance ID", "511081814", cor="#F3BA2F", key="binance_main")
