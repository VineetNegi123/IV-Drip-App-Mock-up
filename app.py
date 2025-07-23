import streamlit as st
import datetime
import pandas as pd
import os
import cv2
import numpy as np
from PIL import Image
import random
import json
from io import BytesIO

# Simulated sensor data
def get_sensor_data():
    drip_level = round(random.uniform(10, 100), 1)
    flow_rate = round(random.uniform(30, 120), 1)
    volume_remaining = (drip_level / 100) * 500
    time_to_empty = round(volume_remaining / flow_rate, 2) if flow_rate > 0 else None
    return {
        "drip_level": drip_level,
        "drip_active": random.choice([True, False]),
        "air_bubble": random.choice([False, True, False]),
        "power_status": random.choice(["Normal", "Battery Backup", "Offline"]),
        "drip_flow_rate": flow_rate,
        "volume_remaining": volume_remaining,
        "time_to_empty_hr": time_to_empty,
        "malfunction": random.choice([False, False, True])
    }

# Alert logger
def log_alert(message):
    log_path = "alert_log.csv"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = pd.DataFrame([[timestamp, message]], columns=["Time", "Alert"])
    if os.path.exists(log_path):
        old = pd.read_csv(log_path)
        new = pd.concat([old, entry], ignore_index=True)
        new.to_csv(log_path, index=False)
    else:
        entry.to_csv(log_path, index=False)

# Load patient data
def load_patient(patient_id):
    path = f"patients/{patient_id}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"name": "Unknown", "age": "-", "ward": "-", "diagnosis": "Not Found"}

# App setup
st.set_page_config(page_title="DripGuard", layout="wide")
if "role" not in st.session_state:
    st.session_state.role = None
if "patient_id" not in st.session_state:
    st.session_state.patient_id = "TEST123"

# Login
if st.session_state.role is None:
    st.title("🔐 Login to DripGuard System")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.role = "admin"
        elif username == "nurse" and password == "nurse123":
            st.session_state.role = "nurse"
        else:
            st.error("Invalid credentials.")
    st.stop()

# Sidebar
st.sidebar.title("🧭 Navigation")
pages = ["Live Monitor", "QR Image Upload", "History"]
if st.session_state.role == "admin":
    pages += ["Dashboard", "Admin Tools"]
pages.append("Logout")
page = st.sidebar.radio("Go to", pages)

# ✅ Logout (reruns the app after clearing session)
if page == "Logout":
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("✅ Logged out.")
    st.experimental_rerun()

# Live Monitor
if page == "Live Monitor":
    st.title("💧 DripGuard - Simulated IV Monitor")
    sensor = get_sensor_data()
    patient = load_patient(st.session_state.patient_id)
    st.markdown(f"### 👤 Patient: {patient['name']} | ID: {st.session_state.patient_id}")
    st.markdown(f"- Age: {patient['age']}, Ward: {patient['ward']}, Diagnosis: {patient['diagnosis']}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💧 Drip Level", f"{sensor['drip_level']}%")
        if sensor['drip_level'] < 20:
            st.error("⚠️ Low Drip Level!")
            log_alert("Low Drip Level")
        elif sensor['drip_level'] < 50:
            st.warning("Drip Level below 50%")
    with col2:
        st.metric("🩺 Drip Activity", "Active" if sensor['drip_active'] else "Stopped")
        if not sensor['drip_active']:
            st.error("⚠️ Drip stopped!")
            log_alert("Drip stopped")
        if sensor['air_bubble']:
            st.error("⚠️ Air Bubble Detected!")
            log_alert("Air Bubble Detected")
    with col3:
        st.metric("🔋 Power Status", sensor['power_status'])
        if sensor['power_status'] == "Offline":
            st.error("⚠️ Power Outage!")
            log_alert("Power Outage")

    st.metric("💦 Flow Rate", f"{sensor['drip_flow_rate']} mL/hr")
    st.metric("Volume Left", f"{round(sensor['volume_remaining'], 1)} mL")
    if sensor['time_to_empty_hr']:
        st.metric("⏳ Time to Depletion", f"{sensor['time_to_empty_hr']} hr")
        if sensor['time_to_empty_hr'] < 1:
            st.warning("May run empty in < 1 hr!")

    if st.button("📞 Call Nurse Now"):
        st.success("🚨 Nurse Alert Sent!")
        log_alert("Manual Nurse Alert")

    if sensor['malfunction']:
        st.error("⚠️ Malfunction Detected!")
        log_alert("Device Malfunction")

# QR Image Upload
elif page == "QR Image Upload":
    st.title("📷 Upload QR Code Image")
    uploaded_file = st.file_uploader("Upload QR image", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        img_array = np.array(image)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        qr = cv2.QRCodeDetector()
        data, points, _ = qr.detectAndDecode(img_bgr)
        if data:
            st.session_state.patient_id = data
            st.success(f"✅ Patient ID loaded: {data}")
        else:
            st.warning("⚠️ No QR code detected.")

# History
elif page == "History":
    st.title("📈 Alert History")
    try:
        df = pd.read_csv("alert_log.csv")
        st.dataframe(df.tail(20))
        st.line_chart(df['Time'].value_counts().sort_index())
    except:
        st.info("No alerts yet.")

# Dashboard
elif page == "Dashboard" and st.session_state.role == "admin":
    st.title("📊 Admin Dashboard")
    try:
        df = pd.read_csv("alert_log.csv")
        df['Date'] = pd.to_datetime(df['Time']).dt.date

        col1, col2, col3 = st.columns(3)
        col1.metric("🔔 Total Alerts", len(df))
        col2.metric("📅 Active Days", df['Date'].nunique())
        col3.metric("⚠️ Most Common", df['Alert'].value_counts().idxmax())

        with st.expander("📆 Filter by Date"):
            start = st.date_input("Start", df['Date'].min())
            end = st.date_input("End", df['Date'].max())
            df = df[(df['Date'] >= start) & (df['Date'] <= end)]

        st.subheader("📈 Alerts Breakdown")
        st.bar_chart(df['Alert'].value_counts())

    except Exception as e:
        st.warning("⚠️ No alert log found or error loading data.")

# Admin Tools
elif page == "Admin Tools" and st.session_state.role == "admin":
    st.title("🛠️ Admin Tools: Patient Records & Reports")

    # Edit patient files
    st.header("📋 Manage Patient Files")
    files = [f.replace(".json", "") for f in os.listdir("patients") if f.endswith(".json")]
    selected_id = st.selectbox("Select Patient ID", files)
    record_path = f"patients/{selected_id}.json"
    with open(record_path) as f:
        patient_data = json.load(f)
    with st.form("edit_patient"):
        name = st.text_input("Name", patient_data.get("name", ""))
        age = st.number_input("Age", value=int(patient_data.get("age", 0)))
        ward = st.text_input("Ward", patient_data.get("ward", ""))
        diagnosis = st.text_input("Diagnosis", patient_data.get("diagnosis", ""))
        save = st.form_submit_button("Save Changes")
    if save:
        updated = {"name": name, "age": age, "ward": ward, "diagnosis": diagnosis}
        with open(record_path, "w") as f:
            json.dump(updated, f, indent=2)
        st.success("✅ Record updated!")

    # Export alerts
    st.header("📤 Export Alerts Log")
    if os.path.exists("alert_log.csv"):
        df = pd.read_csv("alert_log.csv")
        to_excel = BytesIO()
        df.to_excel(to_excel, index=False, engine="openpyxl")
        st.download_button("📥 Download Excel", to_excel.getvalue(),
            file_name="DripGuard_Alerts.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("No alert log found.")
