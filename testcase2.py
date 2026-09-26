import os
import csv
import json
import uuid
from datetime import datetime
import pandas as pd
import streamlit as st
from playwright.sync_api import sync_playwright

# Setup directories
EVIDENCE_DIR = "evidence_files"
CSV_FILE = "fraud_report_master.csv"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

# Define CSV Structure required for report filing
CSV_HEADERS = [
    "Case_ID",
    "Timestamp_Filed",
    "Fraud_Type",
    "Victim_Name",
    "Victim_Phone",
    "Incident_Date",
    "Total_Amount_Lost",
    "Currency",
    "Platform_App_Used",
    "Suspect_URL_Handle",
    "Suspect_Phone_Numbers",
    "Transaction_IDs",
    "Bank_UPI_Details",
    "Evidence_Screenshots",
    "Call_Log_Files",
    "Incident_Description"
]

# Ensure CSV exists with headers
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)

def capture_url_screenshot(url: str, case_id: str) -> str:
    """Takes a full-page screenshot of a suspicious URL using Playwright."""
    try:
        filename = f"{EVIDENCE_DIR}/{case_id}_webpage_{uuid.uuid4().hex[:6]}.png"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 800})
            page.goto(url, timeout=20000, wait_until="networkidle")
            page.screenshot(path=filename, full_page=True)
            browser.close()
        return filename
    except Exception as e:
        return f"Error capturing URL: {str(e)}"

# Page Title
st.set_page_config(page_title="Online Fraud Evidence Collector", layout="wide")
st.title("🚨 Online Fraud Evidence Collector & Report Generator")
st.markdown("Use this portal to capture, structure, and export evidence into a police-ready CSV log.")

with st.form("fraud_collector_form", clear_on_submit=False):
    st.subheader("1. Incident Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        victim_name = st.text_input("Victim Full Name*")
        victim_phone = st.text_input("Victim Phone/Contact*")
    with col2:
        fraud_type = st.selectbox("Fraud Type*", [
            "UPI / Banking Scam", 
            "Phishing / Fake Website", 
            "Investment / Crypto Scam", 
            "E-commerce / Fake Seller Scam", 
            "Job / Identity Scam", 
            "Other"
        ])
        incident_date = st.date_input("Date of Incident*")
    with col3:
        amount_lost = st.number_input("Amount Lost*", min_value=0.0, step=100.0)
        currency = st.selectbox("Currency*", ["INR", "USD", "EUR", "GBP", "Other"])

    st.subheader("2. Suspect & Transaction Identifiers")
    col4, col5 = st.columns(2)
    
    with col4:
        platform_used = st.text_input("Platform Used (e.g., WhatsApp, Telegram, Instagram, Bank App)")
        suspect_phone = st.text_input("Suspect Phone Number(s) / Handles", help="Separate multiple values with commas")
        suspect_url = st.text_input("Suspect Website URL / Profile Link")
    
    with col5:
        txn_ids = st.text_area("Transaction IDs / UTR Numbers*", help="Enter one ID per line")
        bank_details = st.text_area("Bank / UPI / Wallet Details Used", help="e.g., Fraudulent UPI ID or Bank Account No.")

    st.subheader("3. Evidence Uploads")
    
    col6, col7 = st.columns(2)
    with col6:
        uploaded_screenshots = st.file_uploader(
            "Upload Screenshots (Payment receipts, Chat history, Fraudulent posts)", 
            type=["png", "jpg", "jpeg"], 
            accept_multiple_files=True
        )
        auto_capture = st.checkbox("Auto-capture full-page screenshot of the Suspect URL provided above")
        
    with col7:
        uploaded_call_logs = st.file_uploader(
            "Upload Call Logs / Audio Recordings / Documents", 
            type=["png", "jpg", "csv", "txt", "pdf", "mp3", "wav"], 
            accept_multiple_files=True
        )

    st.subheader("4. Incident Narrative")
    description = st.text_area("Detailed Chronological Description of the Scam*")

    submit_button = st.form_submit_button("📁 Process Evidence & Save Entry")

# Form Submission Logic
if submit_button:
    if not victim_name or not amount_lost or not txn_ids or not description:
        st.error("Please fill in all mandatory fields marked with *")
    else:
        case_id = f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        saved_screenshot_paths = []
        saved_call_log_paths = []

        # 1. Process Screenshots
        if uploaded_screenshots:
            for file in uploaded_screenshots:
                save_path = os.path.join(EVIDENCE_DIR, f"{case_id}_img_{file.name}")
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())
                saved_screenshot_paths.append(save_path)

        # 2. Auto Capture Webpage if requested
        if auto_capture and suspect_url:
            with st.spinner("Capturing full-page webpage screenshot..."):
                web_path = capture_url_screenshot(suspect_url, case_id)
                saved_screenshot_paths.append(web_path)

        # 3. Process Call Logs & Docs
        if uploaded_call_logs:
            for file in uploaded_call_logs:
                save_path = os.path.join(EVIDENCE_DIR, f"{case_id}_log_{file.name}")
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())
                saved_call_log_paths.append(save_path)

        # Format list inputs into clean strings
        txn_ids_clean = "; ".join([line.strip() for line in txn_ids.split("\n") if line.strip()])

        # Build Data Row
        row_data = [
            case_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            fraud_type,
            victim_name,
            victim_phone,
            incident_date.strftime("%Y-%m-%d"),
            amount_lost,
            currency,
            platform_used,
            suspect_url,
            suspect_phone,
            txn_ids_clean,
            bank_details,
            " | ".join(saved_screenshot_paths),
            " | ".join(saved_call_log_paths),
            description.replace("\n", " ")
        ]

        # Write to CSV Master File
        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row_data)

        st.success(f"Case {case_id} recorded successfully!")

# Display Master CSV Dataset & Export Options
st.markdown("---")
st.header("📊 Master Fraud Records Log")

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    st.dataframe(df, use_container_width=True)

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="⬇️ Download Structured Fraud CSV Report",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="cyber_fraud_complaint_report.csv",
            mime="text/csv"
        )