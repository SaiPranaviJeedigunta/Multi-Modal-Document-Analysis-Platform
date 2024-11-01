import streamlit as st
from utils.api_requests import fetch_documents
from utils.navigation import navigate_to

def render():
    # Check for API client in session state
    if 'api_client' not in st.session_state:
        st.error("Please login first")
        navigate_to('login')
        return

    # Page Title with style
    st.markdown(
        "<h1 style='text-align: center; color: #F5F5F5; font-size: 36px; margin-bottom: 0;'>📚 Explore Documents</h1>",
        unsafe_allow_html=True
    )
    st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)

    # Description text
    st.markdown("<p style='text-align: center; color: #D3D3D3; font-size: 18px;'>Select a document from the dropdown below:</p>", unsafe_allow_html=True)

    try:
        # Fetch document data using API client
        document_data = st.session_state.api_client.fetch_documents()
        documents = document_data.get("documents", [])

        # Extract titles from the documents for the dropdown
        titles = [doc["title"] for doc in documents]

        # Dropdown to select a title, styled
        selected_title = st.selectbox(
            "Select a publication:",
            titles,
            format_func=lambda x: f"📄 {x}",  # Adds an icon to each option
        )

        # Find the document details corresponding to the selected title
        selected_document = next((doc for doc in documents if doc["title"] == selected_title), None)

        # Display document details and links if a title is selected
        if selected_document:
            st.markdown("<hr style='border: 1px solid #4B4B4B; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

            # Display GCS Path with the label highlighted
            st.markdown(
                f"<p style='font-size: 18px;'><strong style='color: #FFD700;'>GCS Path:</strong> <span style='color: #A9A9A9;'>{selected_document['pdf_gcs_path']}</span></p>",
                unsafe_allow_html=True
            )

            # "Open Document" button to navigate to open_document_page, with styling
            if st.button("Open Document", key="open_doc"):
                # Save the selected document details in session state
                st.session_state.selected_document = selected_document
                # Navigate to open_document_page
                st.session_state.page = 'open_document'

    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")

    # Divider line for separation
    st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)

    # Back button to return to the landing page, styled
    if st.button("Back to Landing Page", key="back_to_landing"):
        navigate_to('landing')

    # Styling the buttons at the bottom using HTML and CSS-like styles
    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            background-color: #1E90FF; 
            color: #FFF; 
            border-radius: 8px; 
            padding: 10px 20px; 
            font-size: 18px; 
            font-weight: bold; 
            margin-top: 10px;
        }
        div.stButton > button:nth-child(2) {
            background-color: #FF6347; 
            color: #FFF; 
            border-radius: 8px; 
            padding: 10px 20px; 
            font-size: 18px; 
            font-weight: bold; 
            margin-top: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )