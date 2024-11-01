import streamlit as st
from pages import login_page, landing_page, explore_page, search_page, qa_page, open_document_page, report_page  # Updated to include open_document_page
from utils.navigation import navigate_to
from utils.config import load_config
from dotenv import load_dotenv  # Import dotenv to load environment variables
import os

# Step 1: Load environment variables from .env file
load_dotenv()  # This loads the .env file

# Step 2: Load additional configuration (if required)
config = load_config()

# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state.page = 'login'  # Default page set to login

if 'selected_document' not in st.session_state:
    st.session_state.selected_document = None  # Initialize selected document state

# Main Navigation Logic
def main():
    # Render the page based on the current state
    if st.session_state.page == 'login':
        login_page.render()
    elif st.session_state.page == 'landing':
        landing_page.render()
    elif st.session_state.page == 'explore':
        explore_page.render()
    elif st.session_state.page == 'search':
        search_page.render()
    elif st.session_state.page == 'qa':
        qa_page.render()
    elif st.session_state.page == 'open_document':  # Updated to navigate to open_document_page
        open_document_page.render()  # Renders the new open_document_page
    elif st.session_state.page == 'report':
        report_page.render()
    else:
        # Default to landing page if page state is unrecognized
        st.session_state.page = 'landing'
        landing_page.render()

# Run the main application function
if __name__ == "__main__":
    main()
