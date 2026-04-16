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

# --- BANCO DE DADOS DE UNLOCKS ---
calendario_unlocks = [
    {"moeda": "ARB", "data": "2026-04-20", "quantidade": "100M", "impacto": "⚠️ Alto"},
    {"moeda": "STRK", "data": "2026-04-25", "quantidade": "64M", "impacto": "⚠️ Médio"},
    {"moeda": "SUI", "data": "2026-05-03", "quantidade": "34M", "impacto": "⚠️ Médio"},
    {"moeda": "OP", "data": "2026-05-15", "quantidade": "24M", "impacto": "⚠️ Alto"},
    {"moeda": "SOL", "data": "2026-05-20", "quantidade": "600K", "impacto": "ℹ️ Baixo"},
]

# --- CONFIGURAÇÃO DE ATIVOS ---
macros_sentimento = {"🌍 DXY (Índice Dólar)": "DX-Y.NYB", "🏦 Treasury 10Y": "^TNX", "😱 VIX (Índice Medo)": "^VIX"}
macros_eua = {"📈 Dow Jones": "YM=F", "🇺🇸 S&P 500": "ES=F", "💻 Nasdaq": "NQ=F"}
macros_br = {"🇧🇷 Ibovespa": "^BVSP", "💵 Dólar Comercial": "USDBRL=X"}
macros_commodities = {"🛢️ Petróleo Brent": "BZ=F", "📀 Ouro": "GC=F", "⛽ Petrobras (PETR4)": "PETR4.SA", "💎 Vale (VALE3)": "VALE3.SA", "🏦 Itaú (ITUB4)": "ITUB4.SA"}

narrativas = {
    "🤖 IA": ["NEAR-USD", "FET-USD"],
    "🏢 RWA": ["LINK-USD", "ONDO-USD"],
    "🌐 Web3/L1": ["ETH-USD", "SOL-USD"],
    "🤡 Memes": ["DOGE-USD", "WIF-USD"]
}
favs = [("ALGO", "ALGO-USD"), ("AVAX", "AVAX-USD"), ("XRP", "XRP-USD")]
criptos_radar = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "AVAX-USD", "ALGO-USD", "TIA-USD", "OP-USD", "ADA-USD", "TRX-USD"] + [a for sub in narrativas.values() for a in sub]

# --- INTERFACE ---
st.title("📡 Radar de Mercado")
c1, c2, c3 = st.columns(3)
with c1: btn_macro = st.button('🏛️ PANORAMA MACRO', use_container_width=True)
with c2: btn_radar = st.button('🎯 RADAR CRIPTO', use_container_width=True)
with c3: btn_unlock = st.button('🔓 UNLOCKS (40D)', use_container_width=True)

# --- BOTÃO 1: MACRO (RESTAURADO) ---
if btn_macro:
    with st.spinner('Gerando Panorama Macro...'):
        todos = {**macros_sentimento, **macros_eua, **macros_br, **macros_commodities}
        dados = yf.download(list(todos.values()), period="5d", interval="1d", progress=False)['Close']
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        msg = f"📡 *PANORAMA MACRO GLOBAL*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
        msg += "🌡️ *Indicadores de Sentimento*\n"
        for nome, ticker in macros_sentimento.items():
            p = dados[ticker].iloc[-1]
            if not pd.isna(p):
                var = ((p/dados[ticker].iloc[-2])-1)*100
                desc = " (Força do dólar)" if "DXY" in nome else " (Custo do dinheiro)" if "Treasury" in nome else " (Volatilidade)"
                msg += f"{nome}: {p:,.2f} ({var:+.2f}%){desc}\n"
        msg += "\n🌎 *Mercado Americano (Wall St)*\n"
        for nome, ticker in macros_eua.items():
            p = dados[ticker].iloc[-1]
            if not pd.isna(p):
                var = ((p/dados[ticker].iloc[-2])-1)*100
                msg += f"{'💹' if var>=0 else '📉'} {nome.split(' ')[1]}: {p:,.2f} ({var:+.2f}%)\n"
        msg += "\n🇧🇷 *Mercado Brasileiro (B3)*\n"
        for nome, ticker in macros_br.items():
            p = dados[ticker].iloc[-1]
            if not pd.isna(p):
                var = ((p/dados[ticker].iloc[-2])-1)*100
                msg += f"{'💹' if var>=0 else '📉'} {nome}: {p:,.2f} ({var:+.2f}%)\n"
        msg += "🏦 Selic: 10,75% a.a (Meta atual)\n\n📦 *Commodities & Blue Chips*\n"
        for nome, ticker in macros_commodities.items():
            p = dados[ticker].iloc[-1]
            if not pd.isna(p):
                var = ((p/dados[ticker].iloc[-2])-1)*100
                emoji = "🚀" if var >= 3.0 else "💹" if var >= 0 else "📉"
                msg += f"{emoji} {nome}: {p:,.2f} ({var:+.2f}%)\n"
        st.text_area("Cópia Macro:", msg, height=450)
        st.link_button("📲 ENVIAR MACRO", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}")

