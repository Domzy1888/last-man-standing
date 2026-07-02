import streamlit as st
import datetime
from supabase import create_client

# 1. Initialize Supabase Client
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Modern App Styling & Theming ---
st.set_page_config(page_title="SQUAD LOCK // LMS", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 800; color: #38bdf8; }
    .league-header { background: #1e293b; padding: 10px; border-radius: 6px; margin: 15px 0 10px 0; font-weight: bold; }
    .match-card { border: 1px solid #334155; padding: 12px; border-radius: 8px; margin-bottom: 10px; background-color: #0f172a; }
    </style>
""", unsafe_with_html=True)

st.title("⚽ SQUAD LOCK")
st.caption("EPL & William Hill Premiership Last Man Standing")

# --- Simple Session User Selector (Until Auth is fully added) ---
# Replace this array with your actual friend group names
players_list = ["Callum", "Jamie", "Ross", "Stuart", "Chris"]
current_user = st.sidebar.selectbox("👤 Select Your Player Profile", players_list)

# --- Top App Scoreboard Analytics ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Your Status", value="ALIVE", delta="Active Pool")
with col2:
    st.metric(label="Current Round", value="Gameweek 1")
with col3:
    st.metric(label="Total Survivors", value=f"{len(players_list)} / {len(players_list)}")

st.divider()

# --- Main App Core Interfaces ---
tab_picks, tab_lobby, tab_admin = st.tabs(["🎯 Make Your Pick", "📊 Live Lobby", "⚙️ Admin Toolkit"])

with tab_picks:
    st.subheader("Available Matches")
    
    # Target current dynamic gameweek bracket (Default to Week 1 for initial setups)
    target_gw = 1 
    
    # Fetch real live synced fixtures out of Supabase
    try:
        res = supabase.table("fixtures").select("*").eq("gameweek", target_gw).order("kickoff_time").execute()
        fixtures = res.data
        
        if not fixtures:
            st.info("No fixtures found in database for this Gameweek yet. Run sync engine.")
        else:
            # Separate teams this user has already picked previously to prevent illegal double selections
            # (We will hook this up dynamically to the database table next)
            burned_teams = [] 
            
            # Categorize fixtures by league
            epl_fixtures = [f for f in fixtures if f["league_id"] == 39]
            spfl_fixtures = [f for f in fixtures if f["league_id"] == 75]
            
            def render_league_fixtures(league_title, league_list):
                if league_list:
                    st.markdown(f"<div class='league-header'>{league_title}</div>", unsafe_with_html=True)
                    for f in league_list:
                        kickoff = datetime.datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))
                        kickoff_display = kickoff.strftime("%a %H:%M")
                        
                        # Generate unique keys per fixture to manage layout states safely
                        with st.container():
                            st.markdown(f"""
                            <div class='match-card'>
                                <strong>{f['home_team']}</strong> vs <strong>{f['away_team']}</strong><br/>
                                <small style='color: #94a3b8;'>📅 Kickoff: {kickoff_display}</small>
                            </div>
                            """, unsafe_with_html=True)
                            
                            # Let users select from the match pairs
                            options = ["-- Choose Team --", f['home_team'], f['away_team']]
                            clean_options = [opt for opt in options if opt not in burned_teams]
                            
                            selected_team = st.selectbox(
                                f"Lock selection for {f['home_team']} v {f['away_team']}", 
                                clean_options, 
                                key=f"sel_{f['id']}"
                            )
                            
                            if selected_team != "-- Choose Team --":
                                if st.button(f"Confirm Pick: {selected_team}", key=f"btn_{f['id']}"):
                                    st.success(f"Locked in {selected_team} for Gameweek {target_gw}!")
                                    # Form payload will be written to user_picks table here
            
            render_league_fixtures("🏴󠁧󠁢󠁥󠁮󠁧󠁿 English Premier League", epl_fixtures)
            render_league_fixtures("🏴󠁧󠁢󠁳󠁣󠁴󠁿 William Hill Scottish Premiership", spfl_fixtures)
            
    except Exception as e:
        st.error(f"Error drawing structural layout options: {e}")

with tab_lobby:
    st.subheader("The Weekend Sweat Feed")
    st.write("Review what squads your mates have locked down for survival.")
    # Real-time lobby leaderboard will load here from user_picks queries

with tab_admin:
    st.subheader("System Administration Panel")
    if st.button("Run Live Fixture Refresher"):
        from sync_fixtures import sync_fixtures
        with st.spinner("Re-syncing latest data arrays..."):
            sync_fixtures()
            st.success("Schedules updated!")
