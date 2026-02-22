# ==========================================================
# RegulaAI – FULL FINAL VERSION (LOCAL + CLOUD SAFE)
# ==========================================================

# =====================
# IMPORTS
# =====================

import streamlit as st
import PyPDF2
import os
import io
import smtplib
import matplotlib.pyplot as plt

from groq import Groq
from email.message import EmailMessage
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from dotenv import load_dotenv


# =====================
# LOAD ENV
# =====================

load_dotenv()


# =====================
# LOAD SECRETS SAFE (NO ERROR)
# =====================

try:

    APP_USER = st.secrets["APP_USER"]
    APP_PASSWORD = st.secrets["APP_PASSWORD"]

    GROQ_KEY = st.secrets["GROQ_API_KEY"]

    EMAIL = st.secrets["SENDER_EMAIL"]
    PASSWORD = st.secrets["SENDER_PASSWORD"]

except:

    APP_USER = os.getenv("APP_USER")
    APP_PASSWORD = os.getenv("APP_PASSWORD")

    GROQ_KEY = os.getenv("GROQ_API_KEY")

    EMAIL = os.getenv("SENDER_EMAIL")
    PASSWORD = os.getenv("SENDER_PASSWORD")


# =====================
# CREATE GROQ CLIENT
# =====================

client = Groq(api_key=GROQ_KEY)


# =====================
# LOGIN SYSTEM
# =====================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


def login():

    st.title("🔐 RegulaAI Login")

    username = st.text_input("Username")

    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username == APP_USER and password == APP_PASSWORD:

            st.session_state.logged_in = True

            st.success("Login successful")

            st.rerun()

        else:

            st.error("Invalid Username or Password")


def logout():

    st.session_state.logged_in = False

    st.rerun()


if not st.session_state.logged_in:

    login()

    st.stop()


st.sidebar.button("Logout", on_click=logout)


# =====================
# PAGE SETTINGS
# =====================

st.set_page_config(page_title="RegulaAI", layout="wide")

st.title("✅ RegulaAI – AI Compliance Checker")

st.caption("AI-Powered Regulatory Compliance Platform")


# =====================
# SESSION VARIABLES
# =====================

if "contract" not in st.session_state:

    st.session_state.contract = ""

if "chat" not in st.session_state:

    st.session_state.chat = []

if "improved" not in st.session_state:

    st.session_state.improved = ""


# =====================
# PDF READER
# =====================

def read_pdf(file):

    reader = PyPDF2.PdfReader(file)

    text = ""

    for page in reader.pages:

        text += page.extract_text() or ""

    return text


# =====================
# RISK ANALYSIS
# =====================

def risk_analysis(text):

    score = 0

    risks = []

    text = text.lower()

    if "termination" in text:

        score += 20

        risks.append("Termination clause present")

    else:

        risks.append("Termination clause missing")

    if "liability" in text:

        score += 25

        risks.append("Liability clause present")

    else:

        risks.append("Liability clause missing")

    if "indemn" in text:

        score += 20

        risks.append("Indemnification clause present")

    if "gdpr" not in text:

        score += 15

        risks.append("GDPR compliance missing")

    return score, risks


# =====================
# GENERATE PDF REPORT
# =====================

def generate_report(contract, score, risks):

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)

    y = 800

    pdf.drawString(50, y, "RegulaAI Compliance Report")

    y -= 40

    pdf.drawString(50, y, f"Risk Score: {score}")

    y -= 30

    for r in risks:

        pdf.drawString(60, y, r)

        y -= 20

    pdf.save()

    buffer.seek(0)

    return buffer


# =====================
# SEND EMAIL
# =====================

def send_email(receiver, pdf):

    msg = EmailMessage()

    msg["Subject"] = "RegulaAI Compliance Report"

    msg["From"] = EMAIL

    msg["To"] = receiver

    msg.set_content("Compliance Report Attached")

    msg.add_attachment(

        pdf.read(),

        maintype="application",

        subtype="pdf",

        filename="Compliance_Report.pdf"

    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

        smtp.login(EMAIL, PASSWORD)

        smtp.send_message(msg)


# =====================
# AI CHATBOT
# =====================

def ask_ai(question):

    contract = st.session_state.contract

    prompt = f"""

You are legal compliance AI.

Contract:
{contract[:6000]}

Question:
{question}

Answer professionally:

"""

    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[{"role": "user", "content": prompt}]

    )

    return response.choices[0].message.content


# =====================
# IMPROVE CONTRACT
# =====================

def improve_contract():

    prompt = f"""

Improve this contract:

{st.session_state.contract[:6000]}

"""

    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[{"role": "user", "content": prompt}]

    )

    return response.choices[0].message.content


# =====================
# SIDEBAR
# =====================

page = st.sidebar.radio(

    "Navigation",

    [

        "Upload Contract",

        "Risk Dashboard",

        "Compliance Chatbot",

        "Improve Contract"

    ]

)


# =====================
# UPLOAD PAGE
# =====================

if page == "Upload Contract":

    file = st.file_uploader("Upload PDF", type="pdf")

    if file:

        st.session_state.contract = read_pdf(file)

        st.success("Contract uploaded successfully")


# =====================
# RISK DASHBOARD
# =====================

elif page == "Risk Dashboard":

    contract = st.session_state.contract

    if contract:

        score, risks = risk_analysis(contract)

        st.metric("Risk Score", score)

        fig, ax = plt.subplots()

        ax.pie([score, 100-score], labels=["Risk", "Safe"], autopct="%1.1f%%")

        st.pyplot(fig)

        for r in risks:

            st.error(r)

        email = st.text_input("Enter Email")

        if st.button("Send Report"):

            pdf = generate_report(contract, score, risks)

            send_email(email, pdf)

            st.success("Report sent successfully")


# =====================
# CHATBOT
# =====================

elif page == "Compliance Chatbot":

    question = st.text_input("Ask question")

    if st.button("Ask"):

        answer = ask_ai(question)

        st.session_state.chat.append((question, answer))

    for q, a in reversed(st.session_state.chat):

        st.write("You:", q)

        st.write("AI:", a)


# =====================
# IMPROVE CONTRACT
# =====================

elif page == "Improve Contract":

    if st.button("Generate Improved Contract"):

        st.session_state.improved = improve_contract()

    st.text_area("Improved Contract", st.session_state.improved, height=400)