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
    season = 2025  # Fallback to 2025 to test immediately with active data
    
    print("🔄 Starting live fixture sync from API-Football...")
    
    for league_id in leagues:
        params = {"league": league_id, "season": season}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            if "response" not in data or not data["response"]:
                continue
                
            fixtures_to_upsert = []
            for item in data["response"]:
                fixture_id = item["fixture"]["id"]
                kickoff = item["fixture"]["date"]
                status = item["fixture"]["status"]["short"]
                home = item["teams"]["home"]["name"]
                away = item["teams"]["away"]["name"]
                
                # Turn "Regular Season - 1" into a clean integer (1)
                round_str = item["league"]["round"]
                gameweek = int(''.join(filter(str.isdigit, round_str)))
                
                winner = None
                if status == "FT":
                    if item["teams"]["home"]["winner"]: winner = home
                    elif item["teams"]["away"]["winner"]: winner = away
                    else: winner = "DRAW"
                
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
                
        except Exception as e:
            print(f"❌ Error syncing league {league_id}: {str(e)}")

if __name__ == "__main__":
    sync_fixtures()
