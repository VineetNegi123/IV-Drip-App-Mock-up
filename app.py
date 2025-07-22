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

# ---------------------------
# Simulated sensor data
# ---------------------------
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

# ---------------------------
# Alert logger
# ---------------------------
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

# ---------------------------
# Load patient record
# ---------------------------
def load_patient(patient_id):
    file_path = f"patients/{patient_id}.json"
    if os.path.exists(file_path):
        with open(file_path) as f:
            return json.load(f)
    else:
        return {"name": "Unknown", "age": "-", "ward": "-", "diagnosis": "Not Found"}

# ---------------------------
# Streamlit App Setup
# ---------------------------
st.set_page_config(page_title="DripGuard", layout="wide")

if "role" not in st.session_state:
    st.session_state.role = None
if "patient_id" not in st.session_state:
    st.session_state.patient_id = "TEST123"

# ---------------------------
# Login Page
# ---------------------------
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

# ---------------------------
# Sidebar Navigation
# ---------------------------
st.sidebar.title("🧭 Navigation")
pages = ["Live Monitor", "QR Image Upload", "History"]
if st.session_state.role == "admin":
    pages += ["Dashboard", "Admin Tools"]
pages.append("Logout")
page = st.sidebar.radio("Go to", pages)

if page == "Logout":
    st.session_state.role = None
    st.experimental_rerun()

# ---------------------------
# Page: Live Monitor
# ---------------------------
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

# ---------------------------
# Page: QR Image Upload
# ---------------------------
elif page == "QR Image Upload":
    st.title("📷 Upload QR Code Image")
    uploaded_file = st.file_uploader("Upload image with QR code", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        img_array = np.array(image)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        qr_detector = cv2.QRCodeDetector()
        data, points, _ = qr_detector.detectAndDecode(img_bgr)
        if data:
            st.session_state.patient_id = data
            st.success(f"✅ Loaded Patient ID: {data}")
        else:
            st.warning("⚠️ No QR code detected.")

# ---------------------------
# Page: History
# ---------------------------
elif page == "History":
    st.title("📈 Alert History")
    try:
        df = pd.read_csv("alert_log.csv")
        st.dataframe(df.tail(20))
        st.line_chart(df['Time'].value_counts().sort_index())
    except:
        st.info("No alerts logged yet.")

# ---------------------------
# Page: Admin Dashboard
# ---------------------------
elif page == "Dashboard" and st.session_state.role == "admin":
    st.title("📊 Admin Dashboard")
    try:
        df = pd.read_csv("alert_log.csv")
        st.metric("🔔 Total Alerts", len(df))
        st.metric("📅 Active Days", df['Time'].str[:10].nunique())
        st.bar_chart(df['Alert'].value_counts())
    except:
        st.info("No data to display.")

# ---------------------------
# Page: Admin Tools
# ---------------------------
elif page == "Admin Tools" and st.session_state.role == "admin":
    st.title("🛠️ Admin Tools")

    # Edit patient records
    st.subheader("📋 Edit Patient Record")
    patient_files = [f.replace(".json", "") for f in os.listdir("patients") if f.endswith(".json")]
    selected_id = st.selectbox("Select Patient ID", patient_files)
    with open(f"patients/{selected_id}.json") as f:
        pdata = json.load(f)
    with st.form("edit_patient"):
        name = st.text_input("Name", value=pdata["name"])
        age = st.number_input("Age", value=int(pdata["age"]), min_value=0)
        ward = st.text_input("Ward", value=pdata["ward"])
        diagnosis = st.text_input("Diagnosis", value=pdata["diagnosis"])
        if st.form_submit_button("Save"):
            pdata = {"name": name, "age": age, "ward": ward, "diagnosis": diagnosis}
            with open(f"patients/{selected_id}.json", "w") as f:
                json.dump(pdata, f, indent=2)
            st.success("✅ Record updated")

    # Export alert log
    st.subheader("📤 Export Alert Log")
    if os.path.exists("alert_log.csv"):
        df = pd.read_csv("alert_log.csv")
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        st.download_button("📥 Download Excel Report", buffer.getvalue(),
                           file_name="DripGuard_Alerts.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("No alert log found.")
