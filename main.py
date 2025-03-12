import streamlit as st
from gmail_utils import GmailClient
from database import EmailDatabase
from text_to_sql import QueryProcessor
import os
from dotenv import load_dotenv
import time

load_dotenv()

def main():
    st.title("Email Assistant")
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'gmail_client' not in st.session_state:
        st.session_state.gmail_client = GmailClient()
    if 'db' not in st.session_state:
        st.session_state.db = EmailDatabase()
    if 'query_processor' not in st.session_state:
        st.session_state.query_processor = QueryProcessor()
    
    # Get instances from session state
    gmail_client = st.session_state.gmail_client
    db = st.session_state.db
    query_processor = st.session_state.query_processor
    
    # Check for token file on startup
    if os.path.exists('token.json') and not st.session_state.authenticated:
        try:
            # Try to initialize with existing token
            if gmail_client.authenticate():
                st.session_state.authenticated = True
        except Exception as e:
            st.error(f"Error with existing credentials: {str(e)}")
            # If token exists but is invalid, remove it
            if os.path.exists('token.json'):
                os.remove('token.json')
                
    # Authentication section
    auth_status = st.empty()
    if not st.session_state.authenticated:
        auth_status.warning("Not authenticated with Gmail. Please login.")
        if st.button("Login with Gmail"):
            auth_placeholder = st.empty()
            auth_placeholder.info("Opening authentication window. Please check your browser.")
            
            try:
                # Start authentication process
                if gmail_client.authenticate():
                    st.session_state.authenticated = True
                    auth_placeholder.success("Authentication successful!")
                    time.sleep(2)  # Give user time to see success message
                    st.experimental_rerun()  # Refresh the app
            except Exception as e:
                auth_placeholder.error(f"Authentication failed: {str(e)}")
                st.error("Make sure port 8088 is not in use by another application.")
    else:
        auth_status.success("✓ Authenticated with Gmail")
    
    # Email fetching section - only show if authenticated
    if st.session_state.authenticated:
        st.subheader("Email Management")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("Fetch Recent Emails"):
                fetch_placeholder = st.empty()
                with st.spinner("Fetching emails..."):
                    try:
                        emails = gmail_client.fetch_emails()
                        if emails:
                            db.store_emails(emails)
                            fetch_placeholder.success(f"Fetched and stored {len(emails)} emails")
                        else:
                            fetch_placeholder.info("No emails found to fetch")
                    except Exception as e:
                        fetch_placeholder.error(f"Error fetching emails: {str(e)}")
        
        # Query section
        st.subheader("Search Your Emails")
        query = st.text_input("Enter your query (e.g., 'Show all emails from last week')")
        
        if query and st.button("Execute Query"):
            with st.spinner("Processing query..."):
                try:
                    results, sql = query_processor.process_query(query)
                    if isinstance(results, str) and "Error" in results:
                        st.error(results)
                    else:
                        st.subheader("SQL Query")
                        st.code(sql, language="sql")
                        st.subheader("Results")
                        st.dataframe(results)
                except Exception as e:
                    st.error(f"Error executing query: {str(e)}")

if __name__ == "__main__":
    main()