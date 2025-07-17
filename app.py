import streamlit as st
import datetime
import pandas as pd
import os
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
import cv2
import random

# ---------------------------
# Simulated sensor data
# ---------------------------
def get_sensor_data():
    drip_level = round(random.uniform(10, 100), 1)
    flow_rate = round(random.uniform(30, 120), 1)
    volume_remaining = (drip_level / 100) * 500
    time_to_empty = round(volume_remaining / flow_rate, 2) if flow_rate > 0 else None

    return {
        "patient_id": "TEST123",
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
# OpenCV QR code scanner
# ---------------------------
class QRProcessor(VideoProcessorBase):
    def __init__(self):
        self.qr_detector = cv2.QRCodeDetector()

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        data, points, _ = self.qr_detector.detectAndDecode(img)
        if data:
            st.session_state.qr_result = data
            if points is not None:
                points = points.astype(int)
                cv2.polylines(img, [points], isClosed=True, color=(0, 255, 0), thickness=2)
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# ---------------------------
# Streamlit App
# ---------------------------
st.set_page_config(page_title="DripGuard", layout="wide")
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Go to", ["Live Monitor", "QR Scan", "History", "Admin Login"])

if page == "Live Monitor":
    st.title("💧 DripGuard - Simulated IV Monitor")
    sensor = get_sensor_data()
    st.markdown(f"### 👤 Patient ID: {sensor['patient_id']}")

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

elif page == "QR Scan":
    st.title("🔍 QR Code Scanner")
    if 'qr_result' not in st.session_state:
        st.session_state.qr_result = ''
    webrtc_streamer(key="qr", video_processor_factory=QRProcessor)
    if st.session_state.qr_result:
        st.success(f"✅ Scanned Patient ID: {st.session_state.qr_result}")

elif page == "History":
    st.title("📈 Alert History")
    try:
        df = pd.read_csv("alert_log.csv")
        st.dataframe(df.tail(20))
        st.line_chart(df['Time'].value_counts().sort_index())
    except:
        st.info("No alerts logged yet.")

elif page == "Admin Login":
    st.title("🔐 Admin Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pwd == "admin123":
            st.success("Access granted.")
        else:
            st.error("❌ Invalid credentials.")
