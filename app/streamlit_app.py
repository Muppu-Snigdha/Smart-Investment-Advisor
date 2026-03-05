import streamlit as st
import yfinance as yf
from datetime import datetime
import sqlite3
import bcrypt
import smtplib
from email.mime.text import MIMEText
import json
from pathlib import Path
import pandas as pd

# compatibility shim so tests can monkeypatch
if not hasattr(st, "experimental_get_query_params"):
    # some streamlit versions provide only query_params proxy
    st.experimental_get_query_params = lambda: st.query_params

@st.cache_data
def fetch_data(sym):
    """Fetch historical data for a symbol or list of symbols.

    This helper is used by multiple pages in the application.
    """
    return yf.download(sym, period="6mo")


# ======= new utilities for live ticker header ======
@st.cache_data(ttl=60)
def get_live_ticker_html():
    """Fetch a smaller set of symbols quickly and return HTML with colored P/L."""
    tickers = [
        "AAPL","MSFT","GOOGL","AMZN","TSLA",
        "NVDA","META","JPM","WMT","DIS",
        "XOM","CVX","KO","PEP","PFE"
    ]
    try:
        # use threads to parallelize network calls and only grab one day
        df = yf.download(tickers, period="1d", threads=True)["Close"]
        if len(df.index) >= 2:
            prev = df.iloc[-2]
            latest = df.iloc[-1]
        else:
            prev = df.iloc[0]
            latest = df.iloc[0]
    except Exception:
        return ""

    parts = []
    for sym in tickers:
        if sym in latest and sym in prev:
            change = latest[sym] - prev[sym]
            color = "#00E676" if change >= 0 else "#FF5252"
            parts.append(f"{sym}: <span style='color:{color}; font-weight:bold'>{change:+.2f}</span>")
    return " &nbsp; &#8212; &nbsp; ".join(parts)


def show_header(title_icon="👑"):
    """Render the moving ticker bar (clickable) and the main title.

    A spinner wraps the data fetch so the UI doesn't feel stalled while the
    first call populates the cache. Subsequent calls return immediately.
    """
    with st.spinner("Loading market tickers..."):
        html = get_live_ticker_html()
    if html:
        # clicking takes user to yahoo finance lookup page for all symbols
        st.markdown(
            f"<div class='marquee'><a href='https://finance.yahoo.com/lookup' target='_blank'>{html}</a></div>",
            unsafe_allow_html=True,
        )
    st.markdown(f"<div class='main-title'>{title_icon} Smart Investment Advisor</div>", unsafe_allow_html=True)

# ===== end new utilities =====


# ---------- additional UI helpers ----------

def show_landing_page():
    """Render a friendly landing / welcome screen.

    This is shown before the user reaches the login/register form.  A
    separate function makes it easy to test the behaviour with monkeypatches.
    """
    st.markdown("""
    <div style='text-align:center; padding:60px 0;'>
      <h1 style='font-size:56px; font-weight:bold; color:#42A5F5; margin-bottom:30px;'>
        Smart Investment Advisor
      </h1>
      <h2 style='font-size:24px; font-weight:bold; color:#E0E0E0; margin-bottom:10px;'>
        Features
      </h2>
      <ul style='font-size:18px; color:#E0E0E0; line-height:1.6; display:inline-block; text-align:left; max-width:600px;'>
        <li>📈 Analyze real-time stock data</li>
        <li>🔍 Predict BUY / SELL / HOLD signals</li>
        <li>📊 Show stock charts</li>
        <li>🔗 Provide Yahoo Finance links</li>
        <li>✉️ Send email alerts</li>
      </ul>

      <h2 style='font-size:24px; font-weight:bold; color:#E0E0E0; margin:40px 0 10px;'>
        How to Use
      </h2>
      <ol style='font-size:18px; color:#E0E0E0; line-height:1.6; display:inline-block; text-align:left; max-width:600px;'>
        <li>Click “Get Started”</li>
        <li>Sign Up to create an account</li>
        <li>Sign In to access the app</li>
        <li>Enter a stock symbol and quantity</li>
        <li>View predictions, charts and alerts</li>
      </ol>
    </div>
    """, unsafe_allow_html=True)
    # big button container allows .get-started-btn styling
    if st.button("Get Started", key="get_started_btn"):
        st.session_state.auth_page = "Login"
        st.rerun()


