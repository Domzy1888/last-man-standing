import os
import requests
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
API_KEY = os.getenv("FOOTBALL_API_KEY")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def sync_fixtures():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    # 39 = English Premier League, 179 = Scottish Premiership
    leagues = [39, 179]
    season = 2026 
    
    print("🔄 Starting fixture sync from API-Football...")
    
    for league_id in leagues:
        print(f"Fetching data for League ID: {league_id}...")
        params = {"league": league_id, "season": season}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            if "response" not in data or not data["response"]:
                print(f"⚠️ No fixture data returned for league {league_id}")
                continue
                
            fixtures_to_upsert = []
            
            for item in data["response"]:
                fixture_id = item["fixture"]["id"]
                kickoff = item["fixture"]["date"]
                status = item["fixture"]["status"]["short"] # 'NS', 'FT', etc.
                home = item["teams"]["home"]["name"]
                away = item["teams"]["away"]["name"]
                
                # Parse out the gameweek number from strings like "Regular Season - 1"
                round_str = item["league"]["round"]
                gameweek = int(''.join(filter(str.isdigit, round_str)))
                
                # Determine winner if the game has already completed
                winner = None
                if status == "FT":
                    if item["teams"]["home"]["winner"]:
                        winner = home
                    elif item["teams"]["away"]["winner"]:
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
            
            # Perform bulk upsert into your fresh Supabase fixtures table
            if fixtures_to_upsert:
                supabase.table("fixtures").upsert(fixtures_to_upsert).execute()
                print(f"✅ Successfully synced {len(fixtures_to_upsert)} fixtures for league {league_id}")
                
        except Exception as e:
            print(f"❌ Error syncing league {league_id}: {str(e)}")

if __name__ == "__main__":
    sync_fixtures()
