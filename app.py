import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import urllib.parse
import pytz
import pandas as pd
import requests
import streamlit.components.v1 as components

st.set_page_config(page_title="Radar de Mercado", page_icon="📈", layout="wide")

# --- FUNÇÕES DE APOIO ---
def buscar_dominancia():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=5).json()
        return f"{r['data']['market_cap_percentage']['btc']:.1f}%"
    except: return "57.2%"

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

# --- CONFIGURAÇÃO DE ATIVOS ---
macros_sentimento = {"🌍 DXY": "DX-Y.NYB", "🏦 Treasury 10Y": "^TNX", "😱 VIX": "^VIX"}
macros_eua = {"📈 Dow Jones": "YM=F", "🇺🇸 S&P 500": "ES=F", "💻 Nasdaq": "NQ=F"}
macros_br = {"🇧🇷 Ibovespa": "^BVSP", "💵 Dólar Comercial": "USDBRL=X"}
macros_commodities = {"🛢️ Brent": "BZ=F", "📀 Ouro": "GC=F", "⛽ PETR4": "PETR4.SA", "💎 VALE3": "VALE3.SA"}

# Narrativas Expandidas (1º e 2º lugar)
narrativas = {
    "🤖 IA": ["NEAR-USD", "FET-USD"],
    "🏢 RWA": ["LINK-USD", "ONDO-USD"],
    "🌐 Web3/L1": ["ETH-USD", "SOL-USD"],
    "🤡 Memes": ["DOGE-USD", "WIF-USD"],
    "📡 DePIN": ["RENDER-USD", "HNT-USD"],
    "🎮 GameFi": ["IMX-USD", "GALA-USD"],
    "🧬 DeSci": ["VITA-USD", "RSC-USD"],
    "⚡ L2s": ["ARB-USD", "OP-USD"]
}

# Lista estendida para monitorar o Top 100 real
top_100_tickers = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "AVAX-USD", "DOGE-USD", "DOT-USD", "LINK-USD",
    "MATIC-USD", "SHIB-USD", "TRX-USD", "LTC-USD", "BCH-USD", "UNI-USD", "NEAR-USD", "APT-USD", "TIA-USD", "FET-USD",
    "ONDO-USD", "WIF-USD", "STX-USD", "FIL-USD", "ARB-USD", "OP-USD", "RENDER-USD", "HNT-USD", "IMX-USD", "GALA-USD",
    "LDO-USD", "SUI-USD", "STRK-USD", "BEAM-USD", "PEPE-USD", "BONK-USD", "VITA-USD", "RSC-USD"
]

# --- INTERFACE ---
st.title("📡 Radar de Mercado")
c1, c2, c3 = st.columns(3)
with c1: btn_macro = st.button('🏛️ PANORAMA MACRO', use_container_width=True)
with c2: btn_radar = st.button('🎯 RADAR CRIPTO', use_container_width=True)
with c3: btn_unlock = st.button('🔓 UNLOCKS (40D)', use_container_width=True)

# --- BOTÃO 1: MACRO ---
if btn_macro:
    with st.spinner('Processando...'):
        todos = {**macros_sentimento, **macros_eua, **macros_br, **macros_commodities}
        dados = yf.download(list(todos.values()), period="5d", interval="1d", progress=False)['Close']
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        msg = f"📡 *PANORAMA MACRO GLOBAL*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        for nome, ticker in todos.items():
            p = dados[ticker].iloc[-1]
            if not pd.isna(p):
                var = ((p/dados[ticker].iloc[-2])-1)*100
                msg += f"{'💹' if var>=0 else '📉'} {nome}: {p:,.2f} ({var:+.2f}%)\n"
        st.text_area("Cópia Macro:", msg, height=400)
        st.link_button("📲 ENVIAR MACRO", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}")

