import streamlit as st
import datetime
import os
from twilio.rest import Client

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CareLink Enterprise", 
    page_icon="💙", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME STATE INITIALIZATION ---
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light"

# --- PERSISTENT SESSION RESTORATION VIA QUERY PARAMS ---
if "user" not in st.session_state:
    saved_email = st.query_params.get("user_email")
    saved_role = st.query_params.get("user_role")
    
    if saved_email and saved_role:
        st.session_state.user = {"email": saved_email, "role": saved_role}
    else:
        st.session_state.user = None

# --- DYNAMIC THEME CSS INJECTION & FIXES ---
if st.session_state.theme_mode == "Dark":
    bg_color = "#0f172a"
    text_color = "#f8fafc"
    card_bg = "#1e293b"
    sidebar_bg = "#1e293b"
    border_color = "#334155"
    sub_text = "#94a3b8"
    toggle_icon_color = "#f8fafc"
else:
    bg_color = "#f8fafc"
    text_color = "#0f172a"
    card_bg = "#ffffff"
    sidebar_bg = "#f1f5f9"
    border_color = "#e2e8f0"
    sub_text = "#64748b"
    toggle_icon_color = "#1e293b"

st.markdown(f"""
<style>
    /* Global App Theme */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        border-right: 1px solid {border_color};
    }}
    
    [data-testid="stSidebar"] * {{
        color: {text_color} !important;
    }}
    
    /* Leftmost Sidebar Collapse/Expand Toggle Button Box Fixes */
    [data-testid="collapsedControl"] {{
        background-color: {card_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 999999;
    }}

    [data-testid="collapsedControl"] button {{
        background-color: transparent !important;
        border: none !important;
        color: {toggle_icon_color} !important;
    }}

    [data-testid="collapsedControl"] svg, 
    [data-testid="collapsedControl"] svg path {{
        fill: {toggle_icon_color} !important;
        stroke: {toggle_icon_color} !important;
        color: {toggle_icon_color} !important;
    }}
    
    /* Fix for Inline Code Blocks / Badges / User Email in Dark Mode */
    [data-testid="stSidebar"] code, [data-testid="stSidebar"] span[data-baseweb="tag"] {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
    }}
    
    /* Headers & Typography */
    h1, h2, h3, h4, h5, h6 {{
        color: {text_color} !important;
        font-weight: 700 !important;
    }}
    
    p, span, label, div {{
        color: {text_color};
    }}
    
    /* Form Containers & Cards */
    [data-testid="stForm"] {{
        background: {card_bg} !important;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid {border_color};
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    
    /* Expander Styling */
    .streamlit-expanderHeader {{
        background-color: {card_bg} !important;
        border-radius: 8px;
        border: 1px solid {border_color};
        color: {text_color} !important;
    }}
    
    /* Button Customization */
    .stButton>button {{
        border-radius: 8px;
        font-weight: 600;
        background-color: {card_bg};
        color: {text_color};
        border: 1px solid {border_color};
        transition: all 0.2s ease-in-out;
    }}

    /* Fix for Streamlit Main Menu (3 Dots) & Popover Dropdowns Text Visibility in Dark Mode */
    [data-testid="stMainMenuPopover"], [data-testid="stMainMenuPopover"] * {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
    }}
    
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"] {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1px solid {border_color} !important;
    }}

    div[data-baseweb="popover"] *, div[data-baseweb="menu"] *, ul[data-baseweb="menu"] * {{
        color: {text_color} !important;
        background-color: transparent !important;
    }}

    div[data-baseweb="menu"] li:hover, ul[data-baseweb="menu"] li:hover {{
        background-color: {border_color} !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "mock_db" not in st.session_state:
    st.session_state.mock_db = {
        "admin@carelink.com": ("password123", "Doctor / Admin"),
        "caregiver@carelink.com": ("password123", "Caregiver"),
        "family@carelink.com": ("password123", "Family / Patient")
    }

if "vitals_logs" not in st.session_state:
    st.session_state.vitals_logs = []

if "schedules" not in st.session_state:
    st.session_state.schedules = []

if "notifications" not in st.session_state:
    st.session_state.notifications = []

if "prescriptions" not in st.session_state:
    st.session_state.prescriptions = []

if "emergency_config" not in st.session_state:
    st.session_state.emergency_config = {"contact": "", "patient": ""}

if "clinical_notes" not in st.session_state:
    st.session_state.clinical_notes = []

if "shift_logs" not in st.session_state:
    st.session_state.shift_logs = []

# --- TWILIO CONFIGURATION CONSTANTS ---
TWILIO_SID = "AC734de765447250919ce5675f390cdce2"
TWILIO_TOKEN = "3a62e0dfeedf90c44defebff884f88ea"

# --- LOCAL AUTH PORTAL WITH RBAC ---
def login_signup_portal():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>💙 CareLink</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: {sub_text};'>Enterprise Health-Tech & Patient Management Platform</p><br>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Secure Login", "New Account Signup"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Access Portal", use_container_width=True)
                
                if submit_login:
                    if not email or not password:
                        st.error("Please fill in all fields.")
                    elif email in st.session_state.mock_db and st.session_state.mock_db[email][0] == password:
                        role = st.session_state.mock_db[email][1]
                        st.session_state.user = {"email": email, "role": role}
                        st.query_params["user_email"] = email
                        st.query_params["user_role"] = role
                        st.success(f"Authenticated as {role}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                        
        with tab2:
            with st.form("signup_form"):
                new_email = st.text_input("Email Address")
                new_password = st.text_input("Password", type="password")
                selected_role = st.selectbox("Select Account Role", ["Caregiver", "Family / Patient", "Doctor / Admin"])
                submit_signup = st.form_submit_button("Register Account", use_container_width=True)
                
                if submit_signup:
                    if not new_email or not new_password:
                        st.error("Please provide a valid email and password.")
                    elif new_email in st.session_state.mock_db:
                        st.warning("Account already exists. Please log in.")
                    else:
                        st.session_state.mock_db[new_email] = (new_password, selected_role)
                        st.session_state.user = {"email": new_email, "role": selected_role}
                        st.query_params["user_email"] = new_email
                        st.query_params["user_role"] = selected_role
                        st.success(f"Account created as {selected_role}!")
                        st.rerun()

def main_dashboard():
    user_data = st.session_state.user
    if isinstance(user_data, dict):
        user_email = user_data.get("email", "unknown@carelink.com")
        user_role = user_data.get("role", "Caregiver")
    else:
        user_email = getattr(user_data, 'email', "unknown@carelink.com")
        user_role = getattr(user_data, 'role', "Caregiver")

    # --- SIDEBAR CONTROLS & NAVIGATION ---
    st.sidebar.markdown("### 💙 CareLink System")
    st.sidebar.markdown(f"**User:** `{user_email}`")
    st.sidebar.markdown(f"**Access Tier:** `{user_role}`")
    st.sidebar.markdown("---")
    
    # Theme Selection Menu in Sidebar
    st.sidebar.markdown("### ⚙️ Settings")
    current_theme_index = 0 if st.session_state.theme_mode == "Light" else 1
    chosen_theme = st.sidebar.radio("System Mode", ["Light", "Dark"], index=current_theme_index, horizontal=True)
    if chosen_theme != st.session_state.theme_mode:
        st.session_state.theme_mode = chosen_theme
        st.rerun()

    st.sidebar.markdown("---")
    
    if user_role == "Doctor / Admin":
        nav_options = [
            "Dashboard Overview", 
            "Vitals Log", 
            "Care Schedule", 
            "Prescription Tracker", 
            "Clinical Notes Vault", 
            "Shift Handover Logs",
            "Patient Reminders (SMS/WhatsApp)", 
            "Emergency SOS", 
            "Family Profiles"
        ]
    elif user_role == "Caregiver":
        nav_options = [
            "Dashboard Overview", 
            "Vitals Log", 
            "Care Schedule", 
            "Prescription Tracker", 
            "Shift Handover Logs",
            "Patient Reminders (SMS/WhatsApp)", 
            "Emergency SOS"
        ]
    else:  # Family / Patient
        nav_options = [
            "Dashboard Overview", 
            "Vitals Log", 
            "Care Schedule", 
            "Prescription Tracker",
            "Clinical Notes Vault",
            "Emergency SOS"
        ]

    menu = st.sidebar.radio("Navigation Menu", nav_options)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Log Out of Session", use_container_width=True):
        st.session_state.user = None
        st.query_params.clear()
        st.rerun()
        
    # --- DASHBOARD VIEWS ---
    if menu == "Dashboard Overview":
        st.title("Dashboard Overview")
        st.markdown(f"Welcome back. You are viewing the clinical workspace under **{user_role}** permissions.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Vitals Logged", len(st.session_state.vitals_logs))
        with col2:
            st.metric("Active Prescriptions", len(st.session_state.prescriptions))
        with col3:
            st.metric("Shift Handover Logs", len(st.session_state.shift_logs))
        with col4:
            st.metric("Security Level", user_role.split()[0])

    elif menu == "Vitals Log":
        st.title("🩺 Patient Vitals Monitor")
        st.markdown("Record, monitor, and audit patient vital signs in real-time.")
        
        if user_role != "Family / Patient":
            with st.form("vitals_form"):
                col1, col2 = st.columns(2)
                with col1:
                    patient_name = st.text_input("Patient Full Name")
                    bp = st.text_input("Blood Pressure (e.g., 120/80)")
                with col2:
                    heart_rate = st.number_input("Heart Rate (bpm)", min_value=40, max_value=200, value=75)
                    temp = st.number_input("Temperature (°C)", min_value=35.0, max_value=42.0, value=36.6, format="%.1f")
                
                submit_vitals = st.form_submit_button("Record Vitals Entry", use_container_width=True)
                if submit_vitals:
                    if patient_name:
                        entry = {
                            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "patient": patient_name,
                            "bp": bp,
                            "hr": heart_rate,
                            "temp": temp
                        }
                        st.session_state.vitals_logs.append(entry)
                        st.success("Vitals successfully saved to patient record!")
                    else:
                        st.error("Please enter the patient's name.")
        else:
            st.info("ℹ️ Family Portal View: Read-only access to recorded patient vitals history.")
                    
        if st.session_state.vitals_logs:
            st.markdown("### Historical Vitals Ledger")
            st.dataframe(st.session_state.vitals_logs, use_container_width=True)
        else:
            st.info("No vitals logged in the system yet.")

    elif menu == "Care Schedule":
        st.title("📅 Care & Medication Schedule")
        st.markdown("Coordinate daily care duties, therapeutic schedules, and appointments.")
        
        if user_role != "Family / Patient":
            with st.form("schedule_form"):
                task = st.text_input("Care Task / Medication Name")
                time_slot = st.text_input("Due Time (e.g., Today at 2:00 PM)")
                notes = st.text_area("Task Instructions / Notes")
                
                submit_sched = st.form_submit_button("Add Task to Schedule", use_container_width=True)
                if submit_sched:
                    if task:
                        st.session_state.schedules.append({"Task": task, "Time": time_slot, "Notes": notes})
                        st.success("Task scheduled successfully!")
                    else:
                        st.error("Please enter a task name.")
                    
        if st.session_state.schedules:
            st.markdown("### Scheduled Operations")
            for item in st.session_state.schedules:
                with st.expander(f"📌 {item['Task']} — {item['Time']}"):
                    st.write(f"**Instructions:** {item['Notes']}")
        else:
            st.info("No items on the care schedule yet.")

    elif menu == "Prescription Tracker":
        st.title("💊 Prescription & Refill Manager")
        st.markdown("Track active pharmacological inventories and trigger automated refill alerts.")
        
        if user_role != "Family / Patient":
            with st.form("rx_form"):
                col1, col2 = st.columns(2)
                with col1:
                    rx_patient = st.text_input("Patient Full Name")
                    med_name = st.text_input("Medication Name & Strength")
                with col2:
                    dosage = st.text_input("Dosage Instructions")
                    pill_count = st.number_input("Remaining Pill Count", min_value=0, max_value=500, value=30)
                    
                rx_contact = st.text_input("Pharmacy / Caregiver WhatsApp Number (e.g., +234...)")
                
                submit_rx = st.form_submit_button("Save Prescription", use_container_width=True)
                if submit_rx:
                    if rx_patient and med_name:
                        st.session_state.prescriptions.append({
                            "patient": rx_patient,
                            "medication": med_name,
                            "dosage": dosage,
                            "count": pill_count,
                            "contact": rx_contact
                        })
                        st.success(f"Prescription for {med_name} registered!")
                    else:
                        st.error("Please provide patient and medication names.")
                    
        if st.session_state.prescriptions:
            st.markdown("### Active Inventory Database")
            for idx, rx in enumerate(st.session_state.prescriptions):
                badge = "🔴 URGENT REFILL" if rx["count"] <= 7 else "🟢 Stock Stable"
                
                with st.expander(f"{rx['medication']} | Patient: {rx['patient']} [{badge}]"):
                    st.write(f"**Dosage Guidelines:** {rx['dosage']}")
                    st.write(f"**Pills Remaining:** {rx['count']}")
                    st.write(f"**Contact Channel:** {rx['contact'] if rx['contact'] else 'Not configured'}")
                    
                    if user_role != "Family / Patient":
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("Dispense 1 Pill (-1)", key=f"dispense_{idx}"):
                                if rx["count"] > 0:
                                    rx["count"] -= 1
                                    st.rerun()
                        with col_b:
                            if st.button("📲 Send WhatsApp Refill Alert", key=f"refill_{idx}"):
                                if not rx["contact"]:
                                    st.error("Please add a contact phone number first.")
                                else:
                                    try:
                                        client = Client(TWILIO_SID, TWILIO_TOKEN)
                                        refill_msg = f"REFILL ALERT: Patient {rx['patient']} is running low on {rx['medication']} ({rx['count']} pills left). - CareLink"
                                        client.messages.create(body=refill_msg, from_="whatsapp:+14155238886", to=f"whatsapp:{rx['contact']}")
                                        st.success("WhatsApp refill alert dispatched!")
                                    except Exception as e:
                                        st.error(f"Transmission failed: {e}")
        else:
            st.info("No active prescriptions tracked.")

    elif menu == "Clinical Notes Vault":
        st.title("📋 Encrypted Clinical Notes & Patient History")
        st.markdown("Maintain longitudinal physician logs, assessments, and medical notes.")
        
        if user_role == "Doctor / Admin":
            with st.form("clinical_form"):
                col1, col2 = st.columns(2)
                with col1:
                    note_patient = st.text_input("Patient Full Name")
                    category = st.selectbox("Category", ["Physician Consultation", "Daily Observation", "Dietary / Nutrition", "Incident Report"])
                with col2:
                    provider_name = st.text_input("Clinician Name (e.g., Dr. Adams)")
                
                note_body = st.text_area("Clinical Observations")
                submit_note = st.form_submit_button("Commit Note to Secure Vault", use_container_width=True)
                
                if submit_note:
                    if note_patient and note_body:
                        st.session_state.clinical_notes.append({
                            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "patient": note_patient,
                            "category": category,
                            "provider": provider_name if provider_name else "Doctor Admin",
                            "body": note_body
                        })
                        st.success("Clinical note securely archived!")
                    else:
                        st.error("Please provide both patient name and note body.")
        else:
            st.info("ℹ️ Read-only access to clinical observation vault.")
                    
        if st.session_state.clinical_notes:
            st.markdown("### Archived Clinical Records")
            for note in reversed(st.session_state.clinical_notes):
                with st.expander(f"[{note['category']}] {note['patient']} — {note['time']} (Dr. {note['provider']})"):
                    st.write(note['body'])
        else:
            st.info("Vault is currently empty.")

    elif menu == "Shift Handover Logs":
        st.title("🔄 Caregiver Shift Handover & Duty Log")
        st.markdown("Seamlessly transfer observations, meal intake, and pending tasks between shifts.")
        
        with st.form("shift_form"):
            col1, col2 = st.columns(2)
            with col1:
                shift_patient = st.text_input("Patient Full Name")
                shift_name = st.selectbox("Duty Shift", ["Morning Shift (07:00 - 15:00)", "Evening Shift (15:00 - 23:00)", "Night Shift (23:00 - 07:00)"])
            with col2:
                outgoing_caregiver = st.text_input("Outgoing Caregiver Name")
                mood_status = st.selectbox("Patient General Mood", ["Stable & Calm", "Cheerful", "Anxious / Restless", "Lethargic", "In Pain"])
            
            meal_notes = st.text_input("Meal & Hydration Status")
            sleep_notes = st.text_input("Sleep & Rest Summary")
            pending_tasks = st.text_area("Pending Tasks / Warnings for Incoming Shift")
            
            submit_shift = st.form_submit_button("Submit Handover Log", use_container_width=True)
            if submit_shift:
                if shift_patient and outgoing_caregiver:
                    st.session_state.shift_logs.append({
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "patient": shift_patient,
                        "shift": shift_name,
                        "caregiver": outgoing_caregiver,
                        "mood": mood_status,
                        "meals": meal_notes,
                        "sleep": sleep_notes,
                        "pending": pending_tasks
                    })
                    st.success("Shift handover recorded successfully!")
                else:
                    st.error("Please fill in patient name and caregiver name.")
                    
        if st.session_state.shift_logs:
            st.markdown("### Handover Feed")
            for log in reversed(st.session_state.shift_logs):
                with st.expander(f"🔄 [{log['shift']}] {log['patient']} — Handed over by {log['caregiver']}"):
                    st.write(f"**Patient Mood:** {log['mood']}")
                    st.write(f"**Meals & Hydration:** {log['meals']}")
                    st.write(f"**Sleep Summary:** {log['sleep']}")
                    st.write(f"**Pending Tasks:** {log['pending']}")

    elif menu == "Patient Reminders (SMS/WhatsApp)":
        st.title("🔔 SMS & WhatsApp Notification Center")
        st.markdown("Dispatch appointment alerts and operational notifications via Twilio.")
        
        with st.form("sms_form"):
            col1, col2 = st.columns(2)
            with col1:
                patient_name = st.text_input("Recipient Patient Name")
                phone_number = st.text_input("Phone Number (with country code, e.g., +234...)")
            with col2:
                channel = st.selectbox("Delivery Channel", ["SMS", "WhatsApp"])
                appointment_time = st.text_input("Appointment / Event Details")
            
            custom_msg = st.text_area("Message Preview", value=f"Hello {patient_name}, reminder for your upcoming session on {appointment_time}. - CareLink")
            
            submit_sms = st.form_submit_button("Dispatch Live Message", use_container_width=True)
            if submit_sms:
                if not phone_number or not patient_name:
                    st.error("Please provide both patient name and phone number.")
                else:
                    try:
                        client = Client(TWILIO_SID, TWILIO_TOKEN)
                        sender = "whatsapp:+14155238886" if channel == "WhatsApp" else "+15017122661"
                        recipient = f"whatsapp:{phone_number}" if channel == "WhatsApp" else phone_number
                        
                        message = client.messages.create(body=custom_msg, from_=sender, to=recipient)
                        st.success(f"Message dispatched via {channel}! (SID: {message.sid})")
                        st.session_state.notifications.append({
                            "patient": patient_name, "phone": phone_number, "channel": channel, "message": custom_msg, "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                    except Exception as e:
                        st.error(f"Transmission failed: {e}")
                        
        if st.session_state.notifications:
            st.markdown("### Dispatched Notifications Log")
            for n in st.session_state.notifications:
                with st.expander(f"📱 [{n['channel']}] To: {n['patient']} ({n['time']})"):
                    st.write(f"**Content:** {n['message']}")

    elif menu == "Emergency SOS":
        st.title("🚨 Emergency SOS & Panic Center")
        st.error("⚠️ Use this section in critical medical emergencies to instantly alert emergency responders or doctors.")
        
        with st.form("sos_setup_form"):
            st.markdown("### Emergency Recipient Configuration")
            sos_patient = st.text_input("Patient Full Name", value=st.session_state.emergency_config["patient"])
            sos_contact = st.text_input("Emergency Contact Phone Number (+234...)", value=st.session_state.emergency_config["contact"])
            
            save_sos = st.form_submit_button("Save Emergency Configuration", use_container_width=True)
            if save_sos:
                if sos_patient and sos_contact:
                    st.session_state.emergency_config["patient"] = sos_patient
                    st.session_state.emergency_config["contact"] = sos_contact
                    st.success("Emergency settings saved!")
                else:
                    st.error("Please fill in both fields.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚨 TRIGGER EMERGENCY SOS BROADCAST", type="primary", use_container_width=True):
            current_patient = st.session_state.emergency_config["patient"]
            current_contact = st.session_state.emergency_config["contact"]
            
            if not current_patient or not current_contact:
                st.error("Emergency config incomplete! Please save a patient name and contact number above first.")
            else:
                try:
                    client = Client(TWILIO_SID, TWILIO_TOKEN)
                    sos_msg = f"🚨 MEDICAL EMERGENCY SOS 🚨: Immediate assistance required for patient {current_patient}. Please respond immediately! - CareLink"
                    message = client.messages.create(body=sos_msg, from_="whatsapp:+14155238886", to=f"whatsapp:{current_contact}")
                    st.success(f"Emergency SOS WhatsApp successfully broadcasted! (SID: {message.sid})")
                except Exception as e:
                    st.error(f"Failed to broadcast emergency alert: {e}")

    elif menu == "Family Profiles":
        st.title("👨‍👩‍👧 Family & Care Recipient Profiles")
        st.markdown("Manage care network contacts and client profiles.")
        st.info("Directory section under construction.")

# --- APP ROUTING CONTROL ---
if st.session_state.user is None:
    login_signup_portal()
else:
    main_dashboard()
