import streamlit as st
from supabase import create_client, Client

# Page Configuration
st.set_page_config(
    page_title="CareLink",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase Client (Replace with your actual Supabase URL and Anon Key)
SUPABASE_URL = "https://mkdvkaraqdjsxgxqjnhg.supabase.co/rest/v1"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1rZHZrYXJhcWRqc3hneHFqbmhnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ1NDgwMzMsImV4cCI6MjEwMDEyNDAzM30.bKkl_O1FtV1iMkbFsTKF06W8hOTpRYQbt7fpFdkGGaI"

@st.cache_resource
def init_supabase():
    # Sanitize the URL by removing trailing slashes and common subpaths
    clean_url = (
        SUPABASE_URL.strip()
        .rstrip("/")
        .replace("/rest/v1", "")
        .replace("/auth/v1", "")
    )
    return create_client(clean_url, SUPABASE_KEY)

supabase = init_supabase()

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
                    response = supabase.auth.sign_in_with_otp({
                        "email": email,
                        "options": {
                            "should_create_user": True
                        }
                    })
                    st.success("Verification code sent to your email inbox! Please check your messages.")
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
                        "options": {
                            "should_create_user": True
                        }
                    })
                    st.success("Registration code sent! Check your email to verify and complete signup.")
                except Exception as e:
                    st.error(f"Registration error: {e}")

def main_dashboard():
    # Updated Sidebar Heading
    st.sidebar.markdown("### 🩺 CareLink System")
    
    # Safely extract user email from Supabase User object
    user = st.session_state.get("user")
    user_email = getattr(user, "email", "User") if user else "User"
    st.sidebar.markdown(f"**Logged in as:** {user_email}")
    
    menu = st.sidebar.selectbox(
        "Navigation Menu", 
        ["Dashboard Overview", "Vitals Logs", "Medication & Prescriptions", "Shift Handovers", "Emergency SOS"]
    )
    
    if st.sidebar.button("Sign Out"):
        supabase.auth.sign_out()
        st.session_state.pop('user', None)
        st.rerun()
        
    if menu == "Dashboard Overview":
        st.title("CareLink Clinical Dashboard")
        st.markdown("Welcome to the centralized patient management and coordination hub.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Patients", "14", "+2 today")
        with col2:
            st.metric("Pending Refills", "3", "Action Required")
        with col3:
            st.metric("System Status", "Secure & Online", "100%")
            
    elif menu == "Vitals Logs":
        st.title("Patient Vitals Logs")
        st.info("Record and review real-time patient vitals including heart rate, blood pressure, and oxygen saturation.")
        
    elif menu == "Medication & Prescriptions":
        st.title("Medication Schedules & Prescriptions")
        st.info("Manage active prescriptions, dosages, and automated refill reminders.")
        
    elif menu == "Shift Handovers":
        st.title("Shift Handover Logs")
        st.info("Document clinical updates and review handovers between doctors and care teams.")
        
    elif menu == "Emergency SOS":
        st.title("Emergency SOS Broadcast")
        st.error("Trigger instant alerts and notifications to designated emergency responders and caregivers.")
