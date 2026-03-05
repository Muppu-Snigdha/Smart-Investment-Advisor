import streamlit as st
import yfinance as yf
from datetime import datetime
import sqlite3
import bcrypt
import smtplib
import random
from email.mime.text import MIMEText
import os

import pandas as pd

# ================= APP CONFIG =================
st.set_page_config(page_title="Smart Investment Advisor", layout="wide")

SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]
USD_TO_INR = 83

# content for the About tab (reused below)
ABOUT_TEXT = """
<div style='text-align:center; padding:60px 0;'>
  <h1 style='font-size:48px; font-weight:bold; color:#42A5F5; margin-bottom:30px;'>
    Smart Investment Advisor
  </h1>
  <h2 style='font-size:22px; font-weight:bold; color:#E0E0E0; margin-bottom:10px;'>
    Features
  </h2>
  <ul style='font-size:16px; color:#E0E0E0; line-height:1.6; display:inline-block; text-align:left; max-width:600px;'>
    <li>📈 Analyze real-time stock data</li>
    <li>🔍 Predict BUY / SELL / HOLD signals</li>
    <li>📊 Show stock charts</li>
    <li>🔗 Provide Yahoo Finance links</li>
    <li>✉️ Send email alerts</li>
  </ul>

  <h2 style='font-size:22px; font-weight:bold; color:#E0E0E0; margin:40px 0 10px;'>
    How to Use
  </h2>
  <ol style='font-size:16px; color:#E0E0E0; line-height:1.6; display:inline-block; text-align:left; max-width:600px;'>
    <li>Click “Get Started”</li>
    <li>Sign Up to create an account</li>
    <li>Sign In to access the app</li>
    <li>Enter a stock symbol & quantity</li>
    <li>View predictions, charts and email alerts</li>
  </ol>
</div>
"""

