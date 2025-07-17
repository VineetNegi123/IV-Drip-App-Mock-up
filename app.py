import streamlit as st
import datetime
import random
import pandas as pd
import os

# Simulated patient data
patient = {
    "name": "Judy Hopps",
    "bed": "12B",
    "ward": "C2",
    "iv_bag_capacity_ml": 500  # Used for estimating depletion time
}

# Generate simulated sensor data
def get_sensor_data():
    drip_level_percent = round(random.uniform(0, 100), 1)
    flow_rate = round(random.uniform(30, 120), 1)  # mL/hr
    volume_remaining = (drip_level_percent / 100) * patient["iv_bag_capacity_ml"]
    time_to_empty_hr = round(volume_remaining / flow_rate, 2) if flow_rate > 0 else None

    return {
        "drip_level": drip_level_percent,
        "drip_active": random.choice([True, False]),
        "air_bubble": random.choice([False, False, True]),
        "power_status": random.choice(["Normal", "Battery Backup", "Offline"]),
        "drip_flow_rate": flow_rate,
        "volume_remaining": volume_remaining,
        "time_to_empty_hr": time_to_empty_hr,
        "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "malfunction": random.choice([False, False, True])
    }

# Log alerts to a CSV
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

# Streamlit setup
st.set_page_config(page_title="DripGuard Monitor", layout="wide")
st.sidebar.title("🧭 DripGuard Navigation")
page = st.sidebar.radio("Go to", ["Live Monitor", "History", "QR Scan", "Admin Login"])

# Live Monitor Page
if page == "Live Monitor":
    st.title("💧 DripGuard Monitoring")
    st.markdown(f"### 👤 Patient: {patient['name']} | Bed: {patient['bed']} | Ward: {patient['ward']}")

    sensor = get_sensor_data()
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

    # Flow rate & estimation
    st.markdown("### 💦 Drip Flow Details")
    st.metric("Flow Rate", f"{sensor['drip_flow_rate']} mL/hr")
    st.metric("Volume Left", f"{round(sensor['volume_remaining'], 1)} mL")
    if sensor['time_to_empty_hr']:
        st.metric("⏳ Time to Depletion", f"{sensor['time_to_empty_hr']} hr")
        if sensor['time_to_empty_hr'] < 1:
            st.warning("IV bag may run empty in less than 1 hour!")

    st.markdown("---")
    if st.button("📞 Call Nurse Now"):
        st.success("🚨 Nurse Alert Sent!")
        log_alert("Manual Nurse Alert")

    if sensor['malfunction']:
        st.error("⚠️ Malfunction Detected!")
        log_alert("Device Malfunction")

    st.markdown(f"<small>Last Synced: {sensor['last_update']}</small>", unsafe_allow_html=True)

# History Page
elif page == "History":
    st.title("📈 Historical Drip & Alert Trends")
    st.subheader("🛎️ Alert Log")
    try:
        df = pd.read_csv("alert_log.csv")
        st.dataframe(df.tail(20))
        st.line_chart(df['Time'].value_counts().sort_index())
    except:
        st.info("No alert log data found yet.")

# QR Scan Page
elif page == "QR Scan":
    st.title("🔍 Scan QR to Select Patient")
    scanned_patient = st.text_input("📷 Paste QR code result (Patient ID)")
    if scanned_patient:
        st.success(f"✅ Loaded patient record: {scanned_patient}")
    else:
        st.info("Awaiting QR input...")

# Admin Login Page
elif page == "Admin Login":
    st.title("🔐 Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.success("Admin Access Granted!")
            st.markdown("🛠 You can now configure thresholds, export logs, and reset system.")
        else:
            st.error("❌ Invalid credentials.")
