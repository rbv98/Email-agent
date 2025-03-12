SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/userinfo.email", "openid"]

PROJECT_ID = "email_app"

AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_PROVIDER_X509_CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"

MAX_CHARACTER_LENGTH_EMAIL = 12000

# Use a different port for OAuth callback
MAIN_REDIRECT_URI = 'http://localhost:8088'

# Make sure these match what's in your Google Cloud Console
ALL_REDIRECT_URIS = ["http://localhost:8088"]
ALL_JAVASCRIPT_ORIGINS = ["http://localhost:8088"]