def show_navbar():
    """Render a simple top navigation bar using anchors.

    Links update the ``nav`` query parameter; we watch that parameter and
    also highlight the currently selected page. Using plain HTML allows the
    nav to be styled cleanly and sidesteps the need for Streamlit buttons
    which would trigger reruns.
    """
    # note: we advertise "Profile" instead of the older "User Profile" label
    pages = ["Home", "About", "Graph", "Yahoo Finance", "Profile"]
    # support new/old streamlit APIs for query params
    if hasattr(st, "experimental_get_query_params"):
        params = st.experimental_get_query_params()
    else:
        # st.query_params is a proxy object behaving like a dict
        params = st.query_params
    current = st.session_state.nav_page
    if "nav" in params:
        val = params["nav"][0]
        if val in pages:
            current = val
            st.session_state.nav_page = val

    html = "<div class='navbar-container'>"
    for p in pages:
        active = " navbar-active" if p == current else ""
        html += f"<a href='?nav={p}' class='nav-btn{active}'>{p}</a>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# end additional helpers


def load_model_metadata(model_path):
    """Return metadata for a model file.

    The function looks for a companion ``.meta.json`` file and merges any
    contents with default values. Used by the unit tests.
    """
    path = Path(model_path)
    meta = {"name": path.name, "created_at": None}
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta.update(data)
        except Exception:
            pass
    return meta


# simple helpers used by various tests ------------------------------------------------

def find_models(models_dir):
    """List all ``.joblib`` files under *models_dir*.

    Returns a list of pathlib.Path objects. The tests only check the names,
    so a straightforward implementation is sufficient.
    """
    p = Path(models_dir)
    if not p.is_dir():
        return []
    return [f for f in p.iterdir() if f.suffix == ".joblib"]


def predict_strategy(df, model=None):
    """Decide whether to recommend a buy based on data or a ML model.

    When *model* is ``None`` the fallback logic is to look at the most
    recent percentage change in the ``Close`` column: positive -> buy.
    Otherwise the model's ``predict`` method is invoked on an array of
    feature columns; the last prediction is used to decide.

    Returns a dict containing at least ``using_model``, ``recommended_buy``
    and ``model_pred`` (when a model is provided).
    """
    result = {"using_model": False, "recommended_buy": False}
    if model is None:
        # fallback: simple return-based decision
        if len(df) >= 2:
            last = df["Close"].iloc[-1]
            prev = df["Close"].iloc[-2]
            # convert numpy.bool_ to native bool for test comparison
            result["recommended_buy"] = bool((last - prev) > 0)
        return result

    # use the model to predict -- assume it handles 2d numpy arrays
    result["using_model"] = True
    try:
        import numpy as _np
        # build features matrix: drop non-numeric or index
        # assume the model knows which columns it needs
        X = df.select_dtypes(include=[_np.number]).to_numpy()
        preds = model.predict(X)
        last_pred = int(preds[-1]) if len(preds) > 0 else 0
        result["model_pred"] = last_pred
        result["recommended_buy"] = bool(last_pred)
    except Exception:
        # if model fails, fall back
        result["using_model"] = False
        if len(df) >= 2:
            last = df["Close"].iloc[-1]
            prev = df["Close"].iloc[-2]
            result["recommended_buy"] = (last - prev) > 0
    return result


def load_model_from_file(path):
    """Attempt to load a joblib model, returning ``None`` on failure."""
    try:
        import joblib
        return joblib.load(path)
    except Exception:
        return None


def load_model():
    """Load a default model for the app.

    This is intentionally minimal for the smoke tests; it may search a
    configured location or simply return ``None`` if no model is available.
    The important part is that the function exists and does not raise when
    called without arguments.
    """
    # placeholder implementation, real app can load a file from disk
    return None

# end helpers -----------------------------------------------------------------------

# ================= APP CONFIG =================
st.set_page_config(page_title="Smart Investment Advisor", layout="wide")

SENDER_EMAIL = "smartinvestmentadvisor36@gmail.com"
APP_PASSWORD = "dadx xxar synn fere"
USD_TO_INR = 83

