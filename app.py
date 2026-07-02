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
.match-card { border: 1px solid #334155; padding: 12px; border-radius: 8px; margin-bottom: 10px; background-color: #0f172a; line-height: 1.6; }
.locked-box { background: #065f46; color: #a7f3d0; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 1px solid #047857; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ SQUAD LOCK")
st.caption("EPL & William Hill Premiership Last Man Standing")

# --- Player Profile Setup ---
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
        # 1. Check if this specific player has already saved a pick for this gameweek
        pick_check = supabase.table("user_picks").select("*").eq("user_id", current_user).eq("gameweek", target_gw).execute()
        existing_pick = pick_check.data
        
        # 2. Query all past selections to "burn" previously chosen squads
        past_picks_res = supabase.table("user_picks").select("team_picked").eq("user_id", current_user).execute()
        burned_teams = [p["team_picked"] for p in past_picks_res.data] if past_picks_res.data else []
        
        # 3. Fetch all fixtures from database
        res = supabase.table("fixtures").select("*").order("kickoff_time").execute()
        all_fixtures = res.data
        
        if not all_fixtures:
            st.info("No fixtures found in database. Go to Admin Toolkit and run the sync engine.")
        else:
            # Filter matches for the targeted gameweek round safely (Fixed NameError)
            fixtures = [
                f for f in all_fixtures 
                if f.get("gameweek") is not None and int(float(f["gameweek"])) == target_gw
            ]
            
            epl_fixtures = [f for f in fixtures if f["league_id"] == 39]
            spfl_fixtures = [f for f in fixtures if f["league_id"] == 179]
            
            # Generate a master list of all teams playing this weekend
            available_teams = sorted(list(set(
                [f["home_team"] for f in fixtures] + [f["away_team"] for f in fixtures]
            )))
            
            # --- PICK SELECTION AREA ---
            st.markdown("### 🔒 Lock In Your Team")
            
            if existing_pick:
                locked_team = existing_pick[0]["team_picked"]
                st.markdown(f"""
                <div class="locked-box">
                    🔒 You have officially locked in {locked_team} for Gameweek {target_gw}!
                </div>
                """, unsafe_allow_html=True)
            else:
                # Traditional LMS Selection: Filter out any previously burned squads
                selectable_options = ["-- Select Team --"] + [team for team in available_teams if team not in burned_teams]
                
                selected_pick = st.selectbox(
                    f"Choose your single survival squad for Gameweek {target_gw}:",
                    selectable_options
                )
                
                if selected_pick != "-- Select Team --":
                    if st.button(f"Confirm & Lock {selected_pick}"):
                        try:
                            supabase.table("user_picks").insert({
                                "user_id": current_user,
                                "gameweek": target_gw,
                                "team_picked": selected_pick
                            }).execute()
                            st.success(f"Success! {selected_pick} is saved.")
                            st.rerun()
                        except Exception as save_err:
                            st.error(f"Failed to submit entry: {save_err}")
            
            st.divider()
            
            # --- FIXTURE DISPLAY CARDS ---
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
                else:
                    st.write(f"ℹ️ No active fixtures found for {league_title} this round.")
            
            render_league_fixtures("🏴󠁧󠁢󠁥󠁮󠁧󠁿 English Premier League", epl_fixtures)
            render_league_fixtures("🏴󠁧󠁢󠁳󠁣󠁴󠁿 William Hill Scottish Premiership", spfl_fixtures)
            
    except Exception as e:
        st.error(f"Error drawing layout: {e}")

with tab_lobby:
    st.subheader("The Weekend Sweat Feed")
    try:
        lobby_res = supabase.table("user_picks").select("*").eq("gameweek", 1).execute()
        all_picks = lobby_res.data
        if not all_picks:
            st.info("Nobody has locked in a team for Gameweek 1 yet.")
        else:
            for p in all_picks:
                st.markdown(f"👤 **{p['user_id']}** has locked in **{p['team_picked']}**")
    except Exception as lobby_err:
        st.error(f"Could not load lobby data: {lobby_err}")

with tab_admin:
    st.subheader("System Administration Panel")
    if st.button("Run Live Fixture Refresher"):
        url = "https://v3.football.api-sports.io/fixtures"
        headers = {
            "x-rapidapi-key": API_KEY,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
        leagues = [39, 179]
        season = 2024  
        
        for league_id in leagues:
            try:
                response = requests.get(url, headers=headers, params={"league": league_id, "season": season})
                data = response.json()
                items = data.get("response", [])
                fixtures_to_upsert = []
                for item in items:
                    round_str = item["league"].get("round", "")
                    digits = ''.join(filter(str.isdigit, round_str))
                    if not digits: continue
                    
                    fixtures_to_upsert.append({
                        "id": item["fixture"]["id"],
                        "league_id": league_id,
                        "gameweek": int(digits),
                        "kickoff_time": item["fixture"]["date"],
                        "home_team": item["teams"]["home"]["name"],
                        "away_team": item["teams"]["away"]["name"],
                        "status": item["fixture"]["status"]["short"],
                        "winner": item["teams"]["home"]["name"] if item["teams"]["home"].get("winner") is True else (item["teams"]["away"]["name"] if item["teams"]["away"].get("winner") is True else ("DRAW" if item["fixture"]["status"]["short"] == "FT" else None))
                    })
                if fixtures_to_upsert:
                    supabase.table("fixtures").upsert(fixtures_to_upsert).execute()
                    st.success(f"✅ Synchronized League {league_id}!")
            except Exception as e:
                st.error(f"💥 Error: {str(e)}")
