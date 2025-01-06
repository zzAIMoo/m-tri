import secrets
import requests
from typing import Optional, Tuple
from kivy.uix.modalview import ModalView
from kivy.core.window import Window
from kivy.app import App
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import json
import os
from pathlib import Path

class MALAuth:
    AUTH_URL = "https://myanimelist.net/v1/oauth2/authorize"
    TOKEN_URL = "https://myanimelist.net/v1/oauth2/token"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.code_verifier = self._generate_code_verifier()
        self.auth_code: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

        self.data_dir = Path.home() / '.mihontracker'
        self.data_dir.mkdir(exist_ok=True)
        self.credentials_file = self.data_dir / 'mal_credentials.json'

        self.load_credentials()

    def _generate_code_verifier(self, length: int = 128) -> str:
        """Generate a random code verifier for PKCE"""
        token = secrets.token_urlsafe(length)
        return token[:128]

    def get_auth_url(self) -> str:
        """Generate the authorization URL"""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "code_challenge": self.code_verifier,
            "redirect_uri": "http://localhost:8080/callback",
            "code_challenge_method": "plain",
            "state": secrets.token_urlsafe(16)
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"

    def save_credentials(self) -> None:
        """Save tokens to a file"""
        credentials = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token
        }

        with open(self.credentials_file, 'w') as f:
            json.dump(credentials, f)

    def load_credentials(self) -> bool:
        """Load tokens from file if they exist"""
        try:
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    credentials = json.load(f)
                    self.access_token = credentials.get('access_token')
                    self.refresh_token = credentials.get('refresh_token')
                    return True
            return False
        except Exception:
            return False

    def clear_credentials(self) -> None:
        """Clear stored credentials"""
        if self.credentials_file.exists():
            self.credentials_file.unlink()
        self.access_token = None
        self.refresh_token = None

    def get_tokens(self, auth_code: str) -> Tuple[str, str]:
        """Exchange authorization code for tokens"""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "http://localhost:8080/callback",
            "code_verifier": self.code_verifier
        }

        response = requests.post(self.TOKEN_URL, data=data)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens["refresh_token"]
            self.save_credentials()
            return self.access_token, self.refresh_token
        else:
            raise Exception(f"Token exchange failed: {response.text}")

    def refresh_access_token(self) -> str:
        """Get a new access token using the refresh token"""
        if not self.refresh_token:
            raise Exception("No refresh token available")

        data = {
            "client_id": self.client_id,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }

        response = requests.post(self.TOKEN_URL, data=data)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens["refresh_token"]
            self.save_credentials()
            return self.access_token
        else:
            self.clear_credentials()
            raise Exception(f"Token refresh failed: {response.text}")

class CallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)

        if 'code' in query_components:
            CallbackHandler.auth_code = query_components['code'][0]

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Authorization successful! You can close this window.")
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Authorization failed! No code received.")

        threading.Thread(target=self.server.shutdown).start()

class MALAuthWebView(ModalView):
    """Modal view for MAL authentication"""
    def __init__(self, auth_url: str, on_auth_complete=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.8, 0.8)
        self.auth_code = None
        self.on_auth_complete = on_auth_complete

        server_thread = threading.Thread(target=self._start_callback_server)
        server_thread.daemon = True
        server_thread.start()

        webbrowser.open(auth_url)

    def _start_callback_server(self):
        server = HTTPServer(('localhost', 8080), CallbackHandler)
        server.serve_forever()

        self.auth_code = CallbackHandler.auth_code

        if self.on_auth_complete and self.auth_code:
            self.on_auth_complete(self.auth_code)

        self.dismiss() 