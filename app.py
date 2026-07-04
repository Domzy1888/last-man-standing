import streamlit as st
import datetime
import requests
from bs4 import BeautifulSoup
from supabase import create_client

# Initialize Supabase Client Connection
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

.team-name {
    display: inline-block;
}

.center-vs-group {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0 4px;
}

.team-badge {
    width: 32px;
    height: 32px;
    object-fit: contain;
}

.vs-divider {
    font-size: 0.95rem;
    color: #64748b;
    font-weight: 400;
    text-transform: lowercase;
}

.time-text { 
    color: #64748b; 
    font-size: 0.9rem; 
    font-weight: 500;
    margin-top: 8px;
    text-transform: uppercase;
}

.locked-box { background: #065f46; color: #a7f3d0; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 1px solid #047857; }
</style>
""", unsafe_allow_html=True)

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
    st.markdown('<div class="custom-metric"><small>Current Round</small><div class="metric-val">Gameweek 1</div><small style="color:#94a3b8;">Live Scraped Lines</small></div>', unsafe_allow_html=True)
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
        # Gracefully handle queries without throwing UUID type format breaks
        pick_check = supabase.table("user_picks").select("*").eq("gameweek", target_gw).execute()
        existing_pick = [p for p in pick_check.data if str(p.get("user_id")) == current_user or p.get("username") == current_user]
        
        past_picks_res = supabase.table("user_picks").select("*").execute()
        burned_teams = [p["team_picked"] for p in past_picks_res.data if p.get("username") == current_user or str(p.get("user_id")) == current_user]
        
        res = supabase.table("fixtures").select("*").order("kickoff_time").execute()
        all_fixtures = res.data
        
        if not all_fixtures:
            st.info("No fixtures found in database. Go to Admin Toolkit and scrape fresh fixtures.")
        else:
            fixtures = [
                f for f in all_fixtures 
                if f.get("gameweek") is not None and int(float(f["gameweek"])) == target_gw
            ]
            
            epl_fixtures = [f for f in fixtures if str(f["league_id"]).upper() == "EPL"]
            spfl_fixtures = [f for f in fixtures if str(f["league_id"]).upper() == "SPFL"]
            
            available_teams = sorted(list(set(
                [f["home_team"] for f in fixtures] + [f["away_team"] for f in fixtures]
            )))
            
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
                            # Use an insert structure that safely sets alternate identifier if text usernames are supported
                            payload = {
                                "gameweek": target_gw,
                                "team_picked": selected_pick
                            }
                            # Check if your table uses user_id as a text column or fallback field
                            try:
                                payload["user_id"] = current_user
                                supabase.table("user_picks").insert(payload).execute()
                            except:
                                payload.pop("user_id", None)
                                payload["username"] = current_user
                                supabase.table("user_picks").insert(payload).execute()
                                
                            st.success(f"Success! {selected_pick} is saved.")
                            st.rerun()
                        except Exception as save_err:
                            st.error(f"Failed to submit entry: {save_err}")
            
            st.divider()
            
            def render_flat_fixtures(league_title, league_list):
                if league_list:
                    st.markdown(f"<div class='league-header'>{league_title}</div>", unsafe_allow_html=True)
                    for f in league_list:
                        home_logo = f.get("home_logo") or "https://img.icons8.com/ios-filled/50/ffffff/football-ball.png"
                        away_logo = f.get("away_logo") or "https://img.icons8.com/ios-filled/50/ffffff/football-ball.png"
                        
                        st.markdown(f"""
                        <div class='match-row-container'>
                            <div class='match-teams-line'>
                                <span class='team-name'>{f['home_team']}</span>
                                <div class='center-vs-group'>
                                    <img src='{home_logo}' class='team-badge' />
                                    <span class='vs-divider'>vs</span>
                                    <img src='{away_logo}' class='team-badge' />
                                </div>
                                <span class='team-name'>{f['away_team']}</span>
                            </div>
                            <div class='time-text'>🕒 {f['kickoff_time']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write(f"ℹ️ No fixtures found for {league_title}.")
            
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
                user_display = p.get('username') or p.get('user_id')
                st.markdown(f"👤 **{user_display}** has locked in **{p['team_picked']}**")
    except Exception as lobby_err:
        st.error(f"Could not load lobby data: {lobby_err}")

with tab_admin:
    st.subheader("📡 Live Sky Sports Fixture Scraper")
    st.info("Scrapes active match blocks directly from live Sky Sports broadcasting rows.")
    
    scrape_gw = st.number_input("Target Gameweek Identifier", min_value=1, max_value=38, value=1)
    
    if st.button("Scrape & Sync Live Schedules"):
        targets = [
            {"league": "EPL", "url": "https://www.skysports.com/premier-league-fixtures"},
            {"league": "SPFL", "url": "https://www.skysports.com/scottish-premiership-fixtures"}
        ]
        
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
        unique_id_counter = int(datetime.datetime.now().timestamp())
        
        for target in targets:
            st.write(f"🕵️‍♂️ Scanning rows for **{target['league']}**...")
            try:
                response = requests.get(target["url"], headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Targets both 'div' and anchor link structures ('a') used by Sky Sports layout updates
                match_groups = soup.find_all(['div', 'a'], class_='fixres__item')
                
                fixtures_to_upsert = []
                for item in match_groups[:12]: 
                    home_el = item.find('span', class_='matches__participant--home')
                    away_el = item.find('span', class_='matches__participant--away')
                    time_el = item.find('span', class_='matches__date')
                    
                    if home_el and away_el:
                        home_name = home_el.find('span', class_='swap-text__target').text.strip()
                        away_name = away_el.find('span', class_='swap-text__target').text.strip()
                        match_time = time_el.text.strip() if time_el else "TBD"
                        
                        unique_id_counter += 1
                        fixtures_to_upsert.append({
                            "id": unique_id_counter,
                            "league_id": target["league"],
                            "gameweek": int(scrape_gw),
                            "kickoff_time": match_time,
                            "home_team": home_name,
                            "away_team": away_name,
                            "home_logo": f"https://img.icons8.com/ios-filled/50/38bdf8/football-ball.png",
                            "away_logo": f"https://img.icons8.com/ios-filled/50/38bdf8/football-ball.png",
                            "status": "NS",
                            "winner": "DRAW"
                        })
                
                if fixtures_to_upsert:
                    supabase.table("fixtures").upsert(fixtures_to_upsert).execute()
                    st.success(f"✅ Loaded {len(fixtures_to_upsert)} live matches into {target['league']} panel!")
                else:
                    st.warning(f"Could not parse any structured match elements for {target['league']}. Checking structural layout fallback...")
            except Exception as e:
                st.error(f"💥 Failed scanning row data: {str(e)}")
