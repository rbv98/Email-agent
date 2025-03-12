from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import base64
from safe_constants import SCOPES
import streamlit as st

class GmailClient:
    def __init__(self):
        self.creds = None
        self.service = None
    
    def authenticate(self):
        # First check if credentials already exist and are valid
        if os.path.exists('token.json'):
            try:
                self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                
                # If credentials exist but are expired, try to refresh
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                    with open('token.json', 'w') as token:
                        token.write(self.creds.to_json())
                    
                # If credentials are valid, build the service
                if self.creds and self.creds.valid:
                    self.service = build('gmail', 'v1', credentials=self.creds)
                    return True
            except Exception as e:
                st.error(f"Error with existing credentials: {str(e)}")
                # If there's an error with existing credentials, continue to get new ones
                if os.path.exists('token.json'):
                    os.remove('token.json')
        
        # If we get here, we need new credentials
        try:
            # Important: Use InstalledAppFlow for desktop applications
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            
            # Don't set redirect_uri manually, let the flow handle it
            # The port should be available and not used by Streamlit
            self.creds = flow.run_local_server(port=8088)
            
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
                
            self.service = build('gmail', 'v1', credentials=self.creds)
            return True
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            raise e

    def fetch_emails(self, max_results=80):
        if not self.service:
            raise ValueError("Gmail service not initialized. Please authenticate first.")
            
        results = self.service.users().messages().list(
            userId='me', maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        emails = []
        for message in messages:
            msg = self.service.users().messages().get(
                userId='me', id=message['id'], format='full').execute()
            email_data = self._parse_message(msg)
            if email_data:
                emails.append(email_data)
        
        return emails

    def _parse_message(self, msg):
        if not msg:
            return None
            
        headers = msg['payload']['headers']
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), '')
        sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), '')
        date = next((header['value'] for header in headers if header['name'].lower() == 'date'), '')
        recipient = next((header['value'] for header in headers if header['name'].lower() == 'to'), '')
        
        if 'parts' in msg['payload']:
            body = self._get_body_from_parts(msg['payload']['parts'])
        else:
            body = self._decode_body(msg['payload'])
            
        return {
            'id': msg['id'],
            'sender': sender,
            'recipient': recipient,
            'date': date,
            'subject': subject,
            'content': body
        }

    def _get_body_from_parts(self, parts):
        text = ''
        for part in parts:
            if part['mimeType'] == 'text/plain':
                text += self._decode_body(part)
            elif part['mimeType'] == 'multipart/alternative' and 'parts' in part:
                text += self._get_body_from_parts(part['parts'])
        return text

    def _decode_body(self, part):
        if 'body' not in part or 'data' not in part['body']:
            return ''
        
        data = part['body']['data']
        data = data.replace('-', '+').replace('_', '/')
        
        try:
            decoded_bytes = base64.b64decode(data)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            print(f"Error decoding message: {e}")
            return ''