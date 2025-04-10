"""
Script to verify all application links in the SCADA RFP Finder webapp.
"""

import requests
import sys
from urllib.parse import urljoin

def verify_links(base_url):
    """
    Verify all links in the application.
    
    Args:
        base_url: Base URL of the application
    """
    print(f"Verifying links for {base_url}")
    
    # List of routes to check (GET routes only)
    routes = [
        "/",
        "/about",
        "/contact",
        "/auth/login",
        "/auth/register",
        "/rfps/",
        "/search",
        "/api/scraper/status",
    ]
    
    # Routes that require authentication
    auth_routes = [
        "/dashboard",
        "/rfps/favorites",
        "/rfps/export",
        "/notifications/",
        "/notifications/preferences",
        "/auth/profile",
        "/auth/logout",
    ]
    
    # Admin routes
    admin_routes = [
        "/admin/",
        "/admin/users",
        "/admin/rfps",
        "/admin/scrapers",
        "/admin/logs",
        "/admin/config",
    ]
    
    # Check public routes
    print("\nChecking public routes:")
    for route in routes:
        url = urljoin(base_url, route)
        try:
            response = requests.get(url, timeout=5)
            status = response.status_code
            print(f"  {route}: {'✅ OK' if status == 200 else f'❌ Error ({status})'}")
        except Exception as e:
            print(f"  {route}: ❌ Error - {str(e)}")
    
    print("\nAuthenticated and admin routes require login and cannot be verified automatically.")
    print("These routes should be manually tested after logging in.")
    
    # Check static assets
    print("\nChecking static assets:")
    static_assets = [
        "/static/css/style.css",
        "/static/js/main.js",
    ]
    
    for asset in static_assets:
        url = urljoin(base_url, asset)
        try:
            response = requests.get(url, timeout=5)
            status = response.status_code
            print(f"  {asset}: {'✅ OK' if status == 200 else f'❌ Error ({status})'}")
        except Exception as e:
            print(f"  {asset}: ❌ Error - {str(e)}")
    
    print("\nVerification complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://5000-iojnm7g3ty6nxhbtnk6ko-58220894.manus.computer"
    
    verify_links(base_url)
