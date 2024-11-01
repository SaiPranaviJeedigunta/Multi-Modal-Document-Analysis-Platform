# BD3app/pages/search_page.py

import streamlit as st
from utils.navigation import navigate_to

def render():
    # Check for API client
    if 'api_client' not in st.session_state:
        st.error("Please login first")
        navigate_to('login')
        return

    # Page Title with style
    st.markdown(
        "<h1 style='text-align: center; color: #F5F5F5; font-size: 36px; margin-bottom: 0;'>🔍 Search Documents</h1>",
        unsafe_allow_html=True
    )
    st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)

    # Search interface with styling
    st.markdown(
        "<p style='text-align: center; color: #D3D3D3; font-size: 18px;'>Search through documents and research notes</p>",
        unsafe_allow_html=True
    )

    # Search input and options
    search_query = st.text_input("Enter your search query:", placeholder="Type your search terms here...")
    search_type = st.selectbox(
        "Search in:",
        ["all", "documents", "research_notes"],
        format_func=lambda x: {
            "all": "📚 All Content",
            "documents": "📄 Documents Only",
            "research_notes": "📝 Research Notes Only"
        }[x]
    )

    # Search button
    if st.button("🔍 Search", help="Click to perform search"):
        if search_query:
            try:
                results = st.session_state.api_client.search_documents(
                    search_query,
                    search_type
                )
                
                # Display results count
                result_count = len(results.get("results", []))
                st.markdown(
                    f"<p style='color: #1E90FF; font-size: 18px;'>Found {result_count} results</p>",
                    unsafe_allow_html=True
                )
                
                # Display results
                for result in results.get("results", []):
                    with st.expander(f"📄 {result['title']}"):
                        # Relevance score with color based on value
                        score = result['relevance_score']
                        score_color = "#00FF00" if score > 0.8 else "#FFA500" if score > 0.5 else "#FF0000"
                        st.markdown(
                            f"<p><strong>Relevance Score:</strong> <span style='color: {score_color};'>{score:.2f}</span></p>",
                            unsafe_allow_html=True
                        )
                        
                        # Content with highlighted search terms
                        content = result['content']
                        # Basic highlighting of search terms
                        for term in search_query.split():
                            content = content.replace(
                                term,
                                f"<mark style='background-color: #FFD700; color: black;'>{term}</mark>"
                            )
                        st.markdown(f"<strong>Content:</strong> {content}", unsafe_allow_html=True)
                        
                        # Visual references if available
                        if result.get('visual_references'):
                            st.markdown("<strong>Visual References:</strong>", unsafe_allow_html=True)
                            for ref in result['visual_references']:
                                st.markdown(
                                    f"- {ref['type']} on page {ref['page']}" +
                                    (f" - {ref['caption']}" if ref.get('caption') else ""),
                                    unsafe_allow_html=True
                                )
            except Exception as e:
                st.error(f"Error performing search: {str(e)}")
        else:
            st.warning("Please enter a search query.")

    # Divider line
    st.markdown("<hr style='border: 1px solid #4B4B4B;'>", unsafe_allow_html=True)

    # Back button to return to the landing page
    if st.button("⬅ Back to Landing Page"):
        navigate_to('landing')

    # Add custom styling
    st.markdown(
        """
        <style>
        /* Style for input fields */
        div.stTextInput > div > div > input {
            background-color: #2F2F2F;
            color: #FFFFFF;
            border: 1px solid #4B4B4B;
            padding: 8px;
            border-radius: 5px;
        }
        
        /* Style for select box */
        div.stSelectbox > div > div > select {
            background-color: #2F2F2F;
            color: #FFFFFF;
            border: 1px solid #4B4B4B;
            padding: 8px;
            border-radius: 5px;
        }
        
        /* Style for buttons */
        div.stButton > button {
            background-color: #1E90FF;
            color: #FFFFFF;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        
        /* Button hover effect */
        div.stButton > button:hover {
            background-color: #FF6347;
        }
        
        /* Style for expander */
        div.streamlit-expanderHeader {
            background-color: #2F2F2F;
            border: 1px solid #4B4B4B;
            border-radius: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )