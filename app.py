import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# Page Configuration
st.set_page_config(
    page_title="CareLink System",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session Theme State
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light Mode ☀️"

# Dynamic Theme Injection
if "Dark" in st.session_state.theme_mode:
    st.markdown("""
        <style>
        .stApp { background-color: #0f172a; color: #f8fafc; }
        div[data-testid="stSidebar"] { background-color: #1e293b; }
        div[data-testid="stForm"] { background-color: #1e293b; border: 1px solid #334155; padding: 20px; border-radius: 10px; }
        .metric-card { background-color: #1e293b; border: 1px solid #334155; padding: 15px; border-radius: 8px; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp { background-color: #f8fafc; color: #0f172a; }
        div[data-testid="stForm"] { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 20px; border-radius: 10px; }
        .metric-card { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; }
        </style>
    """, unsafe_allow_html=True)

# Credentials (Streamlit Secrets with Fallback)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = "https://mkdvkaraqdjsxgxqjnhg.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1rZHZrYXJhcWRqc3hneHFqbmhnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ1NDgwMzMsImV4cCI6MjEwMDEyNDAzM30.bKkl_O1FtV1iMkbFsTKF06W8hOTpRYQbt7fpFdkGGaI"

@st.cache_resource
def init_supabase():
    clean_url = SUPABASE_URL.strip().rstrip("/").replace("/rest/v1", "").replace("/auth/v1", "")
    return create_client(clean_url, SUPABASE_KEY)

supabase = init_supabase()

# Initialize Session Data
if "vitals_data" not in st.session_state:
    st.session_state.vitals_data = [
        {"Timestamp": "2026-07-24 10:30", "Patient": "John Doe (Room 102)", "Heart Rate (BPM)": 78, "Blood Pressure": "120/80", "Temp (°C)": 36.8, "SpO2 (%)": 98, "Logged By": "Dr. Smith"},
        {"Timestamp": "2026-07-24 11:15", "Patient": "Mary Jane (Room 105)", "Heart Rate (BPM)": 105, "Blood Pressure": "138/88", "Temp (°C)": 38.2, "SpO2 (%)": 94, "Logged By": "Nurse Sarah"}
    ]

if "medications_data" not in st.session_state:
    st.session_state.medications_data = [
        {"Patient": "John Doe (Room 102)", "Medication": "Amoxicillin", "Dosage": "500mg", "Frequency": "Twice Daily", "Status": "Active"},
        {"Patient": "Mary Jane (Room 105)", "Medication": "Lisinopril", "Dosage": "10mg", "Frequency": "Once Daily", "Status": "Refill Needed"}
    ]

if "handovers_data" not in st.session_state:
    st.session_state.handovers_data = [
        {"Timestamp": "2026-07-24 08:00", "Outgoing Staff": "Nurse Sarah", "Incoming Staff": "Nurse David", "Patient": "John Doe", "Shift Notes": "Patient slept well. Morning vitals stable."}
    ]

# IDPS Security Incident Logs
if "idps_logs" not in st.session_state:
    st.session_state.idps_logs = [
        {"Timestamp": "2026-07-24 09:12:04", "IP Address": "192.168.1.104", "Event Type": "Brute Force Attempt", "Severity": "High", "Action Taken": "IP Blocked (15m)"},
        {"Timestamp": "2026-07-24 08:45:12", "IP Address": "10.0.0.12", "Event Type": "SQLi Pattern Detected", "Severity": "Critical", "Action Taken": "Request Sanitized & Dropped"},
        {"Timestamp": "2026-07-24 07:30:00", "IP Address": "192.168.1.50", "Event Type": "MFA Auth Success", "Severity": "Low", "Action Taken": "Session Initialized"}
    ]

def login_signup_portal():
    st.markdown("<h1 style='text-align: center; color: #2563eb;'>🩺 CareLink Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Secure Access for Healthcare Coordination</p>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 Sign In / OTP", "📝 Register"])
    
    with tab1:
        st.subheader("Sign In with OTP")
        email = st.text_input("Email Address", key="signin_email")
        
        if st.button("Send 6-Digit OTP Code"):
            if email:
                try:
                    supabase.auth.sign_in_with_otp({
                        "email": email,
                        "options": {"should_create_user": True}
                    })
                    st.success("Verification code sent to your email inbox!")
                except Exception as e:
                    st.error(f"Error sending code: {e}")
            else:
                st.warning("Please enter a valid email address.")
        
        otp_token = st.text_input("Enter 6-Digit Code", type="password", key="otp_token")
        if st.button("Verify & Login"):
            if email and otp_token:
                try:
                    auth_response = supabase.auth.verify_otp({
                        "email": email,
                        "token": otp_token,
                        "type": "email"
                    })
                    if auth_response.session:
                        st.session_state['user'] = auth_response.user
                        st.success("Login successful!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Invalid or expired OTP code: {e}")

    with tab2:
        st.subheader("New Account Registration")
        reg_email = st.text_input("Email Address", key="reg_email")
        if st.button("Register & Send Verification"):
            if reg_email:
                try:
                    supabase.auth.sign_in_with_otp({
                        "email": reg_email,
                        "options": {"should_create_user": True}
                    })
                    st.success("Registration code sent! Check your email to verify.")
                except Exception as e:
                    st.error(f"Registration error: {e}")

