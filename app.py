import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import urllib.parse
import pytz
import pandas as pd
import requests
import streamlit.components.v1 as components

# Configuração da página para aproveitar melhor o espaço lateral
st.set_page_config(page_title="Radar de Mercado Pro", page_icon="📡", layout="wide")

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
        const text = '{texto_para_copiar}';
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

# --- BANCO DE DADOS DE UNLOCKS (Programação 2026) ---
calendario_unlocks = [
    {"moeda": "ARB", "data": "2026-04-20", "quantidade": "100M", "impacto": "⚠️ Alto"},
    {"moeda": "STRK", "data": "2026-04-25", "quantidade": "64M", "impacto": "⚠️ Médio"},
    {"moeda": "SUI", "data": "2026-05-03", "quantidade": "34M", "impacto": "⚠️ Médio"},
    {"moeda": "OP", "data": "2026-05-15", "quantidade": "24M", "impacto": "⚠️ Alto"},
    {"moeda": "SOL", "data": "2026-05-20", "quantidade": "600K", "impacto": "ℹ️ Baixo"},
    {"moeda": "IMX", "data": "2026-05-22", "quantidade": "25M", "impacto": "⚠️ Médio"},
]

# --- ATIVOS ---
macros_sentimento = {"🌍 DXY": "DX-Y.NYB", "🏦 Treasury 10Y": "^TNX", "😱 VIX": "^VIX"}
macros_eua = {"📈 Dow Jones": "YM=F", "🇺🇸 S&P 500": "ES=F", "💻 Nasdaq": "NQ=F"}
macros_br = {"🇧🇷 Ibovespa": "^BVSP", "💵 Dólar": "USDBRL=X"}
macros_commodities = {"🛢️ Brent": "BZ=F", "📀 Ouro": "GC=F", "⛽ PETR4": "PETR4.SA", "💎 VALE3": "VALE3.SA"}

narrativas = {
    "🤖 IA": ["NEAR-USD", "FET-USD"],
    "🏢 RWA": ["LINK-USD", "ONDO-USD"],
    "🌐 Web3/L1": ["ETH-USD", "SOL-USD"],
    "🤡 Memes": ["DOGE-USD", "WIF-USD"]
}
favs = [("ALGO", "ALGO-USD"), ("AVAX", "AVAX-USD"), ("XRP", "XRP-USD")]
criptos_radar = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD", "ALGO-USD"] + [a for sub in narrativas.values() for a in sub]

# --- INTERFACE PRINCIPAL ---
st.title("📡 Radar de Mercado Pro")
st.markdown("Selecione uma análise para gerar o relatório:")

col_b1, col_b2, col_b3 = st.columns(3)
with col_b1: btn_macro = st.button('🏛️ PANORAMA MACRO', use_container_width=True)
with col_b2: btn_radar = st.button('🎯 RADAR CRIPTO', use_container_width=True)
with col_b3: btn_unlock = st.button('🔓 UNLOCKS (40D)', use_container_width=True)

# --- EXECUÇÃO DOS BOTÕES ---
if btn_macro:
    with st.spinner('Puxando dados globais...'):
        todos = {**macros_sentimento, **macros_eua, **macros_br, **macros_commodities}
        dados = yf.download(list(todos.values()), period="5d", interval="1d", progress=False)['Close']
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        
        msg = f"📡 *PANORAMA MACRO GLOBAL*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        for nome, ticker in todos.items():
            p = dados[ticker].iloc[-1]
            if not pd.isna(p):
                var = ((p/dados[ticker].iloc[-2])-1)*100
                emoji = "💹" if var >= 0 else "📉"
                msg += f"{emoji} {nome}: {p:,.2f} ({var:+.2f}%)\n"
        
        st.text_area("Relatório Macro:", msg, height=300)
        st.link_button("📲 ENVIAR MACRO", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}")

if btn_radar:
    with st.spinner('Analisando criptoativos...'):
        data = yf.download(criptos_radar, period="14d", interval="1d", progress=False)
        precos, volumes = data['Close'], data['Volume'].iloc[-1]
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        
        rsi_v, rsi_s = calcular_rsi(precos["BTC-USD"])
        btc_p = precos["BTC-USD"].iloc[-1]
        
        msg = f"📡 *RADAR CRIPTO & ECOSSISTEMAS*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        msg += f"📊 *Bitcoin:* US$ {btc_p:,.2f}\n🔥 RSI: {rsi_v:.2f} ({rsi_s})\n🍕 Dominância: {buscar_dominancia()}\n\n"
        msg += "💎 *Favoritas:* " + " | ".join([f"{n}: ${precos[tk].iloc[-1]:,.3f}" for n, tk in favs]) + "\n\n"
        
        for narra, ativos in narrativas.items():
            t1 = ativos[0]
            v1 = ((precos[t1].iloc[-1]/precos[t1].iloc[-2])-1)*100
            msg += f"{'🚀' if v1 > 5 else '💹'} *{narra}:* {t1.replace('-USD','')}: {v1:+.2f}% | Vol: {format_vol(volumes[t1])}\n"
            
        st.text_area("Relatório Cripto:", msg, height=400)
        st.link_button("📲 ENVIAR RADAR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}")

if btn_unlock:
    with st.spinner('Cruzando dados de Vesting...'):
        hoje = datetime.now().date()
        limite = hoje + timedelta(days=40)
        msg = f"🔓 *RADAR DE DESBLOQUEIOS (40 DIAS)*\n🕒 {hoje.strftime('%d/%m/%Y')}\n\n"
        encontrou = False
        
        for i in calendario_unlocks:
            data_u = datetime.strptime(i['data'], "%Y-%m-%d").date()
            if hoje <= data_u <= limite:
                faltam = (data_u - hoje).days
                msg += f"{'🚨' if faltam <= 7 else '📅'} *{i['moeda']}*: {i['data']} (Faltam {faltam} dias)\n"
                msg += f"   ∟ Qtd: {i['quantidade']} | Impacto: {i['impacto']}\n\n"
                encontrou = True
        
        if not encontrou: msg += "✅ Sem desbloqueios relevantes no radar de 40 dias."
        
        st.text_area("Relatório Unlocks:", msg, height=350)
        st.link_button("📲 ENVIAR UNLOCKS", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}")

# --- APOIO ---
st.markdown("---")
st.subheader("🚀 Apoie o Projeto")
col_pix, col_binance = st.columns(2)

with col_pix:
    st.write("**PIX Copia e Cola**")
    pix = "00020126700014BR.GOV.BCB.PIX0136841f1261-6e84-4132-9fcf-7e6eda71bb9e0208obrigado5204000053039865802BR5924Antonio Edinardo Pereira6009SAO PAULO62140510I8eDCHZjNB63048BFC"
    botao_copiar("Copiar PIX", pix, cor="#00b5a4")
    st.caption("Beneficiário: Antonio Edinardo")

with col_binance:
    st.write("**Binance Pay ID**")
    botao_copiar("Copiar Pay ID", "511081814", cor="#F3BA2F")
    st.caption("No App: Pay > Enviar > ID do Pay")

st.caption("Privacidade garantida: Transações via gateway seguro. 🛡️")
