import streamlit as st
from utils.navigation import navigate_to

def render():
    # Check for API client
    if 'api_client' not in st.session_state:
        st.error("Please login first")
        navigate_to('login')
        return

    # Retrieve the selected document's details from session state
    document = st.session_state.get("selected_document", None)

    # Page Title
    st.markdown(
        "<h1 style='text-align: center; color: #F5F5F5; font-size: 36px; margin-bottom: 0;'>📄 Document Overview</h1>",
        unsafe_allow_html=True
    )
    st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)

    # Check if a document has been selected
    if document:
        # Set up a two-column layout with a wider column for the image
        col1, col2 = st.columns([2.5, 1.5])

        with col1:
            # Display publication title with emphasis and color
            st.markdown(
                f"<h2 style='color: #1E90FF; font-size: 28px; margin-top: 0;'>{document.get('title', 'Unknown Document')}</h2>",
                unsafe_allow_html=True
            )

            # Document details section
            st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)

            # Display the authenticated PDF link as a styled button
            pdf_authenticated_url = document.get("pdf_authenticated_url")
            if pdf_authenticated_url:
                st.markdown(
                    f"<a style='display: inline-block; padding: 10px 20px; color: #FFF; background-color: #FF6347; font-size: 18px; font-weight: bold; border-radius: 8px; text-decoration: none;' href='{pdf_authenticated_url}' target='_blank'>Open PDF</a>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<p style='font-size: 16px; color: #FF6347;'>Authenticated URL not available for this document.</p>",
                    unsafe_allow_html=True
                )

            # Summarize Document Button with API integration
            if st.button("Summarize Document", key="summarize_button", help="Click to generate a summary"):
                try:
                    summary = st.session_state.api_client.get_document_summary(document["id"])
                    st.session_state.document_summary = summary["summary"]
                    st.session_state.show_summary_box = True
                except Exception as e:
                    st.error(f"Error generating summary: {str(e)}")

            # Display summary if available
            if st.session_state.get("show_summary_box", False):
                summary_text = st.session_state.get("document_summary", "Summary will appear here once generated...")
                st.markdown(
                    f"""<div style='margin-top: 10px; padding: 10px; border: 2px solid #FF6347; border-radius: 5px; background-color: #333;'>
                    <textarea style='width: 100%; height: 200px; color: #FFFFFF; background-color: #4B4B4B; resize: none; overflow-y: scroll;' readonly>
                    {summary_text}
                    </textarea>
                    </div>""",
                    unsafe_allow_html=True
                )

            # Q/A Interface Button (navigates to qa_page)
            if st.button("Q/A Interface", key="qa_button", help="Go to Q/A Interface"):
                st.session_state.selected_document_title = document.get("title", "Unknown Document")  # Store the title
                navigate_to('qa')  # Navigate to Q/A Interface page

        with col2:
            # Display the image if an authenticated URL for the image exists
            image_authenticated_url = document.get("image_authenticated_url")
            if image_authenticated_url:
                st.image(image_authenticated_url, caption="Document Image", width=180)
            else:
                st.markdown(
                    "<p style='color: #A9A9A9;'>No image available for this document.</p>",
                    unsafe_allow_html=True
                )

        # Divider line
        st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)

        # Navigation back button to go to Explore Documents page
        if st.button("⬅ Back to Explore Documents"):
            navigate_to('explore')  # Ensure this correctly routes to the explore page
    else:
        # Message if no document is selected
        st.markdown(
            "<p style='font-size: 18px; color: #FF6347;'>No document selected. Please go back to the Explore Documents page.</p>",
            unsafe_allow_html=True
        )
        if st.button("Back to Explore Documents"):
            navigate_to('explore')