# --- BOTÃO 2: CRIPTO (ATUALIZADO COM 8 NARRATIVAS) ---
if btn_radar:
    with st.spinner('Analisando Narrativas...'):
        data = yf.download(top_100_tickers, period="5d", interval="1d", progress=False)
        precos, volumes = data['Close'], data['Volume'].iloc[-1]
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        
        rsi_v, rsi_s = calcular_rsi(precos["BTC-USD"])
        btc_p = precos["BTC-USD"].iloc[-1]
        btc_var = ((precos["BTC-USD"].iloc[-1]/precos["BTC-USD"].iloc[-2])-1)*100
        alerta_rsi = "⚠️ Risco de topo" if rsi_v >= 70 else "⚖️ Equilíbrio" if rsi_v > 30 else "📉 Oportunidade"
        
        msg = f"📡 *RADAR CRIPTO & ECOSSISTEMAS*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        msg += f"📊 *Market Leader: Bitcoin*\n💵 US$ {btc_p:,.2f} ({btc_var:+.2f}%)\n🔥 RSI: {rsi_v:.2f} ({rsi_s})\n💡 *{alerta_rsi}*\n🍕 Dominância: {buscar_dominancia()}\n\n"
        
        msg += "🏆 *Narrativas & Fluxo de Volume*"
        for narra, ativos in narrativas.items():
            # Tenta pegar a variação do primeiro ativo da categoria para o emoji principal
            try:
                v_cat = ((precos[ativos[0]].iloc[-1]/precos[ativos[0]].iloc[-2])-1)*100
                emoji_cat = "💹" if v_cat >= 0 else "📉"
                msg += f"\n{emoji_cat} *{narra}:*"
                for i, ticker in enumerate(ativos):
                    if ticker in precos.columns:
                        p = precos[ticker].iloc[-1]
                        v = ((p/precos[ticker].iloc[-2])-1)*100
                        vol = format_vol(volumes[ticker])
                        msg += f"\n {i+1}º {ticker.replace('-USD','')}: {v:+.2f}% | Vol: {vol}"
                msg += "\n"
            except: continue
        
        variacoes = ((precos.iloc[-1] / precos.iloc[-2]) - 1) * 100
        msg += "\n🚀 *Top 5 Momentum* ⚡"
        for t, v in variacoes.nlargest(5).items():
            msg += f"\n🟩 *{t.replace('-USD','')}*: {v:+.2f}% ⚡"
            
        msg += "\n\n⚠️ *Top 5 Fraqueza*"
        for t, v in variacoes.nsmallest(5).items():
            msg += f"\n🟥 *{t.replace('-USD','')}*: {v:+.2f}% 🪫"
            
        st.text_area("Cópia Radar:", msg, height=600)
        st.link_button("📲 ENVIAR RADAR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}")

# --- BOTÃO 3: UNLOCKS (MANTIDO) ---
if btn_unlock:
    with st.spinner('Verificando Vesting...'):
        hoje = datetime.now().date()
        dados_reais = [
            {"m": "AXS", "d": datetime(2026, 4, 17).date(), "q": "6.08M", "i": "⚠️ Médio"},
            {"m": "ARB", "d": datetime(2026, 4, 20).date(), "q": "92.6M", "i": "🚨 Alto"},
            {"m": "ID", "d": datetime(2026, 4, 22).date(), "q": "18.4M", "i": "⚠️ Médio"},
            {"m": "STRK", "d": datetime(2026, 4, 25).date(), "q": "64M", "i": "⚠️ Médio"},
            {"m": "OP", "d": datetime(2026, 4, 29).date(), "q": "31.3M", "i": "🚨 Alto"},
            {"m": "SUI", "d": datetime(2026, 5, 3).date(), "q": "34.6M", "i": "⚠️ Alto"},
            {"m": "MEME", "d": datetime(2026, 5, 3).date(), "q": "5.3B", "i": "🚨 Crítico"},
            {"m": "IMX", "d": datetime(2026, 5, 12).date(), "q": "25.5M", "i": "⚠️ Médio"},
            {"m": "PYTH", "d": datetime(2026, 5, 20).date(), "q": "2.1B", "i": "🚨 Choque"}
        ]
        msg = f"🔓 *RADAR DE DESBLOQUEIOS (40 DIAS)*\n🕒 Gerado em: {hoje.strftime('%d/%m/%Y')}\n\n"
        for i in sorted(dados_reais, key=lambda x: x['d']):
            if hoje <= i['d'] <= hoje + timedelta(days=40):
                faltam = (i['d'] - hoje).days
                msg += f"{'🚨' if faltam <= 7 else '📅'} *{i['m']}*: {i['d'].strftime('%d/%m/%Y')}\n   ∟ Faltam: {faltam} dias | Qtd: {i['q']}\n\n"
        st.text_area("Cópia Unlocks:", msg, height=400)
        st.link_button("📲 ENVIAR UNLOCKS", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}")

# --- APOIO ---
st.markdown("---")
st.subheader("🚀 Apoie o Projeto")
c_p, c_b = st.columns(2)
with c_p: botao_copiar("Copiar PIX", "00020126700014BR.GOV.BCB.PIX0136841f1261-6e84-4132-9fcf-7e6eda71bb9e0208obrigado5204000053039865802BR5924Antonio Edinardo Pereira6009SAO PAULO62140510I8eDCHZjNB63048BFC", cor="#00b5a4")
with c_b: botao_copiar("Copiar Binance Pay ID", "511081814", cor="#F3BA2F")
