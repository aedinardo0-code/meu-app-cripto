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

# --- BANCO DE DADOS E CONFIGURAÇÕES ---
projecoes = {
    "SELIC_2026": "12,50%", "SELIC_2027": "10,50%",
    "FED_PROJ_2026": "3,40%", "FED_PROJ_2027": "3,10%"
}

lista_favoritas = [
    "BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", 
    "AVAX-USD", "LINK-USD", "ALGO-USD", "SUI-USD"
]

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

# --- FUNÇÕES DE APOIO ---
def buscar_dominancias():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        btc = f"{r['data']['market_cap_percentage']['btc']:.1f}%"
        eth = f"{r['data']['market_cap_percentage']['eth']:.1f}%"
        return btc, eth
    except:
        return "57.4%", "17.2%"

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
        btn.innerText = '✅ COPIADO!';
        btn.style.backgroundColor = '#28a745';
        setTimeout(function() {{ btn.innerText = '📋 {label}'; btn.style.backgroundColor = '{cor}'; }}, 2000);
    }});
    </script>
    """
    return components.html(html_code, height=70)

# --- INTERFACE PRINCIPAL ---
st.title("📡 Radar de Mercado")
c1, c2, c3, c4 = st.columns(4)
with c1: btn_macro = st.button('🏛️ MACRO', use_container_width=True)
with c2: btn_radar = st.button('🎯 CRIPTO', use_container_width=True)
with c3: btn_unlock = st.button('🔓 UNLOCKS', use_container_width=True)
with c4: btn_sites = st.button('🔗 SITES', use_container_width=True)

# --- LÓGICA DO BOTÃO 2: CRIPTO ---
if btn_radar:
    with st.spinner('Sincronizando Mercado...'):
        ativos_narrativas = [item for sublist in narrativas_config.values() for item in sublist]
        todos_ativos = list(set(lista_favoritas + ativos_narrativas))
        
        data = yf.download(todos_ativos, period="5d", interval="1d", progress=False)
        precos, volumes = data['Close'], data['Volume'].iloc[-1]
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        dom_btc, dom_eth = buscar_dominancias()
        
        msg = f"📡 *RADAR CRIPTO & ECOSSISTEMAS*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        
        msg += "💎 *FAVORITAS*"
        for ticker in lista_favoritas:
            p = precos[ticker].iloc[-1]
            var = ((precos[ticker].iloc[-1]/precos[ticker].iloc[-2])-1)*100
            simbolo = ticker.replace('-USD','')
            
            if simbolo == "BTC":
                msg += f"\n📊 ***Bitcoin***: US$ {p:,.2f} ({var:+.2f}%)\n∟ 🍕 Dom: {dom_btc}"
            elif simbolo == "ETH":
                msg += f"\n⟠ ***Ethereum***: US$ {p:,.2f} ({var:+.2f}%)\n∟ 🍕 Dom: {dom_eth}"
            else:
                msg += f"\n🔹 **{simbolo}**: US$ {p:,.4f} ({var:+.2f}%)"

        msg += "\n\n🏆 **NARRATIVAS (VOLUME)**"
        for narra, ativos in narrativas_config.items():
            # Extrai o emoji e o nome da categoria para colocar em negrito
            partes = narra.split()
            emoji = partes[0]
            cat_nome = partes[1]
            msg += f"\n\n{emoji} ***{cat_nome}***:"
            for i, ticker in enumerate(ativos):
                p, var_t = precos[ticker].iloc[-1], ((precos[ticker].iloc[-1]/precos[ticker].iloc[-2])-1)*100
                nome_moeda = ticker.replace('-USD','')
                msg += f"\n {i+1}º **{nome_moeda}**: US$ {p:,.2f} ({var_t:+.2f}%){' ⚡' if var_t > 3 else ''}\n    ∟ Vol: {format_vol(volumes[ticker])}"
        
        st.text_area("Texto do Radar:", msg, height=500)
        col_c1, col_c2 = st.columns(2)
        with col_c1: botao_copiar("Copiar Radar", msg, key="c_copy")
        with col_c2: st.link_button("📲 Enviar p/ WhatsApp", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True)

# (A lógica dos outros botões segue o mesmo padrão de Copy/WhatsApp)
