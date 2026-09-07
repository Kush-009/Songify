import os
import urllib.parse
import urllib.request
import json
import base64
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code = query.get('code', [''])[0]
        
        if not code:
            self.send_response(302)
            self.send_header('Location', "/?error=no_code_provided")
            self.end_headers()
            return

        client_id = os.environ.get('SPOTIFY_CLIENT_ID')
        client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
        
        host = self.headers.get('Host')
        protocol = "https" if "localhost" not in host else "http"
        redirect_uri = f"{protocol}://{host}/api/callback"

        # Exchange Auth code for an official Access Token
        auth_string = f"{client_id}:{client_secret}"
        auth_base64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

        req = urllib.request.Request(
            'https://accounts.spotify.com/api/token',
            data=urllib.parse.urlencode({
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri
            }).encode(),
            headers={
                'Authorization': f'Basic {auth_base64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            method='POST'
        )

        try:
            resp = urllib.request.urlopen(req).read()
            token = json.loads(resp).get('access_token')
            
            # Send them back to index.html with the token in the URL 
            # (which the frontend Javascript will immediately hide and save)
            self.send_response(302)
            self.send_header('Location', f"/?token={token}")
            self.end_headers()
        except Exception as e:
            self.send_response(302)
            self.send_header('Location', "/?error=auth_failed_verify_client_keys")
            self.end_headers()
