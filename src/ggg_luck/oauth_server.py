"""HTTPS callback server for Yahoo OAuth2 flow."""

import ssl
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import webbrowser
from typing import Optional


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handler for OAuth callback requests."""
    
    authorization_code = None
    error = None
    
    def do_GET(self):
        """Handle GET request with OAuth callback."""
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            OAuthCallbackHandler.authorization_code = query_params['code'][0]
            self.send_success_response("Authorization successful! You can close this window.")
        elif 'error' in query_params:
            error_description = query_params.get('error_description', ['Unknown error'])[0]
            OAuthCallbackHandler.error = f"{query_params['error'][0]}: {error_description}"
            self.send_error_response(f"Authorization failed: {error_description}")
        else:
            self.send_error_response("Invalid callback - missing code or error parameter")
    
    def send_success_response(self, message: str):
        """Send successful response."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Yahoo OAuth Success</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 50px; text-align: center; }}
                .success {{ color: green; font-size: 24px; margin-bottom: 20px; }}
                .info {{ color: #666; font-size: 16px; }}
            </style>
        </head>
        <body>
            <div class="success">✅ {message}</div>
            <div class="info">Return to your terminal to continue.</div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def send_error_response(self, message: str):
        """Send error response."""
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Yahoo OAuth Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 50px; text-align: center; }}
                .error {{ color: red; font-size: 24px; margin-bottom: 20px; }}
                .info {{ color: #666; font-size: 16px; }}
            </style>
        </head>
        <body>
            <div class="error">❌ {message}</div>
            <div class="info">Please try again or check your configuration.</div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class HTTPSCallbackServer:
    """Simple HTTPS server for handling OAuth callbacks."""
    
    def __init__(self, host='localhost', port=8443):
        """Initialize the callback server."""
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
    
    def create_self_signed_cert(self):
        """Create a self-signed certificate for HTTPS."""
        import tempfile
        import os
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Save to temporary files
        cert_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')
        key_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.key')
        
        cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
        cert_file.close()
        
        key_file.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        key_file.close()
        
        return cert_file.name, key_file.name
    
    def start(self, timeout: int = 300) -> Optional[str]:
        """Start the HTTPS server and wait for callback."""
        try:
            # Try to use existing cert, or create a new one
            try:
                cert_file, key_file = self.create_self_signed_cert()
            except ImportError:
                print("⚠️  Cryptography library not available. Using simple HTTP fallback.")
                return self._start_http_fallback(timeout)
            
            # Reset class variables
            OAuthCallbackHandler.authorization_code = None
            OAuthCallbackHandler.error = None
            
            # Create server
            self.server = HTTPServer((self.host, self.port), OAuthCallbackHandler)
            
            # Create SSL context
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(cert_file, key_file)
            self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
            
            print(f"🔐 Starting HTTPS callback server on https://{self.host}:{self.port}")
            print("⚠️  Your browser may show a security warning - click 'Advanced' and 'Proceed to localhost'")
            
            # Start server in thread
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            
            # Wait for callback
            import time
            start_time = time.time()
            while time.time() - start_time < timeout:
                if OAuthCallbackHandler.authorization_code:
                    self.stop()
                    # Clean up cert files
                    import os
                    os.unlink(cert_file)
                    os.unlink(key_file)
                    return OAuthCallbackHandler.authorization_code
                elif OAuthCallbackHandler.error:
                    self.stop()
                    # Clean up cert files
                    import os
                    os.unlink(cert_file)
                    os.unlink(key_file)
                    raise Exception(f"OAuth error: {OAuthCallbackHandler.error}")
                time.sleep(1)
            
            self.stop()
            # Clean up cert files
            import os
            os.unlink(cert_file)
            os.unlink(key_file)
            raise TimeoutError(f"No callback received within {timeout} seconds")
            
        except Exception as e:
            print(f"❌ HTTPS server failed: {e}")
            print("🔄 Falling back to HTTP...")
            return self._start_http_fallback(timeout)
    
    def _start_http_fallback(self, timeout: int) -> Optional[str]:
        """Fallback to HTTP server."""
        # Reset class variables
        OAuthCallbackHandler.authorization_code = None
        OAuthCallbackHandler.error = None
        
        # Use HTTP port
        http_port = 8080
        self.server = HTTPServer((self.host, http_port), OAuthCallbackHandler)
        
        print(f"🌐 Starting HTTP callback server on http://{self.host}:{http_port}")
        print("⚠️  Note: Your Yahoo app should be configured for HTTPS, but trying HTTP fallback")
        
        # Start server in thread
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        
        # Wait for callback
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            if OAuthCallbackHandler.authorization_code:
                self.stop()
                return OAuthCallbackHandler.authorization_code
            elif OAuthCallbackHandler.error:
                self.stop()
                raise Exception(f"OAuth error: {OAuthCallbackHandler.error}")
            time.sleep(1)
        
        self.stop()
        raise TimeoutError(f"No callback received within {timeout} seconds")
    
    def stop(self):
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)


def get_authorization_code_interactive(auth_url: str, redirect_uri: str) -> str:
    """
    Get authorization code using interactive flow with HTTPS callback server.
    
    Args:
        auth_url: The Yahoo OAuth authorization URL
        redirect_uri: The redirect URI (should be https://localhost:8443/callback)
    
    Returns:
        The authorization code from Yahoo
    """
    # Parse redirect URI to get port
    parsed = urllib.parse.urlparse(redirect_uri)
    port = parsed.port or (8443 if parsed.scheme == 'https' else 8080)
    
    # Start callback server
    server = HTTPSCallbackServer(port=port)
    
    print(f"🔐 Starting OAuth flow...")
    print(f"📱 Opening browser to: {auth_url}")
    
    # Open browser
    webbrowser.open(auth_url)
    
    try:
        # Wait for callback
        auth_code = server.start(timeout=300)  # 5 minutes timeout
        print("✅ Authorization successful!")
        return auth_code
    except Exception as e:
        print(f"❌ Authorization failed: {e}")
        raise