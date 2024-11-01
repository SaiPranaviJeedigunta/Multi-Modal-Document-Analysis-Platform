# BD3app/pages/qa_page.py

import streamlit as st
from utils.navigation import navigate_to

def render():
    # Check for API client
    if 'api_client' not in st.session_state:
        st.error("Please login first")
        navigate_to('login')
        return

    # Check for selected document
    document = st.session_state.get("selected_document", None)
    if not document:
        st.error("No document selected")
        navigate_to('explore')
        return

    # Retrieve the document title from session state
    document_title = st.session_state.get("selected_document_title", "Document Title")

    # Page Title and Document Title
    st.markdown(
        "<h1 style='text-align: center; color: #F5F5F5; font-size: 36px;'>Q/A Interface</h1>",
        unsafe_allow_html=True
    )
    st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)
    st.markdown(
        f"<h2 style='color: #1E90FF; font-size: 28px;'>{document_title}</h2>",
        unsafe_allow_html=True
    )

    # Section for Question Input
    st.markdown("<h3 style='color: #F5F5F5;'>Ask a Question About the Document</h3>", unsafe_allow_html=True)
    question = st.text_input("Question:", placeholder="Type your question here...")

    # Placeholder area to display the response
    response_area = st.empty()

    # Submit button for the question
    if st.button("Ask"):
        if question:
            try:
                # Use API client to get response
                response = st.session_state.api_client.ask_question(
                    document["id"], 
                    question
                )
                response_area.markdown(
                    f"""
                    <div style='padding: 10px; background-color: #333; border-radius: 5px;'>
                        <strong>Answer:</strong> {response['answer']}<br>
                        <small>Confidence: {response['confidence_score']:.2f}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            except Exception as e:
                response_area.error(f"Error processing question: {str(e)}")
        else:
            response_area.warning("Please enter a question before submitting.")

    # Divider line
    st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)

    # Navigation back button to return to the open document page
    if st.button("⬅ Back to Document Overview"):
        navigate_to('open_document')