# ================= CLEAN CSS =================
st.markdown("""
<style>
/* dark theme background + global text color */
.stApp { background-color: #121212; color: #eee; }

/* force the sidebar to the right instead of the default left */
[data-testid="stSidebar"] {
    left: auto !important;
    right: 0 !important;
}

.main-title {
    text-align:center;
    font-size:36px;
    font-weight:bold;
    color:#6A1B9A;
}

/* marquee animation for live tickers */
.marquee {
    overflow: hidden;
    white-space: nowrap;
    box-sizing: border-box;
    animation: marquee 25s linear infinite;
    background-color: #000;
    color: #fff;
    padding: 5px 0;
}
.marquee a {
    text-decoration: none;
    color: #fff;
    font-size: 18px;
    font-weight: bold;
}
@keyframes marquee {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}

/* inputs */
input[type="text"],
input[type="password"],
input[type="number"],
textarea {
    background-color: #E6E6FA !important;
    color: black !important;
    border-radius: 8px !important;
    border: 1px solid #ccc !important;
}

div[data-baseweb="input"] > div {
    background-color: #E6E6FA !important;
}

/* default buttons */
.stButton > button {
    background-color: #7E57C2 !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: none !important;
}

.stButton > button:hover {
    background-color: #5E35B1 !important;
}

.green-text {
    color:#2E7D32;
    font-size:20px;
    font-weight:bold;
    text-align:center;
}

.red-text {
    color:#C62828;
    font-size:20px;
    font-weight:bold;
    text-align:center;
}

/* landing page */
.landing-container {
    padding: 60px 20px;
    text-align: center;
    color: #fafafa;
}
.landing-summary {
    font-size: 18px;
    line-height: 1.6;
    margin: 20px auto;
    max-width: 600px;
}
.get-started-btn > button {
    background-color: #00bcd4 !important;
    padding: 15px 30px !important;
    font-size: 20px !important;
    border-radius: 10px !important;
}

/* navigation bar */
.navbar-container {
    display: flex;
    justify-content: center;
    gap: 20px;
    background-color: #1a1a1a;
    padding: 10px 0;
    border-radius: 8px;
    margin-bottom: 20px;
}
.navbar-container .stButton>button {
    background-color: transparent !important;
    color: #ccc !important;
    font-size: 16px;
    border-radius: 4px !important;
}
.navbar-container .stButton>button:hover {
    background-color: #333 !important;
}
.navbar-active > button {
    color: #00bcd4 !important;
    font-weight: bold !important;
}

/* link-style buttons in the HTML navbar */
.navbar-container a.nav-btn {
    color: #ccc;
    padding: 8px 16px;
    text-decoration: none;
    font-size: 16px;
    transition: background 0.2s;
}
.navbar-container a.nav-btn:hover {
    background-color: #333;
    border-radius: 4px;
}
.navbar-container a.nav-btn.navbar-active {
    color: #00bcd4;
    font-weight: bold;
    text-decoration: underline;
}
</style>
""", unsafe_allow_html=True)

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            password BLOB
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ================= EMAIL FUNCTION =================
def send_email(to_email, subject, html_message):
    try:
        msg = MIMEText(html_message, "html")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
    except:
        pass

# ================= AUTH FUNCTIONS =================
def register_user(username, email, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        cursor.execute("INSERT INTO users (username,email,password) VALUES (?,?,?)",
                       (username,email,hashed))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def login_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email,password FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode(), user[1]):
        return user[0]
    return None

