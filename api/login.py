import os
import urllib.parse
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        client_id = os.environ.get('SPOTIFY_CLIENT_ID')
        
        if not client_id:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Missing SPOTIFY_CLIENT_ID in Vercel Environment Variables.")
            return
        
        # Dynamically build redirect URL based on Vercel deployment host
        host = self.headers.get('Host')
        protocol = "https" if "localhost" not in host else "http"
        redirect_uri = f"{protocol}://{host}/api/callback"
        
        # We need playlist permissions to display their saved playlists
        scope = "playlist-read-private playlist-read-collaborative"
        url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}&scope={urllib.parse.quote(scope)}&redirect_uri={urllib.parse.quote(redirect_uri)}"
        
        self.send_response(302)
        self.send_header('Location', url)
        self.end_headers()
