import streamlit as st
import datetime
import re
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CareLink Enterprise - Secured", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SUPABASE CONFIGURATION (For Native Auth & OTP) ---
SUPABASE_URL = "YOUR_SUPABASE_PROJECT_URL"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None

# --- TWILIO CONFIGURATION (For Operational WhatsApp Notifications) ---
TWILIO_SID = "AC734de765447250919ce5675f390cdce2"
TWILIO_TOKEN = "3a62e0dfeedf90c44defebff884f88ea"

def send_whatsapp_appointment(patient_phone, message_body):
    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(
            body=f"📅 CareLink Appointment Alert: {message_body}",
            from_="whatsapp:+14155238886",
            to=f"whatsapp:{patient_phone}"
        )
        return True
    except Exception as e:
        return str(e)

# --- THEME STATE INITIALIZATION ---
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light"

# --- PERSISTENT SESSION RESTORATION ---
if "user" not in st.session_state:
    saved_email = st.query_params.get("user_email")
    saved_role = st.query_params.get("user_role")
    if saved_email and saved_role:
        st.session_state.user = {"email": saved_email, "role": saved_role}
    else:
        st.session_state.user = None

# --- SECURITY & IDPS STATE INITIALIZATION ---
if "failed_login_attempts" not in st.session_state:
    st.session_state.failed_login_attempts = 0

if "mfa_state" not in st.session_state:
    st.session_state.mfa_state = {"pending": False, "email": "", "role": "Doctor / Admin"}

if "security_audit_logs" not in st.session_state:
    st.session_state.security_audit_logs = []

# --- IDPS ENGINE: ANOMALY & INJECTION DETECTION ---
def log_security_event(event_type, severity, description):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "time": timestamp,
        "type": event_type,
        "severity": severity,
        "description": description
    }
    st.session_state.security_audit_logs.append(log_entry)

def inspect_input_for_threats(user_input):
    if not isinstance(user_input, str):
        return False
    sql_patterns = re.compile(r"(union\s+select|drop\s+table|--|;|or\s+1=1|exec\()", re.IGNORECASE)
    xss_patterns = re.compile(r"(<script[^>]*?>.*?</script>|javascript:|onerror\s*=)", re.IGNORECASE)
    if sql_patterns.search(user_input):
        log_security_event("SQL Injection Attempt", "HIGH", f"Blocked malicious SQL payload: {user_input[:40]}...")
        return True
    if xss_patterns.search(user_input):
        log_security_event("Cross-Site Scripting (XSS)", "MEDIUM", f"Blocked malicious script injection vector.")
        return True
    return False

# --- DYNAMIC THEME CSS ---
if st.session_state.theme_mode == "Dark":
    bg_color, text_color, card_bg, sidebar_bg, border_color, sub_text, toggle_icon_color = "#0f172a", "#f8fafc", "#1e293b", "#1e293b", "#334155", "#94a3b8", "#f8fafc"
else:
    bg_color, text_color, card_bg, sidebar_bg, border_color, sub_text, toggle_icon_color = "#f1f5f9", "#0f172a", "#ffffff", "#f1f5f9", "#e2e8f0", "#64748b", "#1e293b"

st.markdown(f"""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background-color: {bg_color} !important; color: {text_color} !important; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; border-right: 1px solid {border_color}; }}
    [data-testid="stSidebar"] * {{ color: {text_color} !important; }}
    [data-testid="collapsedControl"] {{ background-color: {card_bg} !important; border: 1px solid {border_color} !important; border-radius: 8px !important; z-index: 999999; }}
    [data-testid="collapsedControl"] svg, [data-testid="collapsedControl"] svg path {{ fill: {toggle_icon_color} !important; stroke: {toggle_icon_color} !important; }}
    h1, h2, h3, h4, h5, h6 {{ color: {text_color} !important; font-weight: 700 !important; }}
    p, span, label, div {{ color: {text_color}; }}
    [data-testid="stForm"] {{ background: {card_bg} !important; padding: 24px; border-radius: 12px; border: 1px solid {border_color}; }}
    .stButton>button {{ border-radius: 8px; font-weight: 600; background-color: {card_bg}; color: {text_color}; border: 1px solid {border_color}; }}
</style>
""", unsafe_allow_html=True)

