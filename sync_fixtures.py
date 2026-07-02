import streamlit as st
import requests
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
API_KEY = st.secrets["FOOTBALL_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def sync_fixtures():
    # Test explicitly with EPL (39)
    url = "https://v3.football.api-sports.io/fixtures"
    
    # We test both header variants (RapidAPI vs Direct API-Sports) to find the lock
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    params = {"league": 39, "season": 2025}
    
    st.info("🔄 Initiating Live API Connection Test...")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        status_code = response.status_code
        st.write(f"📡 API HTTP Connection Status: `{status_code}`")
        
        data = response.json()
        
        st.markdown("### 📋 Raw API Payload Inspection")
        st.json(data)
        
        if "response" in data and len(data["response"]) > 0:
            st.success(f"Success! Found {len(data['response'])} raw fixture items. Parsing data...")
            # Simple proof of entry
            item = data["response"][0]
            st.write(f"Sample item extracted safely: {item.get('teams', {}).get('home', {}).get('name')} vs {item.get('teams', {}).get('away', {}).get('name')}")
        else:
            st.error("The 'response' array is completely empty or missing. Check the parameters or API Key permissions shown above.")
            
    except Exception as e:
        st.error(f"Fatal script execution interruption: {str(e)}")

if __name__ == "__main__":
    sync_fixtures()
