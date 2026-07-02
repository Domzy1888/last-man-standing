import streamlit as st
from sync_fixtures import sync_fixtures
from supabase import create_client

# Connect to database via Streamlit Secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("⚽ SQUAD LOCK // LMS")

# --- Temporary Sync Tool Panel ---
with st.expander("⚙️ Admin Database Controls"):
    st.write("Click below to fetch the initial fixture schedules into Supabase.")
    if st.button("Run System Fixture Sync"):
        with st.spinner("Calling API-Football & parsing leagues..."):
            try:
                sync_fixtures()
                st.success("Fixtures synchronized successfully!")
            except Exception as e:
                st.error(f"Sync failed: {e}")