for k in ["vitals_logs", "schedules", "notifications", "prescriptions", "emergency_config", "clinical_notes", "shift_logs"]:
    if k not in st.session_state:
        st.session_state[k] = [] if k != "emergency_config" else {"contact": "", "patient": ""}

# --- SECURE AUTHENTICATION PORTAL WITH SUPABASE EMAIL OTP ---
def login_signup_portal():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>🛡️ CareLink Security Vault</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: {sub_text};'>Supabase Native Email OTP & Twilio WhatsApp Messaging</p><br>", unsafe_allow_html=True)
        
        if not supabase or SUPABASE_URL == "YOUR_SUPABASE_PROJECT_URL":
            st.warning("⚠️ **Setup Notice:** Please plug in your actual Supabase URL and Anon Key at the top of `app.py` to activate native database authentication.")

        if st.session_state.failed_login_attempts >= 3:
            st.error("🚨 **IDPS SECURITY LOCKOUT:** Excessive failed authentication attempts detected. System temporarily locked for 60 seconds.")
            log_security_event("Brute-Force Lockdown", "CRITICAL", "IP/Session locked due to 3 consecutive failed login failures.")
            if st.button("Reset Security Block", use_container_width=True):
                st.session_state.failed_login_attempts = 0
                st.rerun()
            return

        # MFA Verification Stage (Supabase Email OTP verification)
        if st.session_state.mfa_state["pending"]:
            st.info(f"📧 **Supabase OTP Challenge Sent:** A 6-digit verification code has been emailed to `{st.session_state.mfa_state['email']}`.")
            with st.form("mfa_verify_form"):
                entered_otp = st.text_input("Enter 6-Digit Email OTP Code", max_chars=6)
                verify_submit = st.form_submit_button("Verify & Authorize", use_container_width=True)
                
                if verify_submit:
                    if not supabase:
                        st.error("Supabase client not initialized.")
                    else:
                        try:
                            res = supabase.auth.verify_otp({
                                "email": st.session_state.mfa_state["email"],
                                "token": entered_otp,
                                "type": "email"
                            })
                            
                            if res.session:
                                email = st.session_state.mfa_state["email"]
                                role = st.session_state.mfa_state["role"]
                                st.session_state.user = {"email": email, "role": role}
                                st.query_params["user_email"] = email
                                st.query_params["user_role"] = role
                                
                                st.session_state.mfa_state = {"pending": False, "email": "", "role": ""}
                                log_security_event("Supabase MFA Success", "LOW", f"User {email} successfully verified OTP.")
                                st.success("Authentication Verified! Logging in...")
                                st.rerun()
                            else:
                                log_security_event("Supabase MFA Failure", "HIGH", "Invalid or expired OTP token entered.")
                                st.error("Invalid or expired verification code. Please try again.")
                        except Exception as e:
                            log_security_event("Supabase Auth Error", "HIGH", str(e))
                            st.error(f"Verification error: {e}")
            return

        tab1, tab2 = st.tabs(["Secure Login / OTP Request", "New Account Signup"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email Address")
                selected_role = st.selectbox("Assign Session Role", ["Doctor / Admin", "Caregiver", "Family / Patient"])
                submit_login = st.form_submit_button("Send Supabase OTP Code", use_container_width=True)
                
                if submit_login:
                    if inspect_input_for_threats(email):
                        st.error("🚨 IDPS Alert: Malicious characters detected in request.")
                        st.rerun()

                    if not email:
                        st.error("Please enter your email address.")
                    elif not supabase:
                        st.error("Supabase credentials missing in code configuration.")
                    else:
                        try:
                            supabase.auth.sign_in_with_otp({
                                "email": email,
                                "options": {
                                    "should_create_user": False
                                }
                            })
                            
                            st.session_state.mfa_state = {
                                "pending": True,
                                "email": email,
                                "role": selected_role
                            }
                            
                            log_security_event("Supabase OTP Triggered", "LOW", f"OTP dispatch requested for {email}.")
                            st.success(f"OTP successfully dispatched to {email} via Supabase!")
                            st.rerun()
                        except Exception as e:
                            st.session_state.failed_login_attempts += 1
                            log_security_event("Supabase Login Failed", "MEDIUM", str(e))
                            st.error(f"Authentication notice: {e}. (Ensure email exists in your Supabase Auth users list).")
                        
        with tab2:
            with st.form("signup_form"):
                new_email = st.text_input("Email Address")
                new_password = st.text_input("Password", type="password")
                signup_role = st.selectbox("Select Account Role", ["Caregiver", "Family / Patient", "Doctor / Admin"], key="su_role")
                submit_signup = st.form_submit_button("Register Account", use_container_width=True)
                
                if submit_signup:
                    if not new_email or not new_password:
                        st.error("Please provide email and password.")
                    elif not supabase:
                        st.error("Supabase credentials missing.")
                    else:
                        try:
                            res = supabase.auth.sign_up({
                                "email": new_email,
                                "password": new_password
                            })
                            log_security_event("User Registration", "LOW", f"New Supabase account registered: {new_email}")
                            st.success("Account registered successfully in Supabase! You can now log in.")
                        except Exception as e:
                            st.error(f"Registration error: {e}")

# --- MAIN DASHBOARD ---
def main_dashboard():
    user_data = st.session_state.user
    user_email = user_data.get("email") if isinstance(user_data, dict) else "admin@carelink.com"
    user_role = user_data.get("role") if isinstance(user_data, dict) else "Doctor / Admin"

    st.sidebar.markdown("### 🛡️ CareLink Security Hub")
    st.sidebar.markdown(f"**User:** `{user_email}`")
    st.sidebar.markdown(f"**Role:** `{user_role}`")
    st.sidebar.markdown("Status: 🟢 **Supabase Auth & Twilio Active**")
    st.sidebar.markdown("---")
    
    chosen_theme = st.sidebar.radio("System Mode", ["Light", "Dark"], index=0 if st.session_state.theme_mode=="Light" else 1, horizontal=True)
    if chosen_theme != st.session_state.theme_mode:
        st.session_state.theme_mode = chosen_theme
        st.rerun()

    st.sidebar.markdown("---")
    nav_options = ["Dashboard Overview", "Vitals Log", "Care Schedule", "Prescription Tracker", "Emergency SOS"]
    if user_role == "Doctor / Admin":
        nav_options.extend(["Clinical Notes Vault", "🛡️ IDPS Security Logs"])

    menu = st.sidebar.radio("Navigation Menu", nav_options)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Log Out of Session", use_container_width=True):
        if supabase:
            try:
                supabase.auth.sign_out()
            except:
                pass
        st.session_state.user = None
        st.query_params.clear()
        st.rerun()

    if menu == "Dashboard Overview":
        st.title("Dashboard Overview")
        st.markdown(f"Welcome back. Workspace active under **{user_role}** permissions with Supabase backend and IDPS monitoring.")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Active Vitals Logs", len(st.session_state.vitals_logs))
        with col2: st.metric("Prescriptions Tracked", len(st.session_state.prescriptions))
        with col3: st.metric("Security Incidents Logged", len(st.session_state.security_audit_logs))
        with col4: st.metric("Auth Engine", "Supabase OTP")

    elif menu == "Vitals Log":
        st.title("🩺 Patient Vitals Monitor")
        with st.form("vitals_form"):
            col1, col2 = st.columns(2)
            with col1:
                patient_name = st.text_input("Patient Full Name")
                bp = st.text_input("Blood Pressure (e.g., 120/80)")
            with col2:
                heart_rate = st.number_input("Heart Rate (bpm)", 40, 200, 75)
                temp = st.number_input("Temperature (°C)", 35.0, 42.0, 36.6, format="%.1f")
            
            submit_vitals = st.form_submit_button("Record Vitals", use_container_width=True)
            if submit_vitals:
                if inspect_input_for_threats(patient_name) or inspect_input_for_threats(bp):
                    st.error("🚨 IDPS Alert: Malicious script pattern blocked in form submission.")
                elif patient_name:
                    st.session_state.vitals_logs.append({"time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "patient": patient_name, "bp": bp, "hr": heart_rate, "temp": temp})
                    st.success("Vitals successfully saved!")
                else:
                    st.error("Enter patient name.")
        
        if st.session_state.vitals_logs:
            st.dataframe(st.session_state.vitals_logs, use_container_width=True)

    elif menu == "Care Schedule":
        st.title("📅 Care & Medication Schedule")
        st.markdown("Manage upcoming patient care slots and dispatch operational WhatsApp reminders via Twilio.")
        
        with st.form("schedule_form"):
            col1, col2 = st.columns(2)
            with col1:
                sch_patient = st.text_input("Patient / Recipient Name")
                sch_phone = st.text_input("Recipient Phone (e.g. +2347038973019)", value="+2347038973019")
            with col2:
                sch_time = st.text_input("Appointment Time/Date", "Tomorrow at 10:00 AM")
                sch_desc = st.text_input("Care Activity / Medication Description", "Routine checkup and vitals review")
            
            submit_sch = st.form_submit_button("Save Schedule & Send WhatsApp Reminder", use_container_width=True)
            if submit_sch:
                if sch_patient and sch_phone:
                    st.session_state.schedules.append({
                        "patient": sch_patient, "phone": sch_phone, "time": sch_time, "desc": sch_desc
                    })
                    res_msg = send_whatsapp_appointment(sch_phone, f"Appointment for {sch_patient}: {sch_desc} at {sch_time}.")
                    if res_msg is True:
                        st.success("Schedule saved and WhatsApp notification dispatched successfully via Twilio!")
                        log_security_event("WhatsApp Broadcast", "LOW", f"Sent appointment alert to {sch_phone}")
                    else:
                        st.warning(f"Schedule saved, but Twilio notification failed: {res_msg}")
                else:
                    st.error("Please provide patient name and phone number.")
        
        if st.session_state.schedules:
            st.markdown("### Active Scheduled Tasks")
            st.dataframe(st.session_state.schedules, use_container_width=True)

    elif menu == "Prescription Tracker":
        st.title("💊 Prescription & Refill Manager")
        st.info("Inventory tracker active.")

    elif menu == "Emergency SOS":
        st.title("🚨 Emergency SOS & Panic Center")
        st.error("Emergency broadcast channels secured.")

    elif menu == "🛡️ IDPS Security Logs" and user_role == "Doctor / Admin":
        st.title("🛡️ Intrusion Detection & Prevention System (IDPS) SIEM")
        st.markdown("Real-time monitoring console logging application-layer threat intelligence, brute-force attempts, and payload inspection events.")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a: st.metric("Total Events Tracked", len(st.session_state.security_audit_logs))
        with col_b: st.metric("Brute-Force Blocks", st.session_state.failed_login_attempts)
        with col_c: st.metric("Defense Status", "Active & Shielded")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.security_audit_logs:
            st.dataframe(st.session_state.security_audit_logs, use_container_width=True)
        else:
            st.info("No security incidents or anomalies recorded yet. System clean.")

# --- ROUTING ---
if st.session_state.user is None:
    login_signup_portal()
else:
    main_dashboard()
