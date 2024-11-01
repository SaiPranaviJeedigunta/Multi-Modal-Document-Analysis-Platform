# BD3app/pages/landing_page.py

import streamlit as st
from utils.navigation import navigate_to

def render():
    # Title and Subheader with Styling
    st.markdown(
        "<h1 style='text-align: center; color: #F5F5F5; font-size: 42px;'>🌐 Welcome to the Document Explorer</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<h3 style='text-align: center; color: #D3D3D3; font-size: 20px;'>What would you like to do today?</h3>",
        unsafe_allow_html=True
    )
    st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)

    # Set up three columns for options with equal widths
    col1, col2, col3 = st.columns(3)

    # Adding buttons with icons and styling
    with col1:
        if st.button("📁 Explore Documents"):
            navigate_to('explore')  # Go to Explore Documents page
    with col2:
        if st.button("🔍 Search"):
            navigate_to('search')  # Go to Search page
    with col3:
        if st.button("💬 Q/A Interface"):
            navigate_to('qa')  # Go to Q/A Interface page

    # Additional styles for the button layout and overall page
    st.markdown(
        """
        <style>
        /* Center-align and style the column layout */
        div.stButton > button:first-child {
            width: 100%;
            padding: 10px;
            color: #FFFFFF;
            background-color: #1E90FF;
            border: 1px solid #1E90FF;
            border-radius: 8px;
            font-size: 20px;
            font-weight: bold;
        }

        /* Add hover effect for buttons */
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