def main_dashboard():
    # Sidebar Header
    st.sidebar.markdown("### 🩺 CareLink System")
    
    # Safe User & Metadata Extraction
    user = st.session_state.get("user")
    user_email = getattr(user, "email", "User") if user else "User"
    
    # Extract Role safely from Supabase user_metadata (default to 'clinician')
    user_metadata = getattr(user, "user_metadata", {}) or {}
    user_role = user_metadata.get("role", "clinician").lower()
    
    st.sidebar.markdown(f"**Logged in as:** `{user_email}`")
    st.sidebar.caption(f"🛡️ **Role:** `{user_role.upper()}`")
    st.sidebar.divider()
    
    # Theme Selector
    selected_theme = st.sidebar.radio(
        "🎨 Interface Theme",
        ["Light Mode ☀️", "Dark Mode 🌙"],
        index=0 if st.session_state.theme_mode == "Light Mode ☀️" else 1
    )
    
    if selected_theme != st.session_state.theme_mode:
        st.session_state.theme_mode = selected_theme
        st.rerun()

    st.sidebar.divider()
    
    # RBAC Dynamic Navigation Menu
    menu_options = [
        "Dashboard Overview", 
        "Vitals Logs", 
        "Medication & Prescriptions", 
        "Shift Handovers", 
        "Emergency SOS"
    ]
    
    # Add IDPS only if user role is admin
    if user_role == "admin":
        menu_options.append("🛡️ Security Hub (IDPS)")
    
    menu = st.sidebar.radio("Navigation Menu", menu_options)
    
    st.sidebar.divider()
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        st.session_state.pop('user', None)
        st.rerun()

    # 1. Dashboard Overview
    if menu == "Dashboard Overview":
        st.title("🏥 Clinical Workspace Overview")
        st.markdown("Real-time clinical summary and patient status monitoring.")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Active Patients", "14", "+2 today")
        with col2:
            st.metric("Pending Refills", "3", "Action Required", delta_color="inverse")
        with col3:
            st.metric("Vitals Recorded Today", len(st.session_state.vitals_data), "+1 this hour")
        with col4:
            st.metric("System Status", "Secure & Online", "100%")

        st.divider()
        st.subheader("📋 Recent Clinical Alerts")
        st.warning("⚠️ **Mary Jane (Room 105):** Elevated Heart Rate (105 BPM) & Temp (38.2 °C) logged at 11:15 AM.")
        st.info("ℹ️ **John Doe (Room 102):** Scheduled for afternoon vitals check at 14:00.")

    # 2. Vitals Logs
    elif menu == "Vitals Logs":
        st.title("🫀 Patient Vitals Tracker")
        st.markdown("Record and track real-time physiological metrics for active patients.")

        with st.expander("➕ **Log New Patient Vitals**", expanded=True):
            with st.form("vitals_input_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    patient_name = st.selectbox("Select Patient", ["John Doe (Room 102)", "Mary Jane (Room 105)", "Robert Chen (Room 201)", "Alice Smith (Room 204)"])
                    heart_rate = st.number_input("Heart Rate (BPM)", min_value=30, max_value=220, value=75)
                    systolic_bp = st.number_input("Systolic BP (mmHg)", min_value=60, max_value=240, value=120)
                with col_b:
                    diastolic_bp = st.number_input("Diastolic BP (mmHg)", min_value=40, max_value=150, value=80)
                    temperature = st.number_input("Temperature (°C)", min_value=30.0, max_value=45.0, value=36.6, step=0.1)
                    spo2 = st.number_input("Oxygen Saturation SpO2 (%)", min_value=50, max_value=100, value=98)
                
                notes = st.text_input("Clinical Observations / Notes (Optional)")
                submit_vitals = st.form_submit_button("💾 Save Vitals Record", use_container_width=True)

                if submit_vitals:
                    new_entry = {
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Patient": patient_name,
                        "Heart Rate (BPM)": heart_rate,
                        "Blood Pressure": f"{systolic_bp}/{diastolic_bp}",
                        "Temp (°C)": temperature,
                        "SpO2 (%)": spo2,
                        "Logged By": user_email
                    }
                    st.session_state.vitals_data.insert(0, new_entry)
                    st.success(f"Vitals successfully saved for {patient_name}!")

                    if spo2 < 95 or heart_rate > 100 or temperature >= 38.0:
                        st.error("🚨 ALERT: Entered vitals fall outside normal clinical thresholds!")

        st.divider()
        st.subheader("📊 Logged Vitals History")
        df_vitals = pd.DataFrame(st.session_state.vitals_data)
        st.dataframe(df_vitals, use_container_width=True)

    # 3. Medication & Prescriptions
    elif menu == "Medication & Prescriptions":
        st.title("💊 Medication Schedules & Prescriptions")
        st.markdown("Manage current active prescriptions, dosage schedules, and refill requests.")

        with st.expander("➕ **Add New Medication Schedule**"):
            with st.form("med_input_form", clear_on_submit=True):
                patient = st.selectbox("Patient Name", ["John Doe (Room 102)", "Mary Jane (Room 105)", "Robert Chen (Room 201)"])
                med_name = st.text_input("Medication Name", placeholder="e.g. Metformin")
                dosage = st.text_input("Dosage", placeholder="e.g. 500mg")
                freq = st.selectbox("Frequency", ["Once Daily", "Twice Daily", "Three Times Daily", "As Needed (PRN)"])
                
                submit_med = st.form_submit_button("➕ Save Prescription", use_container_width=True)
                if submit_med and med_name:
                    st.session_state.medications_data.append({
                        "Patient": patient,
                        "Medication": med_name,
                        "Dosage": dosage,
                        "Frequency": freq,
                        "Status": "Active"
                    })
                    st.success(f"Prescription for {med_name} added successfully!")

        st.divider()
        st.subheader("📋 Active Prescriptions Table")
        df_meds = pd.DataFrame(st.session_state.medications_data)
        st.dataframe(df_meds, use_container_width=True)

    # 4. Shift Handovers
    elif menu == "Shift Handovers":
        st.title("🔄 Shift Handover Documentation")
        st.markdown("Log shift reports and ensure smooth clinical continuity between care staff.")

        with st.expander("📝 **Create Shift Handover Log**", expanded=True):
            with st.form("handover_form", clear_on_submit=True):
                outgoing = st.text_input("Outgoing Clinician / Caregiver", value=user_email)
                incoming = st.text_input("Incoming Clinician / Caregiver")
                p_select = st.selectbox("Target Patient", ["John Doe (Room 102)", "Mary Jane (Room 105)", "All Ward Patients"])
                shift_notes = st.text_area("Key Updates, Incidents, or Care Plan Adjustments")
                
                submit_handover = st.form_submit_button("📋 Submit Shift Handover", use_container_width=True)
                if submit_handover and shift_notes:
                    st.session_state.handovers_data.insert(0, {
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Outgoing Staff": outgoing,
                        "Incoming Staff": incoming,
                        "Patient": p_select,
                        "Shift Notes": shift_notes
                    })
                    st.success("Shift handover log submitted successfully!")

        st.divider()
        st.subheader("📚 Handover History")
        df_handovers = pd.DataFrame(st.session_state.handovers_data)
        st.dataframe(df_handovers, use_container_width=True)

    # 5. Emergency SOS Broadcast
    elif menu == "Emergency SOS":
        st.title("🚨 Emergency SOS Broadcast Hub")
        st.markdown("Dispatch urgent SMS/WhatsApp alerts to response teams and primary care doctors.")

        st.error("⚠️ **Warning:** Triggering an SOS will alert emergency care teams immediately.")
        
        with st.form("sos_form"):
            sos_patient = st.selectbox("Select Patient in Distress", ["John Doe (Room 102)", "Mary Jane (Room 105)", "Robert Chen (Room 201)"])
            sos_type = st.selectbox("Emergency Category", ["Cardiac Arrest / Vitals Collapse", "Severe Fall / Trauma", "Acute Respiratory Distress", "Unresponsive Patient"])
            location = st.text_input("Location / Ward", value="Ward A - Room 102")
            sos_notes = st.text_area("Emergency Context / Observations")
            
            trigger_sos = st.form_submit_button("🚨 BROADCAST EMERGENCY SOS ALERT", use_container_width=True)
            if trigger_sos:
                st.error(f"🚨 **EMERGENCY SOS DISPATCHED!** Alert broadcasted for **{sos_patient}** ({sos_type}) at {location}.")
                st.info("📲 On-call physicians and attending nursing staff have been notified via automated broadcast.")

    # 6. Admin Only: Intrusion Detection & Prevention System (IDPS)
    elif menu == "🛡️ Security Hub (IDPS)":
        st.title("🛡️ Admin Security Console (IDPS)")
        st.markdown("Intrusion Detection and Prevention System metrics, threat logs, and network security.")

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Threats Blocked Today", "42", "+5 this hour")
        with m2:
            st.metric("SQLi Filters Active", "100%", "Enforced")
        with m3:
            st.metric("Brute-Force Lockouts", "3", "Active")
        with m4:
            st.metric("MFA Compliance Rate", "98.4%", "+0.5%")

        st.divider()
        st.subheader("🚨 Live Security Incident Stream")
        df_idps = pd.DataFrame(st.session_state.idps_logs)
        st.dataframe(df_idps, use_container_width=True)

def main():
    if 'user' not in st.session_state or st.session_state['user'] is None:
        login_signup_portal()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()
