import streamlit as st
import requests
from supabase import create_client

# Fetch credentials seamlessly from Streamlit Cloud Advanced Settings
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
API_KEY = st.secrets["FOOTBALL_API_KEY"]

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def sync_fixtures():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    # 39 = EPL, 179 = Scottish Premiership
    leagues = [39, 179]
    season = 2025  # Changed from 2026 to 2025 to grab verified historical data
    
    for league_id in leagues:
        params = {"league": league_id, "season": season}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            # Diagnostic check in case the API encounters account-level trouble
            if "errors" in data and data["errors"]:
                st.error(f"API Error for League {league_id}: {data['errors']}")
                continue
                
            if "response" not in data or not data["response"]:
                st.warning(f"No match data returned from API for League {league_id} Season {season}.")
                continue
                
            fixtures_to_upsert = []
            for item in data["response"]:
                fixture_id = item["fixture"]["id"]
                kickoff = item["fixture"]["date"]
                status = item["fixture"]["status"]["short"]
                home = item["teams"]["home"]["name"]
                away = item["teams"]["away"]["name"]
                
                # Check formatting carefully to guarantee integers parse flawlessly
                round_str = item["league"].get("round", "")
                digits = ''.join(filter(str.isdigit, round_str))
                if not digits:
                    continue  # Skips non-gameweek entries smoothly
                gameweek = int(digits)
                
                winner = None
                if status == "FT":
                    if item["teams"]["home"].get("winner") is True: 
                        winner = home
                    elif item["teams"]["away"].get("winner") is True: 
                        winner = away
                    else: 
                        winner = "DRAW"
                
                fixtures_to_upsert.append({
                    "id": fixture_id,
                    "league_id": league_id,
                    "gameweek": gameweek,
                    "kickoff_time": kickoff,
                    "home_team": home,
                    "away_team": away,
                    "status": status,
                    "winner": winner
                })
            
            if fixtures_to_upsert:
                supabase.table("fixtures").upsert(fixtures_to_upsert).execute()
                st.toast(f"Successfully loaded {len(fixtures_to_upsert)} fixtures for league {league_id}!")
                
        except Exception as e:
            st.error(f"System error processing league {league_id}: {str(e)}")

if __name__ == "__main__":
    sync_fixtures()