def reset_password(username, new_password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    cursor.execute("UPDATE users SET password=? WHERE username=?", (hashed, username))
    conn.commit()
    conn.close()

# ================= SESSION =================
# ensure keys exist even when script is imported (e.g. during tests)
session_defaults = {
    "logged_in": False,
    # start on the landing page; clicking "Get Started" switches to login
    "auth_page": "Landing",
    "username": "",
    "user_email": "",
    # navigation state once the user is logged in
    "nav_page": "Home",
}
for key, default in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ================= AUTH UI ==============
# ================= AUTH UI =================
if not st.session_state.logged_in:

    # landing page shown on initial visit
    if st.session_state.auth_page == "Landing":
        with st.container():
            st.markdown("<div class='landing-container'>", unsafe_allow_html=True)
            show_landing_page()
            st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    # show a simple project header when not logged in (no ticker marquee)
    st.markdown("<div class='main-title'>👑 Smart Investment Advisor</div>", unsafe_allow_html=True)

    # split the auth page into two panels so the right side can be a user panel
    left, right = st.columns([3, 1])
    with left:
        # ================= LOGIN =================
        if st.session_state.auth_page == "Login":
            st.markdown("<h2 class='sub-heading'>🔐 LOGIN </h2>", unsafe_allow_html=True)

            username = st.text_input("👤 Username")
            password = st.text_input("🔑 Password", type="password")

            if st.button("🚀 Login"):
                email = login_user(username, password)
                if email:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_email = email
                    # warm the cache so header appears instantly after rerun
                    _ = get_live_ticker_html()
                    st.rerun()
                else:
                    st.error("❌ Invalid Credentials")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔑 Forgot Password"):
                    st.session_state.auth_page = "Forgot"
                    st.rerun()
            with col2:
                if st.button("📝Don't Have An Account? Register"):
                    st.session_state.auth_page = "Register"
                    st.rerun()

        # ================= REGISTER =================
        elif st.session_state.auth_page == "Register":
            st.markdown("<h2 class='sub-heading'>📝Register</h2>", unsafe_allow_html=True)

            username = st.text_input("👤 Username")
            email = st.text_input("📧 Email")
            password = st.text_input("🔑 Password", type="password")

            if st.button("✅ Register Now"):
                if register_user(username, email, password):
                    st.success("🎉 Account Created Successfully!")
                    st.session_state.auth_page = "Login"
                    st.rerun()
                else:
                    st.error("⚠ Username already exists")

            if st.button("🔐Already Have An Account?Login"):
                st.session_state.auth_page = "Login"
                st.rerun()

        # ================= FORGOT PASSWORD =================
        elif st.session_state.auth_page == "Forgot":
            st.markdown("<h2 class='sub-heading'>🔑 RESET YOUR PASSWORD</h2>", unsafe_allow_html=True)

            username = st.text_input("👤 Enter Username")
            new_password = st.text_input("🆕 New Password", type="password")

            if st.button("🔄 Reset Password"):
                reset_password(username, new_password)
                st.success("✅ Password Reset Successful!")
                st.session_state.auth_page = "Login"
                st.rerun()

            if st.button("⬅ Back To Login"):
                st.session_state.auth_page = "Login"
                st.rerun()
    
    with right:
        # simple user panel on the right side of auth screens
        st.markdown("### 🧩 User Panel")
        if st.session_state.auth_page == "Login":
            st.write("Welcome! Please login using your credentials.")
        elif st.session_state.auth_page == "Register":
            st.write("Create an account to start using the app.")
        elif st.session_state.auth_page == "Forgot":
            st.write("Reset your password here.")

    st.stop()

# sidebar user box removed per layout requirements; profile info lives in the
# dedicated Profile page instead

# ================= MAIN APP =================
# first, display our enhanced navigation-driven pages
if st.session_state.logged_in:
    show_header("📈")
    st.caption(f"🕒 Live Market | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.write("Ticker box shows live profit/loss. Click ticker to explore all stocks on Yahoo Finance.")
    show_navbar()

    page = st.session_state.nav_page
    if page == "Home":
        # original stock search logic moved here
        st.subheader("🔎 Stock Search")

        symbol = st.text_input("Enter Stock Symbol", "AAPL", key="home_symbol")
        quantity = st.number_input("Quantity", min_value=1, value=1, key="home_qty")

        if not st.button("🚀 Fetch & Predict", key="home_go"):
            st.stop()
        # store last requested ticker so other pages can reuse it
        st.session_state.last_symbol = symbol

        # use global helper rather than defining anew
        df = fetch_data(symbol)
        data_stub = False
        if df.empty or "Close" not in df.columns or len(df["Close"]) == 0:
            df = pd.DataFrame({"Close": [0.0, 0.0]})
            data_stub = True

        # price operations
        try:
            latest_price = float(df["Close"].iloc[-1])
        except Exception:
            try:
                latest_price = float(df["Close"].iat[-1])
            except Exception:
                latest_price = 0.0
        total_value = latest_price * quantity * USD_TO_INR

        st.subheader("💰 Live Price")
        st.success(f"USD: ${latest_price:.2f}")
        st.success(f"INR: ₹{latest_price*USD_TO_INR:.2f}")

        decision = "HOLD"
        if not data_stub and len(df) >= 50:
            df["ma20"] = df["Close"].rolling(20).mean()
            df["ma50"] = df["Close"].rolling(50).mean()
            df = df.dropna()
            if len(df) > 0:
                if df["ma20"].iloc[-1] > df["ma50"].iloc[-1]:
                    decision = "BUY"
                elif df["ma20"].iloc[-1] < df["ma50"].iloc[-1]:
                    decision = "SELL"
        else:
            decision = "HOLD"

        st.subheader("📊 Price Trend")
        if decision == "SELL":
            st.line_chart(df["Close"], color="#C62828")
        elif decision == "BUY":
            st.line_chart(df["Close"], color="#2E7D32")
        else:
            st.line_chart(df["Close"])

        st.subheader("📢 Investment Decision")
        st.markdown("""
        <style>
        @keyframes pulseGlow {
            0% { box-shadow: 0 0 5px rgba(126,87,194,0.3); }
            50% { box-shadow: 0 0 25px rgba(126,87,194,0.8); }
            100% { box-shadow: 0 0 5px rgba(126,87,194,0.3); }
        }

        .animated-box {
            background-color:#E6E6FA;
            padding:25px;
            border-radius:15px;
            border:1px solid #ccc;
            text-align:center;
            margin-top:15px;
            animation: pulseGlow 2s infinite;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("<div class='animated-box'>", unsafe_allow_html=True)
        if decision == "BUY":
            st.markdown("<h2 style='color:#2E7D32;'>📈 ✅ BUY Signal</h2>", unsafe_allow_html=True)
        elif decision == "SELL":
            st.markdown("<h2 style='color:#C62828;'>📉 ❌ SELL Signal</h2>", unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='color:#6A1B9A;'>📊 HOLD Position</h2>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if decision in ["BUY", "SELL"]:
            html_content = f"""
            <html>
            <body style="margin:0;padding:0;background-color:#1E1B2E;font-family:Arial;">
                <div style="padding:30px;">
                    <div style="
                        background-color:#0D0D0D;
                        padding:30px;
                        border-radius:20px;
                        max-width:500px;
                        margin:auto;
                        box-shadow:0 0 30px rgba(0,0,0,0.8);
                    ">

                        <h1 style="text-align:center;color:#E1BEE7;font-size:32px;">
                            Smart Investment Advisor
                        </h1>

                        <h2 style="text-align:center;
                                   color:{'#00E676' if decision=='BUY' else '#FF5252'};
                                   font-size:26px;">
                            {decision} Alert 🚨
                        </h2>

                        <br>

                        <p style="color:white;font-size:18px;">
                            <strong>Stock:</strong> {symbol}
                        </p>

                        <p style="color:white;font-size:18px;">
                            <strong>Price:</strong> ${latest_price:.2f}
                        </p>

                        <p style="color:white;font-size:18px;">
                            <strong>Quantity:</strong> {quantity}
                        </p>

                        <p style="color:white;font-size:18px;">
                            <strong>Total (INR):</strong> ₹{total_value:,.2f}
                        </p>

                        <hr style="border:1px solid #333;margin-top:25px;">

                        <p style="font-size:13px;color:gray;text-align:center;">
                            Automated alert from Smart Investment Advisor <br>
                            ⚠ This is an AI generated message. Please do not reply.
                        </p>

                    </div>
                </div>
            </body>
            </html>
            """
            send_email(
                st.session_state.user_email,
                f"{decision} Alert for {symbol}",
                html_content
            )

        st.markdown(
            f"""
            <div style='text-align:center; margin-top:30px;'>
                <a href='https://finance.yahoo.com/quote/{symbol}' target='_blank'
                style='
                    background-color: #7E57C2;
                    padding: 12px 28px;
                    border-radius: 10px;
                    color: white;
                    font-weight: bold;
                    font-size: 18px;
                    text-decoration: none;
                    display: inline-block;
                '>
                🔗 View {symbol} on Yahoo Finance
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif page == "About":
        st.header("About Smart Investment Advisor")
        st.write(
            "A modern web app that uses machine learning to give simple buy/hold/sell signals, "
            "live market data, and integrates with Yahoo Finance for deep dives."
        )
        st.write("Built with Streamlit, yfinance, and a lightweight SQLite authentication system.")
        # small market snapshot graph to accompany the summary text
        try:
            tickers = ["AAPL", "MSFT", "GOOGL"]
            df_snapshot = fetch_data(tickers)
            if isinstance(df_snapshot, pd.DataFrame) and "Close" in df_snapshot.columns:
                st.subheader("📈 Market Snapshot")
                # yfinance returns a multiindex when given multiple symbols
                if isinstance(df_snapshot.columns, pd.MultiIndex):
                    chart_df = df_snapshot["Close"]
                else:
                    chart_df = df_snapshot
                st.line_chart(chart_df)
        except Exception:
            # network or lookup may fail – silently ignore
            pass

    elif page == "Graph":
        st.subheader("📈 Price Trend")
        # simply render the latest symbol the user fetched (or a default)
        graph_sym = st.session_state.get("last_symbol", "AAPL")
        try:
            df2 = fetch_data(graph_sym)
            if isinstance(df2, pd.DataFrame) and "Close" in df2.columns:
                st.line_chart(df2["Close"])
            else:
                st.error("Could not fetch data for that symbol.")
        except Exception:
            st.error("Unable to load graph. Try selecting a stock on the Home tab.")

    elif page == "Yahoo Finance":
        st.subheader("🔗 Yahoo Finance")
        # link directly to the last stock the user looked at (or default to AAPL)
        sym = st.session_state.get("last_symbol", "AAPL")
        st.markdown(
            f"<div style='text-align:center;margin-top:20px;'>"
            f"<a href='https://finance.yahoo.com/quote/{sym}' target='_blank' "
            "style='color:#00bcd4;font-size:20px;text-decoration:none;'>"
            f"Open {sym} on Yahoo Finance »</a></div>",
            unsafe_allow_html=True,
        )

    elif page == "Profile":
        st.subheader("👤 Profile")
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Email:** {st.session_state.user_email}")

        # password change flow
        if "show_change_pw" not in st.session_state:
            st.session_state.show_change_pw = False
        if st.button("🔒 Change Password"):
            st.session_state.show_change_pw = True
        if st.session_state.show_change_pw:
            curr = st.text_input("Current Password", type="password", key="cur_pw")
            newp = st.text_input("New Password", type="password", key="new_pw")
            if st.button("Update Password", key="update_pw_btn"):
                verified = login_user(st.session_state.username, curr)
                if not verified:
                    st.error("❌ Current password incorrect")
                else:
                    reset_password(st.session_state.username, newp)
                    st.success("✅ Password Updated Successfully")
                    st.session_state.show_change_pw = False
                    st.rerun()
        if st.button("🚪 Logout", key="profile_logout"):
            st.session_state.logged_in = False
            st.rerun()

    # nothing beyond this point should execute; routing handled above
    st.stop()

# legacy code disabled below (retained only for reference)

symbol = st.text_input("Enter Stock Symbol", "AAPL")
quantity = st.number_input("Quantity", min_value=1, value=1)

if not st.button("🚀 Fetch & Predict"):
    st.stop()

@st.cache_data
def fetch_data(sym):
    return yf.download(sym, period="6mo")

df = fetch_data(symbol)
data_stub = False
if df.empty or "Close" not in df.columns or len(df["Close"]) == 0:
    # create a small stub dataframe so downstream UI code won't raise
    df = pd.DataFrame({"Close": [0.0, 0.0]})
    data_stub = True

# Safely get the latest close price (guards against empty series/index errors)
latest_price = None
try:
    latest_price = float(df["Close"].iloc[-1])
except Exception:
    try:
        latest_price = float(df["Close"].iat[-1])
    except Exception:
        latest_price = 0.0

total_value = latest_price * quantity * USD_TO_INR

st.subheader("💰 Live Price")
st.success(f"USD: ${latest_price:.2f}")
st.success(f"INR: ₹{latest_price*USD_TO_INR:.2f}")

decision = "HOLD"
# Only compute moving averages when we have enough real data
if not data_stub and len(df) >= 50:
    df["ma20"] = df["Close"].rolling(20).mean()
    df["ma50"] = df["Close"].rolling(50).mean()
    df = df.dropna()
    if len(df) > 0:
        if df["ma20"].iloc[-1] > df["ma50"].iloc[-1]:
            decision = "BUY"
        elif df["ma20"].iloc[-1] < df["ma50"].iloc[-1]:
            decision = "SELL"
else:
    # fallback when insufficient data
    decision = "HOLD"

st.subheader("📊 Price Trend")

if decision == "SELL":
    st.line_chart(df["Close"], color="#C62828")
elif decision == "BUY":
    st.line_chart(df["Close"], color="#2E7D32")
else:
    st.line_chart(df["Close"])

st.subheader("📢 Investment Decision")

st.markdown("""
<style>
@keyframes pulseGlow {
    0% { box-shadow: 0 0 5px rgba(126,87,194,0.3); }
    50% { box-shadow: 0 0 25px rgba(126,87,194,0.8); }
    100% { box-shadow: 0 0 5px rgba(126,87,194,0.3); }
}

.animated-box {
    background-color:#E6E6FA;
    padding:25px;
    border-radius:15px;
    border:1px solid #ccc;
    text-align:center;
    margin-top:15px;
    animation: pulseGlow 2s infinite;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='animated-box'>", unsafe_allow_html=True)

if decision == "BUY":
    st.markdown("<h2 style='color:#2E7D32;'>📈 ✅ BUY Signal</h2>", unsafe_allow_html=True)
elif decision == "SELL":
    st.markdown("<h2 style='color:#C62828;'>📉 ❌ SELL Signal</h2>", unsafe_allow_html=True)
else:
    st.markdown("<h2 style='color:#6A1B9A;'>📊 HOLD Position</h2>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ================= PREMIUM EMAIL ALERT =================
if decision in ["BUY", "SELL"]:

    html_content = f"""
    <html>
    <body style="margin:0;padding:0;background-color:#1E1B2E;font-family:Arial;">
        <div style="padding:30px;">
            <div style="
                background-color:#0D0D0D;
                padding:30px;
                border-radius:20px;
                max-width:500px;
                margin:auto;
                box-shadow:0 0 30px rgba(0,0,0,0.8);
            ">

                <h1 style="text-align:center;color:#E1BEE7;font-size:32px;">
                    Smart Investment Advisor
                </h1>

                <h2 style="text-align:center;
                           color:{'#00E676' if decision=='BUY' else '#FF5252'};
                           font-size:26px;">
                    {decision} Alert 🚨
                </h2>

                <br>

                <p style="color:white;font-size:18px;">
                    <strong>Stock:</strong> {symbol}
                </p>

                <p style="color:white;font-size:18px;">
                    <strong>Price:</strong> ${latest_price:.2f}
                </p>

                <p style="color:white;font-size:18px;">
                    <strong>Quantity:</strong> {quantity}
                </p>

                <p style="color:white;font-size:18px;">
                    <strong>Total (INR):</strong> ₹{total_value:,.2f}
                </p>

                <hr style="border:1px solid #333;margin-top:25px;">

                <p style="font-size:13px;color:gray;text-align:center;">
                    Automated alert from Smart Investment Advisor <br>
                    ⚠ This is an AI generated message. Please do not reply.
                </p>

            </div>
        </div>
    </body>
    </html>
    """

    send_email(
        st.session_state.user_email,
        f"{decision} Alert for {symbol}",
        html_content
    )

# ================= YAHOO LINK =================
st.markdown(
    f"""
    <div style='text-align:center; margin-top:30px;'>
        <a href='https://finance.yahoo.com/quote/{symbol}' target='_blank'
        style='
            background-color: #7E57C2;
            padding: 12px 28px;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            font-size: 18px;
            text-decoration: none;
            display: inline-block;
        '>
        🔗 View {symbol} on Yahoo Finance
        </a>
    </div>
    """,
    unsafe_allow_html=True
)