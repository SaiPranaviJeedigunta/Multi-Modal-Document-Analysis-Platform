import streamlit as st
from utils.api_client import APIClient
from utils.config import load_config
from utils.navigation import navigate_to

# Load configuration settings
config = load_config()
backend_url = config["backend_url"]

def render():
    # Initialize API client if not in session state
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient()

    # Page Title and Subheader with Styling
    st.markdown(
        "<h1 style='text-align: center; color: #F5F5F5; font-size: 36px; margin-bottom: 0;'>🔐 Login to the Application</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<h4 style='text-align: center; color: #D3D3D3; font-size: 18px; margin-top: 0;'>Please enter your login credentials</h4>",
        unsafe_allow_html=True
    )
    st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)

    # Centering form content
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Input fields for email and password with placeholders
        email = st.text_input("📧 Email Address", placeholder="Enter your email")
        password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")

        # Placeholder area for displaying messages
        message_area = st.empty()

        # Mock credentials for testing
        test_email = "test@example.com"
        test_password = "password123"

        # Login Button with styling
        if st.button("🔓 Login", help="Click to access your account"):
            if email and password:
                try:
                    with st.spinner("Connecting to server..."):
                        auth_data = st.session_state.api_client.login(email, password)
                        st.session_state.jwt_token = auth_data["access_token"]
                        st.session_state.user_email = email
                        
                        st.success(f"Welcome back, {email}!")
                        navigate_to('landing')
                except Exception as e:
                    error_message = str(e)
                    if "Unable to connect to server" in error_message:
                        message_area.error("⚠️ Backend server is not running. Please start the backend server and try again.")
                    else:
                        message_area.error(f"❌ Login failed: {error_message}")
            else:
                message_area.warning("⚠️ Please enter both email and password.")

    # Additional styles for the button and input fields layout
    st.markdown(
        """
        <style>
        /* Center-align and style the input fields */
        div.stTextInput > label {
            font-size: 18px;
            color: #D3D3D3;
            font-weight: bold;
        }
        /* Style login button */
        div.stButton > button:first-child {
            width: 100%;
            padding: 10px;
            font-size: 20px;
            font-weight: bold;
            color: #FFFFFF;
            background-color: #1E90FF;
            border: 1px solid #1E90FF;
            border-radius: 8px;
        }
        /* Button hover effect */
        div.stButton > button:hover {
            background-color: #FF6347;
            border: 1px solid #FF6347;
            color: #FFFFFF;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Divider line
    st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)