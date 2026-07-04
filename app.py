import streamlit as st
import datetime
from supabase import create_client

# Initialize Supabase Client Connection for recording survival selections
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Last Man Standing", page_icon="⚽", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;600;800&display=swap');

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
    padding: 20px 0;
}

.match-teams-line {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
    font-size: 1.3rem; 
    font-weight: 800; 
    text-transform: uppercase;
    letter-spacing: 0.02em;
    flex-wrap: wrap;
}

.team-name { display: inline-block; }
.center-vs-group { display: flex; align-items: center; gap: 10px; margin: 0 4px; }
.team-badge { width: 32px; height: 32px; object-fit: contain; }
.vs-divider { font-size: 0.95rem; color: #64748b; font-weight: 400; text-transform: lowercase; }
.time-text { color: #64748b; font-size: 0.9rem; font-weight: 500; margin-top: 8px; text-transform: uppercase; }
.locked-box { background: #065f46; color: #a7f3d0; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 1px solid #047857; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 🏟️ MASTER FIXTURE DATA DICTIONARY (2026/27 SEASON)
# ----------------------------------------------------
FIXTURE_DATABASE = {
    1: {
        "start_date": datetime.date(2026, 7, 29),  # Wednesday
        "end_date": datetime.date(2026, 8, 25),    # Extended to include opening rounds
        "EPL": [
            {"home": "Arsenal", "away": "Coventry City", "time": "Fri 21 Aug - 20:00"},
            {"home": "Hull City", "away": "Manchester United", "time": "Sat 22 Aug - 12:30"},
            {"home": "Everton", "away": "Crystal Palace", "time": "Sat 22 Aug - 15:00"},
            {"home": "Ipswich Town", "away": "Sunderland", "time": "Sat 22 Aug - 15:00"},
            {"home": "Nottingham Forest", "away": "Leeds United", "time": "Sat 22 Aug - 15:00"},
            {"home": "Brentford", "away": "Tottenham Hotspur", "time": "Sat 22 Aug - 17:30"},
            {"home": "Brighton & Hove Albion", "away": "Aston Villa", "time": "Sun 23 Aug - 14:00"},
            {"home": "Manchester City", "away": "AFC Bournemouth", "time": "Sun 23 Aug - 14:00"},
            {"home": "Newcastle United", "away": "Liverpool", "time": "Sun 23 Aug - 16:30"},
            {"home": "Fulham", "away": "Chelsea", "time": "Mon 24 Aug - 20:00"}
        ],
        "SPFL": [
            {"home": "Dundee United", "away": "Rangers", "time": "Fri 31 Jul - 20:00"},
            {"home": "Falkirk", "away": "St Mirren", "time": "Sat 1 Aug - 15:00"},
            {"home": "Aberdeen", "away": "Heart of Midlothian", "time": "Sat 1 Aug - 17:30"},
            {"home": "St Johnstone", "away": "Kilmarnock", "time": "Sun 2 Aug - 14:00"},
            {"home": "Hibernian", "away": "Motherwell", "time": "Sun 2 Aug - 16:30"},
            {"home": "Celtic", "away": "Dundee", "time": "Mon 3 Aug - 19:30"}
        ]
    },
    2: {
        "start_date": datetime.date(2026, 8, 26), # Wednesday
        "end_date": datetime.date(2026, 9, 1),    # Tuesday
        "EPL": [
            {"home": "AFC Bournemouth", "away": "Everton", "time": "Sat 29 Aug - 15:00"},
            {"home": "Aston Villa", "away": "Arsenal", "time": "Sat 29 Aug - 15:00"},
            {"home": "Chelsea", "away": "Brighton & Hove Albion", "time": "Sat 29 Aug - 15:00"},
            {"home": "Coventry City", "away": "Hull City", "time": "Sat 29 Aug - 15:00"},
            {"home": "Crystal Palace", "away": "Manchester City", "time": "Sat 29 Aug - 15:00"},
            {"home": "Leeds United", "away": "Brentford", "time": "Sat 29 Aug - 15:00"},
            {"home": "Liverpool", "away": "Nottingham Forest", "time": "Sat 29 Aug - 15:00"},
            {"home": "Manchester United", "away": "Ipswich Town", "time": "Sat 29 Aug - 15:00"},
            {"home": "Sunderland", "away": "Fulham", "time": "Sat 29 Aug - 15:00"},
            {"home": "Tottenham Hotspur", "away": "Newcastle United", "time": "Sat 29 Aug - 15:00"}
        ],
        "SPFL": [
            {"home": "Dundee", "away": "Aberdeen", "time": "Sat 8 Aug - 15:00"},
            {"home": "Heart of Midlothian", "away": "Dundee United", "time": "Sat 8 Aug - 15:00"},
            {"home": "Motherwell", "away": "Falkirk", "time": "Sat 8 Aug - 15:00"},
            {"home": "St Mirren", "away": "St Johnstone", "time": "Sat 8 Aug - 15:00"},
            {"home": "Kilmarnock", "away": "Celtic", "time": "Sun 9 Aug - 13:30"},
            {"home": "Rangers", "away": "Hibernian", "time": "Sun 9 Aug - 16:00"}
        ]
    }
}

# ----------------------------------------------------
# 📅 AUTOMATIC GAMEWEEK DETECTION CALCULATION
# ----------------------------------------------------
today = datetime.date.today()
current_calculated_gw = 1 # Fallback default

for gw, bounds in FIXTURE_DATABASE.items():
    if bounds["start_date"] <= today <= bounds["end_date"]:
        current_calculated_gw = gw
        break

st.title("⚽ Last Man Standing")
st.caption("EPL & William Hill Premiership Survival League")

players_list = ["Callum", "Jamie", "Ross", "Stuart", "Chris"]
current_user = st.sidebar.selectbox("👤 Select Your Player Profile", players_list)

entrance_fee = 10
total_prizepot = len(players_list) * entrance_fee

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="custom-metric"><small>Your Status</small><div class="metric-val">ALIVE</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="custom-metric"><small>Current Calendar Round</small><div class="metric-val">Gameweek {current_calculated_gw}</div><small style="color:#38bdf8;">Hardcoded Roster</small></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="custom-metric"><small>Total Survivors</small><div class="metric-val">{len(players_list)}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="custom-metric"><small>Total Prize Pot</small><div class="metric-val">£{total_prizepot}</div></div>', unsafe_allow_html=True)

st.divider()

# Main player viewing environment
gw_to_show = st.selectbox("📅 View Roster Sheet For:", list(FIXTURE_DATABASE.keys()), index=current_calculated_gw-1)
selected_gw_data = FIXTURE_DATABASE[gw_to_show]

tab_picks, tab_lobby = st.tabs(["🎯 Make Your Pick", "📊 User Selections"])

with tab_picks:
    try:
        # DB syntax error handling using a safe user identifier format
        pick_check = supabase.table("user_picks").select("*").eq("gameweek", gw_to_show).execute()
        existing_pick = [p for p in pick_check.data if p.get("username") == current_user or str(p.get("user_id")) == current_user]
        
        past_picks_res = supabase.table("user_picks").select("*").execute()
        burned_teams = [p["team_picked"] for p in past_picks_res.data if p.get("username") == current_user or str(p.get("user_id")) == current_user]
        
        # Build available list from the dictionary structure instead of an external web request
        all_teams_in_gw = []
        for match in selected_gw_data["EPL"] + selected_gw_data["SPFL"]:
            all_teams_in_gw.extend([match["home"], match["away"]])
        available_teams = sorted(list(set(all_teams_in_gw)))
        
        st.markdown("### 🔒 Lock In Your Team")
        
        if existing_pick:
            locked_team = existing_pick[0]["team_picked"]
            st.markdown(f"""
            <div class="locked-box">
                🔒 You have officially locked in {locked_team} for Gameweek {gw_to_show}!
            </div>
            """, unsafe_allow_html=True)
        else:
            selectable_options = ["-- Select Team --"] + [team for team in available_teams if team not in burned_teams]
            selected_pick = st.selectbox(f"Choose your survival squad for Gameweek {gw_to_show}:", selectable_options)
            
            if selected_pick != "-- Select Team --":
                if st.button(f"Confirm & Lock {selected_pick}"):
                    payload = {"gameweek": gw_to_show, "team_picked": selected_pick}
                    try:
                        payload["user_id"] = current_user
                        supabase.table("user_picks").insert(payload).execute()
                    except:
                        payload.pop("user_id", None)
                        payload["username"] = current_user
                        supabase.table("user_picks").insert(payload).execute()
                        
                    st.success(f"Success! {selected_pick} is securely saved.")
                    st.rerun()
        
        st.divider()
        
        # Render lists elegantly out of the explicit dictionary payload
        def draw_league_fixtures(title, matches_list):
            st.markdown(f"<div class='league-header'>{title}</div>", unsafe_allow_html=True)
            for m in matches_list:
                logo = "https://img.icons8.com/ios-filled/50/ffffff/football-ball.png"
                st.markdown(f"""
                <div class='match-row-container'>
                    <div class='match-teams-line'>
                        <span class='team-name'>{m['home']}</span>
                        <div class='center-vs-group'>
                            <img src='{logo}' class='team-badge' />
                            <span class='vs-divider'>vs</span>
                            <img src='{logo}' class='team-badge' />
                        </div>
                        <span class='team-name'>{m['away']}</span>
                    </div>
                    <div class='time-text'>🕒 {m['time']}</div>
                </div>
                """, unsafe_allow_html=True)

        draw_league_fixtures("🏴󠁧󠁢󠁥󠁮󠁧󠁿 English Premier League", selected_gw_data["EPL"])
        draw_league_fixtures("🏴󠁧󠁢󠁳󠁣󠁴󠁿 William Hill Scottish Premiership", selected_gw_data["SPFL"])
            
    except Exception as e:
        st.error(f"Error drawing layout: {e}")

with tab_lobby:
    st.subheader(f"LMS Selection Feed (Gameweek {gw_to_show})")
    try:
        lobby_res = supabase.table("user_picks").select("*").eq("gameweek", gw_to_show).execute()
        all_picks = lobby_res.data
        if not all_picks:
            st.info(f"Nobody has locked in a team for Gameweek {gw_to_show} yet.")
        else:
            for p in all_picks:
                user_display = p.get('username') or p.get('user_id')
                st.markdown(f"👤 **{user_display}** has locked in **{p['team_picked']}**")
    except Exception as lobby_err:
        st.error(f"Could not load lobby data: {lobby_err}")
