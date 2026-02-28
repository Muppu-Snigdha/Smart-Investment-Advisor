import streamlit as st
import yfinance as yf
from datetime import datetime
import sqlite3
import bcrypt
import smtplib
from email.mime.text import MIMEText

# ================= APP CONFIG =================
st.set_page_config(page_title="Smart Investment Advisor", layout="wide")

SENDER_EMAIL = "smartinvestmentadvisor36@gmail.com"
APP_PASSWORD = "dadx xxar synn fere"
USD_TO_INR = 83

# ================= CLEAN CSS =================
st.markdown("""
<style>

/* ---------- APP BACKGROUND ---------- */
.stApp {
    background-color: #FFFFFF;
    font-family: 'Segoe UI', sans-serif;
}

/* ---------- MAIN TITLE ---------- */
.main-title {
    text-align: center;
    font-size: 36px;
    font-weight: bold;
    color: #6A1B9A;
    margin-bottom: 10px;
}

/* ---------- ALL HEADINGS FIX ---------- */
h1, h2, h3, h4, h5, h6 {
    color: #4B0082 !important;
    opacity: 1 !important;
    font-weight: 700 !important;
}

/* Custom sub heading */
.sub-heading {
    color: #4B0082 !important;
    font-weight: 700 !important;
    text-align: center;
}

/* ---------- INPUT BOXES ---------- */
input[type="text"],
input[type="password"],
input[type="number"],
textarea {
    background-color: #EDE7F6 !important;
    color: black !important;
    border-radius: 10px !important;
    border: 1px solid #D1C4E9 !important;
    padding: 8px !important;
}

/* Streamlit input container */
div[data-baseweb="input"] > div {
    background-color: #EDE7F6 !important;
    border-radius: 10px !important;
}

/* ---------- BUTTONS ---------- */
.stButton > button {
    background-color: #7E57C2 !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 20px !important;
    transition: 0.3s ease-in-out;
}

.stButton > button:hover {
    background-color: #5E35B1 !important;
    transform: scale(1.03);
}

/* ---------- SUCCESS & ERROR TEXT ---------- */
.green-text {
    color: #2E7D32;
    font-size: 20px;
    font-weight: bold;
    text-align: center;
}

.red-text {
    color: #C62828;
    font-size: 20px;
    font-weight: bold;
    text-align: center;
}

/* ---------- SIDEBAR ---------- */
section[data-testid="stSidebar"] {
    background-color: #F3E5F5;
}

/* ---------- MOBILE RESPONSIVE ---------- */
@media (max-width: 768px) {

    .main-title {
        font-size: 26px !important;
    }

    h1 { font-size: 24px !important; }
    h2 { font-size: 20px !important; }
    h3 { font-size: 18px !important; }

    .stButton > button {
        width: 100% !important;
    }

    div[data-baseweb="input"] {
        width: 100% !important;
    }
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
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "Login"

# ================= AUTH UI ==============
# ================= AUTH UI =================
if not st.session_state.logged_in:

    st.markdown("<div class='main-title'>👑 Smart Investment Advisor</div>", unsafe_allow_html=True)

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

    st.stop()
       
# ================= SIDEBAR =================
st.sidebar.title("👤 User Details")
st.sidebar.write(f"**Username:** {st.session_state.username}")
st.sidebar.write(f"**Email:** {st.session_state.user_email}")

if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ================= MAIN APP =================
st.markdown("<div class='main-title'>📈 Smart Investment Advisor</div>", unsafe_allow_html=True)
st.caption(f"🕒 Live Market | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.subheader("🔎 Stock Search")

symbol = st.text_input("Enter Stock Symbol", "AAPL")
quantity = st.number_input("Quantity", min_value=1, value=1)

if not st.button("🚀 Fetch & Predict"):
    st.stop()

@st.cache_data
def fetch_data(sym):
    return yf.download(sym, period="6mo")

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
    border-radius:18px;
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