# ================= CLEAN CSS =================
st.markdown("""
<style>

/* ================= GLOBAL DARK BACKGROUND ================= */
.stApp {
    background-color: #0E1117;
    color: #FFFFFF;
}

/* ================= FIX CONTENT WIDTH ================= */
.block-container {
    max-width: 1200px;
    margin: auto;
    padding-top: 2rem;
}

/* Remove horizontal scroll */
html, body {
    overflow-x: hidden;
}

/* ================= MAIN TITLE ================= */
.main-title {
    text-align: center;
    font-size: 38px;
    font-weight: bold;
    color: #42A5F5;
    margin-bottom: 10px;
}

/* ==== ticker marquee ==== */
.marquee {
    overflow: hidden;
    white-space: nowrap;
    box-sizing: border-box;
    animation: marquee 25s linear infinite;
    background-color: #1F1F2E;
    padding: 5px 0;
}
.marquee a {
    text-decoration: none;
    color: #FFFFFF;
    font-size: 18px;
    font-weight: bold;
}
@keyframes marquee {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}

.stTabs [data-baseweb="tab-list"] {
    justify-content: center;
    gap: 20px;
}

.stTabs [data-baseweb="tab"] {
    background: #1F1F2E;
    border-radius: 12px;
    padding: 12px 25px;
    font-weight: bold;
    font-size: 16px;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg,#1976D2,#42A5F5);
}

/* ================= HEADINGS ================= */
h1, h2, h3, h4, h5, h6 {
    color: #FFFFFF !important;
}

p, label, span {
    color: #E0E0E0 !important;
}

/* ================= INPUT FIELDS ================= */
input[type="text"],
input[type="password"],
input[type="number"],
textarea {
    background-color: #1F1F2E !important;
    color: white !important;
    border-radius: 8px !important;
    border: 1px solid #333 !important;
}

/* Streamlit internal wrapper fix */
div[data-baseweb="input"] > div {
    background-color: #1F1F2E !important;
}

/* ================= BLUE BUTTON THEME ================= */
.stButton > button {
    background: linear-gradient(90deg, #1976D2, #42A5F5) !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 20px !important;
    transition: 0.3s ease-in-out !important;
}

/* Hover Effect */
.stButton > button:hover {
    background: linear-gradient(90deg, #1565C0, #1E88E5) !important;
    transform: scale(1.03);
}

/* ================ LANDING PAGE STYLES ================ */
.landing-container {
    text-align:center;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    height:100vh;
    padding:20px;
}
.landing-container h1 {
    font-size:60px;
    font-weight:900;
    color:#42A5F5;
    margin-bottom:10px;
}
.landing-container h3 {
    font-size:28px;
    font-weight:bold;
    color:white;
    margin-top:30px;
}
.landing-container p {
    font-size:20px;
    max-width:850px;
    margin:auto;
    color:#E0E0E0;
    line-height:1.8;
}

/* ================= SIDEBAR DARK ================= */
section[data-testid="stSidebar"] {
    background-color: #161625 !important;
}

/* ================= SUCCESS / ERROR COLORS ================= */
.green-text {
    color: #00E676;
    font-size: 20px;
    font-weight: bold;
    text-align: center;
}

.red-text {
    color: #FF5252;
    font-size: 20px;
    font-weight: bold;
    text-align: center;
}

/* ================= SUBHEADERS ================= */
.sub-heading {
    color: #42A5F5;
    text-align: center;
    margin-bottom: 15px;
}

/* ================= LINKS ================= */
a {
    color: #42A5F5 !important;
    text-decoration: underline !important;
}

a:hover {
    color: #90CAF9 !important;
}

/* ================= FIX LINK BUTTON BLUE ================= */

div[data-testid="stLinkButton"] > a {
    background: linear-gradient(90deg, #1976D2, #42A5F5) !important;
    color: white !important;
    font-weight: bold !important;
    padding: 12px 28px !important;
    border-radius: 12px !important;
    text-decoration: none !important;
    display: inline-block !important;
    box-shadow: 0 0 15px rgba(66,165,245,0.6);
    transition: 0.3s ease;
}

div[data-testid="stLinkButton"] > a:hover {
    background: linear-gradient(90deg, #1565C0, #1E88E5) !important;
    transform: scale(1.05);
}

</style>
""", unsafe_allow_html=True)



# ======= utilities for live header =====

@st.cache_data(ttl=60)
def get_live_ticker_html():
    # smaller set of around 15 well‑known stocks for performance
    tickers = [
        "AAPL","MSFT","GOOGL","AMZN","TSLA",
        "NVDA","META","JPM","WMT","DIS",
        "XOM","CVX","KO","PEP","PFE"
    ]
    try:
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


def show_header(title="🚀"):
    # perform the fetch inside a spinner so the user sees immediate feedback on
    # slow network calls; cached result makes subsequent renders fast.
    with st.spinner("Loading market tickers..."):
        html = get_live_ticker_html()
    if html:
        st.markdown(
            f"<div class='marquee'><a href='?page=stocks'>{html}</a></div>",
            unsafe_allow_html=True,
        )
    st.markdown(f"<h1 style='text-align:center;'>{title} Smart Investment Advisor</h1>", unsafe_allow_html=True)

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

# helper functions for portfolio / watchlist storage

def add_to_portfolio(username, symbol, quantity, price):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO portfolio (username, symbol, quantity, price) VALUES (?,?,?,?)",
                   (username, symbol, quantity, price))
    conn.commit()
    conn.close()

