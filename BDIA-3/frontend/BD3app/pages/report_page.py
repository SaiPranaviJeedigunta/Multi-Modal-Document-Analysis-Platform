# BD3app/pages/report_page.py

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

    # Page Title
    st.title("Report Generation")

    # Instructions
    st.write("Select the content you want to include in your report:")

    # Report Content Selection Options
    include_summary = st.checkbox("Include Document Summary")
    include_qa_responses = st.checkbox("Include Q/A Responses")
    include_full_text = st.checkbox("Include Full Document Text")

    # Display Selected Content for Preview
    st.write("### Report Preview")
    
    # Preview sections based on selections
    if include_summary:
        st.subheader("Document Summary")
        try:
            summary = st.session_state.api_client.get_document_summary(document["id"])
            st.write(summary.get("summary", "Summary not available"))
        except Exception as e:
            st.write("(Unable to load summary)")

    if include_qa_responses:
        st.subheader("Q/A Responses")
        if "qa_responses" in st.session_state:
            st.write(st.session_state.qa_responses)
        else:
            st.write("(No Q/A responses available)")

    if include_full_text:
        st.subheader("Full Document Text")
        try:
            full_text = st.session_state.api_client.get_document_text(document["id"])
            st.write(full_text.get("content", "Full text not available"))
        except Exception as e:
            st.write("(Unable to load full text)")

    # Button to generate the report
    if st.button("Generate Report"):
        try:
            report_options = {
                "include_summary": include_summary,
                "include_qa_responses": include_qa_responses,
                "include_full_text": include_full_text
            }
            
            report = st.session_state.api_client.generate_report(
                document["id"],
                report_options
            )
            
            st.session_state.generated_report = report
            st.success("Report generated successfully!")
            
            # Display report preview
            st.write("### Generated Report")
            st.write(report["content"])
            
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")

    # Button to download the report
    if st.button("Download Report as PDF"):
        if "generated_report" in st.session_state:
            try:
                pdf_data = st.session_state.api_client.get_report_pdf(
                    document["id"],
                    st.session_state.generated_report["id"]
                )
                st.download_button(
                    label="Click to Download",
                    data=pdf_data["content"],
                    file_name=f"report_{document['id']}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error downloading report: {str(e)}")
        else:
            st.info("Please generate a report first before downloading")

    # Back button to navigate to the Document Overview or Landing Page
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back to Document Overview"):
            navigate_to('document_overview')
    with col2:
        if st.button("Back to Landing Page"):
            navigate_to('landing')