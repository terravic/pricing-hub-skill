#!/usr/bin/env python3
"""Lightweight local runner for the Pricing Hub Interactive Dashboard UI."""

import http.server
import os
import socketserver
import sys
import webbrowser

PORT = 8080
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_free_port(start_port: int) -> int:
    import socket
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
            port += 1
    return start_port


def main():
    os.chdir(PROJECT_ROOT)
    port = find_free_port(PORT)
    dashboard_rel = "src/ui/dashboard.html"

    if not os.path.exists(dashboard_rel):
        print(f"Error: Dashboard file not found at {dashboard_rel}")
        sys.exit(1)

    url = f"http://localhost:{port}/dashboard.html"
    print("=" * 65)
    print("       PRICING HUB: INTERACTIVE DASHBOARD RUNNER       ")
    print("=" * 65)
    print(f"[*] Dashboard URL : {url}")
    print(f"[*] Canonical Path: {PROJECT_ROOT}/src/ui/dashboard.html")
    print("[*] Theme Support : Light / Dark Mode Toggle Enabled")
    print("[*] Press Ctrl+C to stop local server.\n")

    # If --open flag is passed, attempt opening browser
    if "--open" in sys.argv:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Server stopped.")


if __name__ == "__main__":
    main()