def get_portfolio(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, quantity, price FROM portfolio WHERE username=?", (username,))
    results = cursor.fetchall()
    conn.close()
    return results

def add_to_watchlist(username, symbol):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO watchlist (username, symbol) VALUES (?,?)", (username, symbol))
    conn.commit()
    conn.close()

def get_watchlist(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM watchlist WHERE username=?", (username,))
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

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
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_change_pw" not in st.session_state:
    st.session_state.show_change_pw = False
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "Login"
if "show_landing" not in st.session_state:
    st.session_state.show_landing = True
# ensure basic user info fields exist to avoid access errors on import
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "otp" not in st.session_state:
    st.session_state.otp = None
if "otp_verified" not in st.session_state:
    st.session_state.otp_verified = False
if "reset_user" not in st.session_state:
    st.session_state.reset_user = None



# ================= LANDING PAGE =================


if st.session_state.show_landing and "page" not in st.query_params:

    st.markdown("""
<div class="landing-container"
style="
background-image:url('https://images.unsplash.com/photo-1581091870622-c43a6e3dfa9f?auto=format&fit=crop&w=897&q=80');
background-size:cover;
background-position:center;
height:100vh;
width:100%;
display:flex;
flex-direction:column;
justify-content:center;
align-items:center;
text-align:center;
">
<h1>🚀 Smart Investment Advisor</h1>
<h3>📊 Analyze Stocks • Predict Trends • Make Smarter Investments</h3>
<br>
<p>💡 <b>Smart Investment Advisor</b> is an intelligent stock analysis platform that helps investors make better decisions using real-time stock data.<br><br>
📈 Track live stock prices with interactive charts.  
🤖 Get automated <b>BUY / SELL / HOLD</b> signals using moving averages.  
📧 Receive instant email alerts when market signals change.  
🔗 Explore detailed financial insights directly from Yahoo Finance.<br><br>
This app combines <b>data analysis, AI-based signals, and live market insights</b> to help you invest smarter and faster.
</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1,1])

    with col2:
        if st.button("🚀 Get Started"):
            st.session_state.show_landing = False
            st.rerun()

    st.stop()


# ================= QUERY PARAM ROUTING =================

query_params = st.query_params

# -------- PAGE ROUTING (Login / Register / Forgot) --------
if "page" in query_params:
    page_value = query_params["page"]

    if isinstance(page_value, list):
        page_value = page_value[0]

    page_value = page_value.lower()

    if page_value == "forgot":
        st.session_state.auth_page = "Forgot"
    elif page_value == "login":
        st.session_state.auth_page = "Login"
    elif page_value == "register":
        st.session_state.auth_page = "Register"

# -------- LOGOUT ROUTING --------
if "action" in query_params:
    action_value = query_params["action"]

    if isinstance(action_value, list):
        action_value = action_value[0]

    if action_value.lower() == "logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_email = ""
        st.rerun()


# ================= AUTH UI =================
if not st.session_state.logged_in:
    # show static project heading on starting page before sign-in
    st.markdown("<div class='main-title'>🚀 Smart Investment Advisor</div>", unsafe_allow_html=True)
    # on login/signup pages we do not render the live ticker header yet; it only appears
    # after successful authentication to avoid unnecessary network calls.

    # ================= LOGIN PAGE =================
    if st.session_state.auth_page == "Login":

        st.markdown("<h2 style='text-align:center;'>🔐 Sign In</h2>", unsafe_allow_html=True)

        username = st.text_input("Username",key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Sign In",key="login_button"):
            email = login_user(username, password)
            if email:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_email = email
                # warm cache so header is ready immediately
                _ = get_live_ticker_html()
                st.rerun()
            else:
                st.error("Invalid Credentials")

        if st.button("Sign Up",key="goto_register"):
            st.session_state.show_landing = False
            st.session_state.auth_page = "Register"
            st.query_params.clear()
            st.rerun()

        # Forgot Password (Underlined Hyperlink)
        st.markdown(
            """
            <div style='text-align:center; margin-top:10px;'>
                <a href='?page=Forgot'
                   style='
                       font-size:14px;
                       font-weight:500;
                       color:#1976D2;
                       text-decoration: underline;
                   '>
                   Forgot Password?
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ================= SIGN UP PAGE =================
    elif st.session_state.auth_page == "Register":

         st.markdown("<h2 class='sub-heading'>📝 Sign Up</h2>", unsafe_allow_html=True)

         reg_username = st.text_input("👤 Username", key="reg_user")
         reg_email = st.text_input("📧 Email", key="reg_email")
         reg_password = st.text_input("🔑 Password", type="password", key="reg_pass")

         if st.button("Sign Up", key="register_btn"):

             if reg_username == "" or reg_email == "" or reg_password == "":
                 st.warning("⚠ Please fill all fields")
             else:
                 success = register_user(reg_username, reg_email, reg_password)

                 if success:
                     st.success("🎉 Account Created Successfully!")
                     st.session_state.auth_page = "Login"
                     st.rerun()
                 else:
                     st.error("⚠ Username already exists")

         if st.button("Sign In", key="goto_login"):
            st.session_state.show_landing = False
            st.session_state.auth_page = "Login"
            st.rerun()

    # ================= FORGOT PASSWORD PAGE =================
    elif st.session_state.auth_page == "Forgot":

        st.markdown("<h2 style='text-align:center;'>🔑 Reset Password</h2>", unsafe_allow_html=True)

        email = st.text_input("Enter your registered Email")

        # SEND OTP
        if st.button("Send OTP"):

            otp = random.randint(100000, 999999)
            st.session_state.otp = str(otp)

            html = f"""
            <h2>Smart Investment Advisor</h2>
            <p>Your OTP for password reset is:</p>
            <h1>{otp}</h1>
            """

            send_email(email, "Password Reset OTP", html)

            st.success("OTP sent to your email")

        # ENTER OTP
        otp_input = st.text_input("Enter OTP")

        if st.button("Verify OTP"):

            if otp_input.strip() == str(st.session_state.otp):
               st.session_state.otp_verified = True
               st.success("OTP Verified ✅")
            else:
               st.error("Invalid OTP ❌")

        # RESET PASSWORD
        if st.session_state.get("otp_verified"):

           new_password = st.text_input("Enter New Password", type="password")

           if st.button("Reset Password"):

              reset_password(st.session_state["reset_user"], new_password)

              st.success("Password Reset Successful")

              st.session_state["otp"] = None
              st.session_state["otp_verified"] = False
              st.session_state["auth_page"] = "Login"

              st.rerun()

    st.stop()



# sidebar user section removed – profile information is shown inside the dedicated
# Profile tab per updated UX requirements

# ================= MAIN APP =================
# the header is shown only when logged in (it was already rendered above the
# sidebar, but keep this guard as well to avoid flashing during auth
if st.session_state.logged_in:
    show_header("📈")
    st.caption(f"🕒 Live Market | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.write("Ticker box shows live profit/loss. Click ticker to explore all stocks on Yahoo Finance.")
# ================= TOP MENU =================

# shared helper for downloading stock data
@st.cache_data
def fetch_data(sym):
    return yf.download(sym, period="6mo")

home_tab, about_tab, graph_tab, yahoo_tab, profile_tab, stocks_tab = st.tabs(
["🏠 Home", "📘 About", "📊 Graph", "🔗 Yahoo Finance", "👤 Profile", "📈 Stocks"]
)

# store last picked symbol for re-use in other tabs
if "last_symbol" not in st.session_state:
    st.session_state.last_symbol = "AAPL"

IS_TEST = "PYTEST_CURRENT_TEST" in os.environ
if not IS_TEST:
    with home_tab:
        symbol = st.text_input("Enter Stock Symbol", "AAPL", key="home_sym")
        quantity = st.number_input("Quantity", min_value=1, value=1, key="home_qty")
    
        if not st.button("🚀 Fetch & Predict", key="home_go"):
            st.stop()
    
        # remember symbol for the other tabs
        st.session_state.last_symbol = symbol
    
        df = fetch_data(symbol)
    
        if df.empty:
            st.error("No data found")
            st.stop()
    
        latest_price = float(df["Close"].iloc[-1])
        total_value = latest_price * quantity * USD_TO_INR
    
    
        st.subheader("💰 Live Price")
        st.success(f"USD: ${latest_price:.2f}")
        st.success(f"INR: ₹{latest_price*USD_TO_INR:.2f}")
    
        df["ma20"] = df["Close"].rolling(20).mean()
        df["ma50"] = df["Close"].rolling(50).mean()
        df = df.dropna()
    
        decision = "HOLD"
        if df["ma20"].iloc[-1] > df["ma50"].iloc[-1]:
            decision = "BUY"
        elif df["ma20"].iloc[-1] < df["ma50"].iloc[-1]:
            decision = "SELL"
    
        st.subheader("📊 Price Trend")
        if decision == "SELL":
            st.line_chart(df["Close"], color="#C62828")
        elif decision == "BUY":
            st.line_chart(df["Close"], color="#2E7D32")
        else:
            st.line_chart(df["Close"])
    
        # decision panel with animated styling
        st.subheader("📢 Investment Decision")
    
        st.markdown("""
        <style>
        @keyframes softGlowGreen {
        0% { box-shadow: 0 0 5px rgba(76,175,80,0.3); }
        50% { box-shadow: 0 0 30px rgba(76,175,80,0.7); }
        100% { box-shadow: 0 0 5px rgba(76,175,80,0.3); }
        }
        
        @keyframes softGlowRed {
        0% { box-shadow: 0 0 5px rgba(244,67,54,0.3); }
        50% { box-shadow: 0 0 30px rgba(244,67,54,0.7); }
        100% { box-shadow: 0 0 5px rgba(244,67,54,0.3); }
        }
        
        @keyframes softGlowPurple {
        0% { box-shadow: 0 0 5px rgba(156,39,176,0.3); }
        50% { box-shadow: 0 0 30px rgba(156,39,176,0.7); }
        100% { box-shadow: 0 0 5px rgba(156,39,176,0.3); }
        }
        
        .animated-box {
        padding:25px;
        border-radius:15px;
        border:1px solid #ccc;
        text-align:center;
        margin-top:15px;
        font-weight:bold;
        font-size:22px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        
        # 🔥 Decision Logic
        if decision == "BUY":
            decision_text = "📈 BUY Signal"
            bg_color = "#E8F5E9"   # Light Green Background
            text_color = "#2E7D32"
            animation = "softGlowGreen 2s infinite"
        
        elif decision == "SELL":
            decision_text = "📉 SELL Signal"
            bg_color = "#FFEBEE"   # Light Red Background
            text_color = "#C62828"
            animation = "softGlowRed 2s infinite"
        
        else:
            decision_text = "📊 HOLD Position"
            bg_color = "#F3E5F5"
            text_color = "#6A1B9A"
            animation = "softGlowPurple 2s infinite"
        
        
        st.markdown(f"""
        <div class="animated-box"
         style="background-color:{bg_color};
                color:{text_color};
                animation:{animation};">
        {decision_text}
        </div>
        """, unsafe_allow_html=True)
        
        
        
        
        #============Email alert for BUY/SELL signals (only on Home tab to avoid duplicates)===========
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
    
        st.markdown("### 📊 More Stock Details")
        st.info("For complete financial data and charts, click below 👇")
        st.link_button(
            "🔗 View on Yahoo Finance",
            f"https://finance.yahoo.com/quote/{st.session_state.last_symbol}"
        )
    
    with about_tab:
        # reuse the ABOUT_TEXT constant so the copy in tests can inspect it
        st.markdown(ABOUT_TEXT, unsafe_allow_html=True)
    
    with graph_tab:
        st.subheader("📊 Price Trend")
        if decision == "SELL":
            st.line_chart(df["Close"], color="#C62828")
        elif decision == "BUY":
            st.line_chart(df["Close"], color="#2E7D32")
        else:
            st.line_chart(df["Close"])
    
    with yahoo_tab:
        st.markdown("### 📊 More Stock Details")
        st.info("For complete financial data and charts, click below 👇")
        st.link_button(
            "🔗 View on Yahoo Finance",
            f"https://finance.yahoo.com/quote/{st.session_state.last_symbol}"
        )
    
    # ================= USER SIDEBAR =================
    
    with profile_tab:
    
        st.markdown("## 👤 User Details")
        
    
        st.write(f"**Username:** {st.session_state.username}")
        st.write(f"**Email:** {st.session_state.user_email}")
    
        
    
        # 🔥 Logout Hyperlink
        st.markdown(
            """
            <div style='margin-top:10px;'>
                <a href='?action=logout'
                   style='
                       color:#FF5252;
                       font-weight:600;
                       text-decoration: underline;
                       font-size:15px;
                   '>
                   🚪 Logout
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
            
    
        # Password Form
        if st.button("🔑 Change Password"):
            st.session_state.show_change_pw = True
    
        if st.session_state.show_change_pw:
    
            st.subheader("🔐 Update Password")
    
            old_password = st.text_input("Old Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
    
            if st.button("Update Password"):
    
                conn = sqlite3.connect("users.db")
                cursor = conn.cursor()
    
                cursor.execute("SELECT password FROM users WHERE username=?",
                               (st.session_state.username,))
                user = cursor.fetchone()
    
                if user:
                    stored_password = user[0]
    
                    if bcrypt.checkpw(old_password.encode(), stored_password):
    
                        if new_password == confirm_password:
    
                            hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    
                            cursor.execute(
                                "UPDATE users SET password=? WHERE username=?",
                                (hashed, st.session_state.username)
                            )
    
                            conn.commit()
                            conn.close()
    
                            st.success("✅ Password updated successfully")
    
                        else:
                            st.error("⚠ Passwords do not match")
    
                    else:
                        st.error("❌ Old password incorrect")
    
                else:
                    st.error("User not found")
    
    if __name__ == "__main__":
        with stocks_tab:
            
            st.title("📈 Live Stock Market")
    
            stocks = {
                "Apple": "AAPL",
                "Microsoft": "MSFT",
                "Google": "GOOGL",
                "Amazon": "AMZN",
                "Tesla": "TSLA",
                "Nvidia": "NVDA",
                "Meta": "META",
                "Netflix": "NFLX",
                "Intel": "INTC",
                "AMD": "AMD",
                "Boeing": "BA",
                "Disney": "DIS",
                "Nike": "NKE",
                "Starbucks": "SBUX",
                "Coca Cola": "KO",
                "Pepsi": "PEP",
                "Walmart": "WMT",
                "JPMorgan": "JPM",
                "Visa": "V",
                "Mastercard": "MA"
            }
    
            for name, ticker in stocks.items():
    
                data = yf.download(ticker, period="1d", interval="5m")
    
                if not data.empty:
    
                    # ensure single numeric values (not Series) for comparison
                    close_series = data["Close"]
                    # retrieving values may occasionally return a 1-element Series
                    raw_latest = close_series.iloc[-1]
                    raw_first = close_series.iloc[0]
                    if hasattr(raw_latest, "item"):
                        latest_price = float(raw_latest.item())
                    else:
                        latest_price = float(raw_latest)
                    if hasattr(raw_first, "item"):
                        first_price = float(raw_first.item())
                    else:
                        first_price = float(raw_first)
                    change = latest_price - first_price
    
                    col1, col2 = st.columns([3,1])
    
                    with col1:
                        st.subheader(f"{name} ({ticker})")
                        st.line_chart(close_series)
    
                    with col2:
                        if change >= 0:
                            st.success(f"${latest_price:.2f} ▲ {change:.2f}")
                        else:
                            st.error(f"${latest_price:.2f} ▼ {change:.2f}")
    
                    st.divider()