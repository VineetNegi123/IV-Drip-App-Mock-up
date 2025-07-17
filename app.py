import streamlit as st
import datetime
import pandas as pd
import os
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
from pyzbar.pyzbar import decode
import cv2
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_service_account.json")  # Replace with your actual path
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://your-project-id.firebaseio.com/'  # Replace with your Firebase Realtime DB URL
    })

# Fetch sensor data from Firebase
def get_sensor_data():
    try:
        ref = db.reference("sensor_data")  # Path to your ESP32 data
        return ref.get()
    except Exception as e:
        st.error(f"Firebase Error: {e}")
        return None

# Log alerts locally
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

# QR Code scanner processor
class QRProcessor(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        decoded_objs = decode(img)
        for obj in decoded_objs:
            data = obj.data.decode("utf-8")
            st.session_state.qr_result = data
            cv2.rectangle(img, obj.rect[:2], (obj.rect[0]+obj.rect[2], obj.rect[1]+obj.rect[3]), (0, 255, 0), 2)
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# Streamlit UI setup
st.set_page_config(page_title="DripGuard", layout="wide")
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Go to", ["Live Monitor", "QR Scan", "History", "Admin Login"])

# Live Monitor Page
if page == "Live Monitor":
    st.title("💧 DripGuard - Real-Time IV Monitor")

    sensor = get_sensor_data()
    if sensor:
        patient_id = sensor.get("patient_id", "Unknown")
        st.markdown(f"### 👤 Patient ID: {patient_id}")
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
        if 'volume_remaining' in sensor:
            st.metric("Volume Left", f"{round(sensor['volume_remaining'], 1)} mL")
        if 'time_to_empty_hr' in sensor:
            st.metric("⏳ Time to Depletion", f"{sensor['time_to_empty_hr']} hr")
            if sensor['time_to_empty_hr'] < 1:
                st.warning("IV bag may run empty in less than 1 hour!")

        if st.button("📞 Call Nurse Now"):
            st.success("🚨 Nurse Alert Sent!")
            log_alert("Manual Nurse Alert")

        if sensor['malfunction']:
            st.error("⚠️ Malfunction Detected!")
            log_alert("Device Malfunction")
    else:
        st.warning("⚠️ No sensor data available yet.")

# QR Code Page
elif page == "QR Scan":
    st.title("🔍 QR Code Scanner")
    if 'qr_result' not in st.session_state:
        st.session_state.qr_result = ''
    webrtc_streamer(key="qr", video_processor_factory=QRProcessor)
    if st.session_state.qr_result:
        st.success(f"✅ Scanned Patient ID: {st.session_state.qr_result}")

# Alert History
elif page == "History":
    st.title("📈 Alert History")
    try:
        df = pd.read_csv("alert_log.csv")
        st.dataframe(df.tail(20))
        st.line_chart(df['Time'].value_counts().sort_index())
    except:
        st.info("No alerts logged yet.")

# Admin Page
elif page == "Admin Login":
    st.title("🔐 Admin Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pwd == "admin123":
            st.success("Access granted.")
            st.info("Configure thresholds, reset system, or export logs.")
        else:
            st.error("❌ Invalid credentials.")