# --- BOTÃO 2: CRIPTO (RESTAURADO) ---
if btn_radar:
    with st.spinner('Mapeando Ecossistemas...'):
        data = yf.download(criptos_radar, period="14d", interval="1d", progress=False)
        precos, volumes = data['Close'], data['Volume'].iloc[-1]
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        rsi_v, rsi_s = calcular_rsi(precos["BTC-USD"])
        btc_p, btc_var = precos["BTC-USD"].iloc[-1], ((precos["BTC-USD"].iloc[-1]/precos["BTC-USD"].iloc[-2])-1)*100
        alerta_rsi = "⚠️ Risco de topo" if rsi_v >= 70 else "⚖️ Equilíbrio" if rsi_v > 30 else "📉 Oportunidade"
        msg = f"📡 *RADAR CRIPTO & ECOSSISTEMAS*\n🕒 {agora.strftime('%d/%m/%Y %H:%M')}\n\n📊 *Market Leader: Bitcoin*\n💵 Preço: US$ {btc_p:,.2f}\n🧭 Tendência: {'💹 Alta' if btc_var > 0 else '📉 Baixa'}\n🔥 RSI: {rsi_v:.2f} ({rsi_s})\n💡 *{alerta_rsi}*\n🍕 Dominância: {buscar_dominancia()}\n\n💎 *Portfólio Estratégico*\n"
        msg += " | ".join([f"{n}: ${precos[tk].iloc[-1]:,.3f}" for n, tk in favs]) + "\n\n🏆 *Narrativas & Fluxo de Volume*"
        for narra, ativos in narrativas.items():
            t1 = ativos[0]
            p1, v1 = precos[t1].iloc[-1], ((precos[t1].iloc[-1]/precos[t1].iloc[-2])-1)*100
            msg += f"\n{'🚀' if v1 > 5 else '💹' if v1 > 0 else '📉'} *{narra}:* {t1.replace('-USD','')}: {v1:+.2f}% | Vol: {format_vol(volumes[t1])}"
        variacoes = ((precos.iloc[-1] / precos.iloc[-2]) - 1) * 100
        msg += "\n\n🚀 *Top 3 Momentum* ⚡"
        for t, v in variacoes.nlargest(3).items(): msg += f"\n🟩 *{t.replace('-USD','')}*: {v:+.2f}% ⚡"
        msg += "\n\n⚠️ *Top 3 Fraqueza*"
        for t, v in variacoes.nsmallest(3).items(): msg += f"\n🟥 *{t.replace('-USD','')}*: {v:+.2f}% 🪫"
        st.text_area("Cópia Radar:", msg, height=500)
        st.link_button("📲 ENVIAR RADAR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}")

# --- BOTÃO 3: UNLOCKS (NOVO) ---
if btn_unlock:
    with st.spinner('Analisando Vesting...'):
        hoje = datetime.now().date()
        limite = hoje + timedelta(days=40)
        msg = f"🔓 *RADAR DE DESBLOQUEIOS (40 DIAS)*\n🕒 {hoje.strftime('%d/%m/%Y')}\n\n"
        encontrou = False
        for i in calendario_unlocks:
            data_u = datetime.strptime(i['data'], "%Y-%m-%d").date()
            if hoje <= data_u <= limite:
                faltam = (data_u - hoje).days
                msg += f"{'🚨' if faltam <= 7 else '📅'} *{i['moeda']}*: {i['data']} (Faltam {faltam} dias)\n   ∟ Qtd: {i['quantidade']} | Impacto: {i['impacto']}\n\n"
                encontrou = True
        if not encontrou: msg += "✅ Sem desbloqueios relevantes no radar."
        st.text_area("Cópia Unlocks:", msg, height=350)
        st.link_button("📲 ENVIAR UNLOCKS", f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}")

# --- APOIO ---
st.markdown("---")
st.subheader("🚀 Apoie o Projeto")
col_p, col_b = st.columns(2)
with col_p:
    st.write("**PIX Copia e Cola**")
    pix = "00020126700014BR.GOV.BCB.PIX0136841f1261-6e84-4132-9fcf-7e6eda71bb9e0208obrigado5204000053039865802BR5924Antonio Edinardo Pereira6009SAO PAULO62140510I8eDCHZjNB63048BFC"
    botao_copiar("Copiar PIX", pix, cor="#00b5a4")
with col_b:
    st.write("**Binance Pay ID**")
    botao_copiar("Copiar Pay ID", "511081814", cor="#F3BA2F")
st.caption("Privacidade garantida: Transações via gateway seguro. 🛡️")
