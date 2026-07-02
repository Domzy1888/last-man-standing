import streamlit as st
import datetime
import requests
from supabase import create_client

# Initialize Supabase Client Connection
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
API_KEY = st.secrets["FOOTBALL_API_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="SQUAD LOCK // LMS", page_icon="⚽", layout="wide")

st.markdown("""
<style>
.custom-metric { background: #1e293b; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #334155; }
.metric-val { font-size: 1.8rem; font-weight: 800; color: #38bdf8; }
.league-header { background: #1e293b; padding: 10px; border-radius: 6px; margin: 15px 0 10px 0; font-weight: bold; }
.match-card { border: 1px solid #334155; padding: 12px; border-radius: 8px; margin-bottom: 10px; background-color: #0f172a; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ SQUAD LOCK")
st.caption("EPL & William Hill Premiership Last Man Standing")

players_list = ["Callum", "Jamie", "Ross", "Stuart", "Chris"]
current_user = st.sidebar.selectbox("👤 Select Your Player Profile", players_list)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="custom-metric"><small>Your Status</small><div class="metric-val">ALIVE</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="custom-metric"><small>Current Round</small><div class="metric-val">Gameweek 1</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="custom-metric"><small>Total Survivors</small><div class="metric-val">{len(players_list)}</div></div>', unsafe_allow_html=True)

st.divider()

tab_picks, tab_lobby, tab_admin = st.tabs(["🎯 Make Your Pick", "📊 Live Lobby", "⚙️ Admin Toolkit"])

with tab_picks:
    st.subheader("Available Matches")
    target_gw = 1 
    
    try:
        res = supabase.table("fixtures").select("*").eq("gameweek", target_gw).order("kickoff_time").execute()
        fixtures = res.data
        
        if not fixtures:
            st.info("No fixtures found in database for Gameweek 1. Go to Admin Toolkit and run the sync engine.")
        else:
            burned_teams = [] 
            epl_fixtures = [f for f in fixtures if f["league_id"] == 39]
            spfl_fixtures = [f for f in fixtures if f["league_id"] == 179]
            
            def render_league_fixtures(league_title, league_list):
                if league_list:
                    st.markdown(f"<div class='league-header'>{league_title}</div>", unsafe_allow_html=True)
                    for f in league_list:
                        try:
                            kickoff = datetime.datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))
                            kickoff_display = kickoff.strftime("%a %H:%M")
                        except:
                            kickoff_display = str(f["kickoff_time"])
                        
                        st.markdown(f"""
                        <div class='match-card'>
                            <strong>{f['home_team']}</strong> vs <strong>{f['away_team']}</strong><br/>
                            <small style='color: #94a3b8;'>📅 Kickoff: {kickoff_display}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        options = ["-- Choose Team --", f['home_team'], f['away_team']]
                        clean_options = [opt for opt in options if opt not in burned_teams]
                        
                        st.selectbox(
                            f"Lock selection for {f['home_team']} v {f['away_team']}", 
                            clean_options, 
                            key=f"sel_{f['id']}"
                        )
                else:
                    st.write(f"ℹ️ No fixtures found for {league_title}.")
            
            render_league_fixtures("🏴󠁧󠁢󠁥󠁮󠁧󠁿 English Premier League", epl_fixtures)
            render_league_fixtures("🏴󠁧󠁢󠁳󠁣󠁴󠁿 William Hill Scottish Premiership", spfl_fixtures)
            
    except Exception as e:
        st.error(f"Error drawing layout: {e}")

with tab_lobby:
    st.subheader("The Weekend Sweat Feed")

with tab_admin:
    st.subheader("System Administration Panel")
    
    if st.button("Run Live Fixture Refresher"):
        st.warning("⚠️ Running Live Check Directly inside Main Loop...")
        
        url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-rapidapi-key": API_KEY,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
        
        # Test directly with 2025 to prove the layout works
        leagues = [39, 179]
        season = 2025  
        
        for league_id in leagues:
            st.write(f"📡 Requesting League `{league_id}`, Season `{season}`...")
            try:
                response = requests.get(url, headers=headers, params={"league": league_id, "season": season})
                data = response.json()
                
                # Check 1: Did the API throw an error message?
                if "errors" in data and data["errors"]:
                    st.error(f"❌ API explicitly rejected request for League {league_id}: {data['errors']}")
                    continue
                
                # Check 2: Did it return anything inside response?
                items = data.get("response", [])
                st.write(f"📥 Received `{len(items)}` match rows from API.")
                
                fixtures_to_upsert = []
                for item in items:
                    fixture_id = item["fixture"]["id"]
                    kickoff = item["fixture"]["date"]
                    status = item["fixture"]["status"]["short"]
                    home = item["teams"]["home"]["name"]
                    away = item["teams"]["away"]["name"]
                    
                    round_str = item["league"].get("round", "")
                    digits = ''.join(filter(str.isdigit, round_str))
                    if not digits:
                        continue
                    gameweek = int(digits)
                    
                    winner = None
                    if status == "FT":
                        if item["teams"]["home"].get("winner") is True: winner = home
                        elif item["teams"]["away"].get("winner") is True: winner = away
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
                    st.write(f"⏳ Attempting write of `{len(fixtures_to_upsert)}` entries to Supabase...")
                    supabase.table("fixtures").upsert(fixtures_to_upsert).execute()
                    st.success(f"✅ Successfully written rows for League {league_id}!")
                else:
                    st.error("❌ Processed 0 rows. No matching valid gameweeks parsed.")
                    
            except Exception as e:
                st.error(f"💥 Critical Crash: {str(e)}")
