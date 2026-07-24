import streamlit as st
import pandas as pd
import random
import string
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
    SUPABASE_SERVICE_ROLE_KEY = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", None)
except Exception:
    SUPABASE_URL = "https://mkdvkaraqdjsxgxqjnhg.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1rZHZrYXJhcWRqc3hneHFqbmhnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ1NDgwMzMsImV4cCI6MjEwMDEyNDAzM30.bKkl_O1FtV1iMkbFsTKF06W8hOTpRYQbt7fpFdkGGaI"
    SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1rZHZrYXJhcWRqc3hneHFqbmhnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NDU0ODAzMywiZXhwIjoyMTAwMTI0MDMzfQ.IZgi6bai-Rr9hveCYRoHOkwL9n3VpqPwrIPa27hW0TY"

@st.cache_resource
def init_supabase():
    clean_url = SUPABASE_URL.strip().rstrip("/").replace("/rest/v1", "").replace("/auth/v1", "")
    return create_client(clean_url, SUPABASE_KEY)

@st.cache_resource
def init_supabase_admin():
    if SUPABASE_SERVICE_ROLE_KEY:
        clean_url = SUPABASE_URL.strip().rstrip("/").replace("/rest/v1", "").replace("/auth/v1", "")
        return create_client(clean_url, SUPABASE_SERVICE_ROLE_KEY)
    return None

supabase = init_supabase()

# Initialize Patient Access Codes Store
if "patient_access_codes" not in st.session_state:
    st.session_state.patient_access_codes = {
        "PAT-1020": "John Doe (Room 102)",
        "PAT-1050": "Mary Jane (Room 105)"
    }

# Initialize Clinical Data
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

if "idps_logs" not in st.session_state:
    st.session_state.idps_logs = [
        {"Timestamp": "2026-07-24 09:12:04", "IP Address": "192.168.1.104", "Event Type": "Uninvited Login Attempt", "Severity": "Medium", "Action Taken": "Access Denied"},
        {"Timestamp": "2026-07-24 08:45:12", "IP Address": "10.0.0.12", "Event Type": "SQLi Pattern Detected", "Severity": "Critical", "Action Taken": "Request Sanitized & Dropped"}
    ]

