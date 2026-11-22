import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timezone

API = "https://api.elections.kalshi.com/trade-api/v2"
st.set_page_config(page_title="JORDAN TC | Kalshi Scanner", page_icon="📡", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1450px;}
.hero {padding: 1.2rem 1.4rem; border: 1px solid rgba(128,128,128,.25); border-radius: 18px; margin-bottom: 1rem;}
.muted {color: #888; font-size: .9rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>📡 JORDAN TC</h1><h3> KALSHI MARKET SCANNER</h3><p class="muted">Escáner público de mercados · Solo lectura · Sin operaciones automáticas</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuración")
    pages = st.slider("Páginas a consultar", 1, 20, 5)
    min_volume = st.number_input("Volumen mínimo 24h (contratos)", min_value=0, value=100, step=50)
    max_spread = st.slider("Spread máximo para observar", 0.01, 0.30, 0.08, 0.01)
    category_filter = st.multiselect(
        "Categorías",
        ["Criptomonedas", "Política", "Deportes", "Economía", "Otros"],
        default=["Criptomonedas", "Política", "Deportes", "Economía", "Otros"]
    )
    refresh = st.button("🔄 Actualizar mercados", use_container_width=True)
    st.caption("Los datos públicos de mercado no requieren claves API.")

def num(x):
    try:
        return float(x) if x is not None and x != "" else None
    except (TypeError, ValueError):
        return None

def classify(m):
    cat = str(m.get("category") or "").lower()
    text = (str(m.get("title") or "") + " " + str(m.get("ticker") or "")).lower()
    if any(k in cat for k in ["crypto", "cryptocurrency"]) or any(k in text for k in ["bitcoin", "btc", "ethereum", "ether", "crypto", "solana"]):
        return "Criptomonedas"
    if any(k in cat for k in ["politic", "election"]) or any(k in text for k in ["election", "president", "congress", "senate", "vote", "governor", "primary"]):
        return "Política"
    if "sport" in cat or any(k in text for k in ["nfl", "nba", "mlb", "nhl", "wnba", "soccer", "football", "basketball", "super bowl", "world cup"]):
        return "Deportes"
    if any(k in cat for k in ["economic", "economy", "financial"]) or any(k in text for k in ["inflation", "federal reserve", "fed rate", "interest rate", "gdp", "jobs report", "unemployment"]):
        return "Economía"
    return "Otros"

@st.cache_data(ttl=60, show_spinner=False)
def fetch_markets(max_pages):
    all_markets, cursor = [], None
    for _ in range(max_pages):
        params = {"status": "open", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        response = requests.get(f"{API}/markets", params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        all_markets.extend(payload.get("markets", []))
        cursor = payload.get("cursor")
        if not cursor:
            break
        time.sleep(0.15)
    return all_markets

def to_row(m):
    yb = num(m.get("yes_bid_dollars"))
    ya = num(m.get("yes_ask_dollars"))
    nb = num(m.get("no_bid_dollars"))
    na = num(m.get("no_ask_dollars"))
    vol = num(m.get("volume_24h_fp"))
    if vol is None:
        vol = num(m.get("volume_24h")) or 0
    spread = ya-yb if ya is not None and yb is not None else None
    mid = (ya+yb)/2 if ya is not None and yb is not None else None
    return {
        "Categoría": classify(m),
        "Mercado": m.get("title") or "Sin título",
        "Ticker": m.get("ticker") or "",
        "YES bid": yb, "YES ask": ya,
        "NO bid": nb, "NO ask": na,
        "Prob. implícita YES (%)": round(mid*100, 1) if mid is not None else None,
        "Spread YES": round(spread, 4) if spread is not None else None,
        "Volumen 24h": vol,
        "Cierre": m.get("close_time") or "",
        "URL": "https://kalshi.com/markets/" + str(m.get("ticker") or "")
    }

col1, col2, col3 = st.columns(3)
col1.metric("Modo", "Solo lectura")
col2.metric("Umbral de observación", f"{min_volume:,} contratos")
col3.metric("Spread máximo", f"{max_spread:.0%}")

try:
    with st.spinner("Consultando mercados públicos de Kalshi..."):
        markets = fetch_markets(pages)
    rows = [to_row(m) for m in markets]
    df = pd.DataFrame(rows)
    if df.empty:
        st.warning("Kalshi no devolvió mercados abiertos en esta consulta. Intenta actualizar.")
        st.stop()

    filtered = df[df["Categoría"].isin(category_filter)].copy()
    filtered["Volumen 24h"] = pd.to_numeric(filtered["Volumen 24h"], errors="coerce").fillna(0)
    filtered["Candidato de observación"] = (
        (filtered["Volumen 24h"] >= min_volume) &
        filtered["Spread YES"].notna() &
        (filtered["Spread YES"] <= max_spread)
    )
    candidates = filtered[filtered["Candidato de observación"]].sort_values(
        ["Volumen 24h"], ascending=False
    )

    a, b, c, d = st.columns(4)
    a.metric("Mercados descargados", f"{len(df):,}")
    b.metric("En categorías elegidas", f"{len(filtered):,}")
    c.metric("Candidatos para revisar", f"{len(candidates):,}")
    d.metric("Última consulta UTC", datetime.now(timezone.utc).strftime("%H:%M:%S"))

    st.subheader("📊 Mercados por categoría")
    summary = filtered.groupby("Categoría").size().reset_index(name="Mercados")
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.subheader("🔎 Candidatos de observación")
    st.caption("Ordenados por volumen. Ser candidato no significa que sea una apuesta recomendada.")
    display_cols = ["Categoría", "Mercado", "Ticker", "YES bid", "YES ask", "NO bid", "NO ask",
                    "Prob. implícita YES (%)", "Spread YES", "Volumen 24h", "Cierre", "URL"]
    st.dataframe(candidates[display_cols].head(100), use_container_width=True, hide_index=True,
                 column_config={"URL": st.column_config.LinkColumn("Kalshi")})

    with st.expander("Ver todos los mercados filtrados"):
        st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True,
                     column_config={"URL": st.column_config.LinkColumn("Kalshi")})

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar resultados CSV", csv, "JORDAN_TC_scanner.csv", "text/csv")

    st.info("La probabilidad implícita es una lectura aproximada del precio YES (promedio bid/ask), no una predicción independiente. Este escáner aún no calcula probabilidades propias ni demuestra una tasa de acierto del 65%.")
except requests.HTTPError as e:
    st.error(f"Kalshi respondió con un error HTTP: {e}")
except requests.RequestException as e:
    st.error(f"No se pudo conectar con Kalshi: {e}. Comprueba tu conexión e inténtalo de nuevo.")
except Exception as e:
    st.error(f"Error inesperado: {e}")

st.divider()
st.caption("JORDAN TC · Herramienta informativa y experimental. No garantiza ganancias. Verifica precios, liquidez, reglas y comisiones directamente en Kalshi antes de tomar decisiones.")
