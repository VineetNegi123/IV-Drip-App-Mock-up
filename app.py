import streamlit as st
import datetime
import random

# Simulated data for demo
def get_sensor_data():
    return {
        "drip_level": round(random.uniform(0, 100), 1),
        "drip_active": random.choice([True, False]),
        "air_bubble": random.choice([False, False, True]),
        "power_status": random.choice(["Normal", "Battery Backup", "Offline"]),
        "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "malfunction": random.choice([False, False, True]),
    }

# Page setup
st.set_page_config(page_title="DripGuard Monitor", layout="wide")
st.sidebar.title("🧭 DripGuard Navigation")
page = st.sidebar.radio("Go to", ["Live Monitor", "History", "QR Scan", "Admin Login"])

# Page: Live Monitor
if page == "Live Monitor":
    st.title("💧 DripGuard Monitoring")
    st.markdown("### 👤 Patient: Judy Hopps | Bed: 12B | Ward: C2")

    sensor = get_sensor_data()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("💧 Drip Level", f"{sensor['drip_level']}%")
        if sensor['drip_level'] < 20:
            st.error("Warning: Low Drip Level!")
        elif sensor['drip_level'] < 50:
            st.warning("Drip Level below 50%")

    with col2:
        st.metric("🩺 Drip Activity", "Active" if sensor['drip_active'] else "Stopped")
        if not sensor['drip_active']:
            st.error("Alert: Drip stopped!")
        if sensor['air_bubble']:
            st.error("⚠️ Air Bubble Detected!")

    with col3:
        st.metric("🔋 Power Status", sensor['power_status'])
        if sensor['power_status'] == "Offline":
            st.error("Power Outage Detected!")

    st.markdown("---")
    if st.button("📞 Call Nurse Now"):
        st.success("Nurse Alert Sent!")

    if sensor['malfunction']:
        st.error("⚠️ Malfunction Detected: Sensor needs inspection.")

    st.markdown("---")
    st.markdown(f"<small>Last Synced: {sensor['last_update']}</small>", unsafe_allow_html=True)

# Page: History
elif page == "History":
    st.title("📈 Historical Trends")
    st.info("This page will display charts of drip usage, alerts, and refill trends.")
    st.line_chart([random.randint(20, 100) for _ in range(10)])

# Page: QR Scan
elif page == "QR Scan":
    st.title("🔍 Scan QR to Select Patient")
    st.write("Simulated QR scan for patient selection:")
    scanned_patient = st.text_input("📷 Paste QR code result (patient ID):")
    if scanned_patient:
        st.success(f"✅ Patient record loaded for ID: {scanned_patient}")
    else:
        st.info("Awaiting QR scan input...")

# Page: Admin Login
elif page == "Admin Login":
    st.title("🔐 Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.success("Access granted. Welcome Admin!")
            st.markdown("You can now manage thresholds, reset data, or configure Firebase.")
        else:
            st.error("Invalid credentials.")
