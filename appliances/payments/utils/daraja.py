import requests
import base64
from django.conf import settings

def get_access_token():
    """Get M-Pesa access token"""
    try:
        consumer_key = settings.CONSUMER_KEY
        consumer_secret = settings.CONSUMER_SECRET
        
        if not consumer_key or not consumer_secret:
            print("M-Pesa credentials not configured")
            return None
        
        credentials = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            headers=headers,
            timeout=30
        )
        
        print(f"M-Pesa Auth Response Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                print("M-Pesa access token retrieved successfully")
                return access_token
            else:
                print(f"No access token in response: {token_data}")
        else:
            print(f"M-Pesa auth failed: {response.status_code} - {response.text}")
        
        return None
    except Exception as e:
        print(f"Access token error: {e}")
        return None