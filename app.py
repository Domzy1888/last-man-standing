import streamlit as st
import datetime
import requests
from supabase import create_client

# Initialize Supabase Client Connection
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
API_KEY = st.secrets["FOOTBALL_API_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Last Man Standing", page_icon="⚽", layout="wide")

# CSS Overhaul for a Premium Sportsbook Sans-Serif Minimalist Presentation
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.custom-metric { background: #1e293b; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #334155; }
.metric-val { font-size: 1.8rem; font-weight: 800; color: #38bdf8; }

.league-header { 
    font-size: 1.1rem; 
    font-weight: 800; 
    color: #94a3b8; 
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 35px 0 15px 0; 
    text-align: center;
}

.match-row-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 18px 0;
    font-family: 'Inter', sans-serif;
}

.match-teams-line {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    font-size: 1.3rem; 
    font-weight: 700; 
    text-transform: uppercase;
    letter-spacing: 0.02em;
}

.team-badge {
    width: 28px;
    height: 28px;
    object-fit: contain;
}

.vs-divider {
    font-size: 0.95rem;
    color: #64748b;
    font-weight: 400;
    text-transform: lowercase;
    margin: 0 4px;
}

.time-text { 
    color: #64748b; 
    font-size: 0.9rem; 
    font-weight: 500;
    margin-top: 6px;
    text-transform: uppercase;
}

.locked-box { background: #065f46; color: #a7f3d0; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 1px solid #047857; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ Last Man Standing")
st.caption("EPL & William Hill Premiership Survival League")

# --- Temporary Player Profile Setup ---
players_list = ["Callum", "Jamie", "Ross", "Stuart", "Chris"]
current_user = st.sidebar.selectbox("👤 Select Your Player Profile", players_list)

entrance_fee = 10
total_prizepot = len(players_list) * entrance_fee

# --- Scoreboard Analytics Dashboard ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="custom-metric"><small>Your Status</small><div class="metric-val">ALIVE</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="custom-metric"><small>Current Round</small><div class="metric-val">Gameweek 1</div><small style="color:#94a3b8;">Aug 16 - Aug 18</small></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="custom-metric"><small>Total Survivors</small><div class="metric-val">{len(players_list)}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="custom-metric"><small>Total Prize Pot</small><div class="metric-val">£{total_prizepot}</div></div>', unsafe_allow_html=True)

st.divider()

tab_picks, tab_lobby, tab_admin = st.tabs(["🎯 Make Your Pick", "📊 User Selections", "⚙️ Admin Toolkit"])

with tab_picks:
    st.subheader("Available Matches")
    target_gw = 1 
    
    try:
        pick_check = supabase.table("user_picks").select("*").eq("user_id", current_user).eq("gameweek", target_gw).execute()
        existing_pick = pick_check.data
        
        past_picks_res = supabase.table("user_picks").select("team_picked").eq("user_id", current_user).execute()
        burned_teams = [p["team_picked"] for p in past_picks_res.data] if past_picks_res.data else []
        
        res = supabase.table("fixtures").select("*").order("kickoff_time").execute()
        all_fixtures = res.data
        
        if not all_fixtures:
            st.info("No fixtures found in database. Go to Admin Toolkit and run the sync engine.")
        else:
            fixtures = [
                f for f in all_fixtures 
                if f.get("gameweek") is not None and int(float(f["gameweek"])) == target_gw
            ]
            
            epl_fixtures = [f for f in fixtures if f["league_id"] == 39]
            spfl_fixtures = [f for f in fixtures if f["league_id"] == 179]
            
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
                selectable_options = ["-- Select Team --"] + [team for team in available_teams if team not in burned_teams]
                selected_pick = st.selectbox(f"Choose your single survival squad for Gameweek {target_gw}:", selectable_options)
                
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
            
            # --- UNIFIED FLUID LIST VIEW (NO DIVIDERS, CENTERED, BADGES INCLUDED) ---
            def render_flat_fixtures(league_title, league_list):
                if league_list:
                    st.markdown(f"<div class='league-header'>{league_title}</div>", unsafe_allow_html=True)
                    for f in league_list:
                        try:
                            kickoff = datetime.datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))
                            kickoff_display = kickoff.strftime("%a %H:%M")
                        except:
                            kickoff_display = str(f["kickoff_time"])
                        
                        # Fallback placeholders if sync engine hasn't populated badges yet
                        home_logo = f.get("home_logo") or "https://media.api-sports.io/football/teams/placeholder.png"
                        away_logo = f.get("away_logo") or "https://media.api-sports.io/football/teams/placeholder.png"
                        
                        st.markdown(f"""
                        <div class='match-row-container'>
                            <div class='match-teams-line'>
                                <img src='{home_logo}' class='team-badge' />
                                <span>{f['home_team']}</span>
                                <span class='vs-divider'>vs</span>
                                <span>{f['away_team']}</span>
                                <img src='{away_logo}' class='team-badge' />
                            </div>
                            <div class='time-text'>🕒 {kickoff_display}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write(f"ℹ️ No active fixtures found for {league_title}.")
            
            render_flat_fixtures("🏴󠁧󠁢󠁥󠁮󠁧󠁿 English Premier League", epl_fixtures)
            render_flat_fixtures("🏴󠁧󠁢󠁳󠁣󠁴󠁿 William Hill Scottish Premiership", spfl_fixtures)
            
    except Exception as e:
        st.error(f"Error drawing layout: {e}")

with tab_lobby:
    st.subheader("LMS User Selections Feed")
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
                        "home_logo": item["teams"]["home"].get("logo"),
                        "away_logo": item["teams"]["away"].get("logo"),
                        "status": item["fixture"]["status"]["short"],
                        "winner": item["teams"]["home"]["name"] if item["teams"]["home"].get("winner") is True else (item["teams"]["away"]["name"] if item["teams"]["away"].get("winner") is True else ("DRAW" if item["fixture"]["status"]["short"] == "FT" else None))
                    })
                if fixtures_to_upsert:
                    supabase.table("fixtures").upsert(fixtures_to_upsert).execute()
                    st.success(f"✅ Synchronized League {league_id} with Team Badges!")
            except Exception as e:
                st.error(f"💥 Error: {str(e)}")