def login_signup_portal():
    st.markdown("<h1 style='text-align: center; color: #2563eb;'>🩺 CareLink Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Secure Healthcare Access for Staff & Patients</p>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["👨‍⚕️ Clinical Staff Sign In", "🏥 Patient Registration", "🔒 Access Info"])
    
    # 1. Staff Login
    with tab1:
        st.subheader("Invited Staff OTP Sign In")
        email = st.text_input("Staff Email Address", key="staff_signin_email", placeholder="doctor@hospital.org")
        
        if st.button("Send 6-Digit OTP Code", key="btn_staff_otp", use_container_width=True):
            if email:
                try:
                    supabase.auth.sign_in_with_otp({
                        "email": email,
                        "options": {"should_create_user": False}
                    })
                    st.success("Verification code sent to your email inbox!")
                except Exception as e:
                    st.error("Access Denied: Unregistered staff email. Contact your admin for an invitation.")
            else:
                st.warning("Please enter your registered staff email.")
        
        st.divider()
        otp_token = st.text_input("Enter 6-Digit OTP Code", type="password", key="staff_otp_token")
        if st.button("Verify & Login as Staff", key="btn_staff_login", use_container_width=True):
            if email and otp_token:
                try:
                    auth_response = supabase.auth.verify_otp({"email": email, "token": otp_token, "type": "email"})
                    if auth_response.session:
                        st.session_state['user'] = auth_response.user
                        st.success("Login successful!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Invalid or expired OTP: {e}")

    # 2. Patient Registration via Access Code
    with tab2:
        st.subheader("Activate Patient Access")
        st.caption("Enter the 6-digit Patient Access Code printed on your intake document or wristband.")
        
        p_email = st.text_input("Patient / Family Email Address", key="pat_email")
        access_code = st.text_input("Patient Access Code", key="pat_code", placeholder="PAT-1020").strip().upper()
        
        if st.button("Activate Account & Send OTP", key="btn_pat_reg", use_container_width=True):
            if p_email and access_code:
                if access_code in st.session_state.patient_access_codes:
                    linked_patient = st.session_state.patient_access_codes[access_code]
                    try:
                        # Register patient with linked metadata
                        supabase.auth.sign_in_with_otp({
                            "email": p_email,
                            "options": {
                                "should_create_user": True,
                                "data": {
                                    "full_name": linked_patient.split(" (")[0],
                                    "role": "patient",
                                    "linked_patient": linked_patient
                                }
                            }
                        })
                        st.success(f"Access Code verified for **{linked_patient}**! Verification code sent to {p_email}.")
                    except Exception as e:
                        st.error(f"Error sending code: {e}")
                else:
                    st.error("Invalid Patient Access Code. Please check your intake card or contact nursing staff.")
            else:
                st.warning("Please provide both your email and Patient Access Code.")

        st.divider()
        pat_otp = st.text_input("Enter 6-Digit OTP Code", type="password", key="pat_otp_token")
        if st.button("Verify & Enter Patient Portal", key="btn_pat_login", use_container_width=True):
            if p_email and pat_otp:
                try:
                    auth_response = supabase.auth.verify_otp({"email": p_email, "token": pat_otp, "type": "email"})
                    if auth_response.session:
                        st.session_state['user'] = auth_response.user
                        st.success("Welcome to your Patient Portal!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Invalid OTP code: {e}")

    # 3. Access Policy Info
    with tab3:
        st.subheader("Security & Privacy Guidelines")
        st.info("🔒 CareLink enforces strict role isolation. Staff require administrator invitations, while patients require verified wristband access codes issued during hospital intake.")

# Patient Restricted View
def patient_dashboard(user, user_metadata):
    full_name = user_metadata.get("full_name", "Patient")
    linked_patient = user_metadata.get("linked_patient", "")

    st.sidebar.markdown("### 🩺 CareLink Patient Portal")
    st.sidebar.markdown(f"**Patient:** `{full_name}`")
    st.sidebar.caption(f"🏥 **Linked Record:** `{linked_patient}`")
    st.sidebar.divider()
    
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        st.session_state.pop('user', None)
        st.rerun()

    st.title(f"👋 Welcome, {full_name}")
    st.markdown("Track your personal health vitals, active prescriptions, and care plan.")

    p_menu = st.tabs(["🫀 My Vitals History", "💊 My Prescriptions", "🚨 Request Assistance"])

    with p_menu[0]:
        st.subheader("Your Latest Health Metrics")
        # Filter vitals strictly for this patient
        my_vitals = [v for v in st.session_state.vitals_data if v["Patient"] == linked_patient]
        if my_vitals:
            df_my_vitals = pd.DataFrame(my_vitals)
            st.dataframe(df_my_vitals[["Timestamp", "Heart Rate (BPM)", "Blood Pressure", "Temp (°C)", "SpO2 (%)"]], use_container_width=True)
        else:
            st.info("No recorded vitals available for your profile yet.")

    with p_menu[1]:
        st.subheader("Your Active Prescriptions")
        # Filter medications strictly for this patient
        my_meds = [m for m in st.session_state.medications_data if m["Patient"] == linked_patient]
        if my_meds:
            df_my_meds = pd.DataFrame(my_meds)
            st.dataframe(df_my_meds[["Medication", "Dosage", "Frequency", "Status"]], use_container_width=True)
        else:
            st.info("No active prescription records found.")

    with p_menu[2]:
        st.subheader("🚨 Call Nurse / Request Assistance")
        st.markdown("Need urgent assistance in your room or from your assigned caregiver?")
        if st.button("🔔 CALL ATTENDING NURSE NOW", use_container_width=True):
            st.success(f"Notification sent to the nursing station for {linked_patient}!")

# Main Clinical & Staff Dashboard
def main_dashboard():
    user = st.session_state.get("user")
    user_metadata = getattr(user, "user_metadata", {}) or {}
    user_role = user_metadata.get("role", "doctor").lower()
    
    # Route Patient accounts to the restricted Patient Portal
    if user_role == "patient":
        patient_dashboard(user, user_metadata)
        return

    full_name = user_metadata.get("full_name", getattr(user, "email", "Staff"))

    # Sidebar Header
    st.sidebar.markdown("### 🩺 CareLink System")
    st.sidebar.markdown(f"**Staff:** `{full_name}`")
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
    
    # Navigation Options
    menu_options = [
        "Dashboard Overview", 
        "Patient Access Codes",
        "Vitals Logs", 
        "Medication & Prescriptions", 
        "Shift Handovers", 
        "Emergency SOS"
    ]
    
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
        st.markdown(f"Welcome back, **{full_name}**.")
        
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

    # 2. Patient Access Codes (Clinician Issue Hub)
    elif menu == "Patient Access Codes":
        st.title("🎫 Patient Intake & Access Code Issuer")
        st.markdown("Generate secure access codes to grant patients portal access.")

        with st.form("issue_code_form", clear_on_submit=True):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                p_name_input = st.text_input("Patient Full Name", placeholder="e.g. Robert Chen")
            with col_c2:
                p_room_input = st.text_input("Room / Ward Number", placeholder="e.g. Room 201")
            
            submit_gen_code = st.form_submit_button("🔑 Generate Patient Access Code", use_container_width=True)
            
            if submit_gen_code and p_name_input:
                new_code = f"PAT-{''.join(random.choices(string.digits, k=4))}"
                patient_label = f"{p_name_input} ({p_room_input})" if p_room_input else p_name_input
                st.session_state.patient_access_codes[new_code] = patient_label
                st.success(f"Access Code **`{new_code}`** generated for **{patient_label}**!")

        st.divider()
        st.subheader("📋 Active Patient Access Codes")
        df_codes = pd.DataFrame([{"Access Code": k, "Linked Patient Record": v} for k, v in st.session_state.patient_access_codes.items()])
        st.dataframe(df_codes, use_container_width=True)

    # 3. Vitals Logs
    elif menu == "Vitals Logs":
        st.title("🫀 Patient Vitals Tracker")
        with st.expander("➕ **Log New Patient Vitals**", expanded=True):
            with st.form("vitals_input_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    patient_name = st.selectbox("Select Patient", ["John Doe (Room 102)", "Mary Jane (Room 105)", "Robert Chen (Room 201)"])
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
                        "Logged By": full_name
                    }
                    st.session_state.vitals_data.insert(0, new_entry)
                    st.success(f"Vitals successfully saved for {patient_name}!")

        st.divider()
        st.dataframe(pd.DataFrame(st.session_state.vitals_data), use_container_width=True)

    # 4. Medication & Prescriptions
    elif menu == "Medication & Prescriptions":
        st.title("💊 Medication Schedules & Prescriptions")
        st.dataframe(pd.DataFrame(st.session_state.medications_data), use_container_width=True)

    # 5. Shift Handovers
    elif menu == "Shift Handovers":
        st.title("🔄 Shift Handover Documentation")
        st.dataframe(pd.DataFrame(st.session_state.handovers_data), use_container_width=True)

    # 6. Emergency SOS
    elif menu == "Emergency SOS":
        st.title("🚨 Emergency SOS Broadcast Hub")
        st.error("⚠️ Triggering an SOS will alert emergency care teams immediately.")

    # 7. Admin IDPS
    elif menu == "🛡️ Security Hub (IDPS)":
        st.title("🛡️ Admin Security Console (IDPS)")
        st.dataframe(pd.DataFrame(st.session_state.idps_logs), use_container_width=True)

def main():
    if 'user' not in st.session_state or st.session_state['user'] is None:
        login_signup_portal()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()
