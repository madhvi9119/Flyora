import streamlit as st
from datetime import date, datetime,timedelta
from database import get_connection  # import DB connection

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Airline Booking Platform",
    page_icon="✈️",
    layout="centered"
)

st.markdown("""
<style>
/* Hide sidebar nav already exists in your code */
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------
if "user_id" not in st.session_state:
    st.session_state.user_id = None  # Track if user is logged in

if "username" not in st.session_state:
    st.session_state.username = ""  # Store logged in user's name

if "flights" not in st.session_state:
    st.session_state.flights = []

if "login_success_message" in st.session_state:
    st.toast(st.session_state.login_success_message)
    del st.session_state.login_success_message


with st.sidebar:
    st.sidebar.title("Navigation")

    # ---------- NOT LOGGED IN ----------
    if st.session_state.get("user_id") is None:
        if st.button("🔐 Login / Create Account"):
            st.session_state.redirect_page = "app.py"  # or current page
            st.switch_page("pages/login.py")

    # ---------- LOGGED IN ----------
    else:
        st.write(f"👤 {st.session_state.username}")

        if st.button("Your Bookings"):
            st.switch_page("pages/your_bookings.py")

        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.switch_page("pages/login.py")



# ---------------- HEADER ----------------
st.title("✈️ Airline Booking Platform")
st.write("Welcome! Book your flight easily by selecting your route and travel date.")
st.divider()

# ---------------- ROUTE SELECTION ----------------
st.subheader("Search Flights")

locations = ["Delhi", "Mumbai", "Hyderabad", "Chennai", "Kolkata"]

col1,col_mid, col2 = st.columns([4,1,4])

# Restore previous search values if available
source = st.session_state.get("source", "")
destination = st.session_state.get("destination", "")

with col1:
    source = st.selectbox(
        "🛫 From",
        options=locations,
        index=locations.index(source) if source in locations else None,
        placeholder="Select source city"
    )

with col_mid:
    st.write("")
    st.write("")
    if st.button("🔄"):
        if source and destination:
            st.session_state.source, st.session_state.destination = (
            destination, source
        )
            st.rerun()

with col2:
    destination = st.selectbox(
        "🛬 To",
        options=locations,
        index=locations.index(destination) if destination in locations else None,
        placeholder="Select destination city"
    )

# Save selections in session_state
st.session_state.source = source
st.session_state.destination = destination

# ----------  VALIDATION ----------
if source and destination and source == destination:
    st.warning("⚠️ Source and destination cannot be the same.")

# ---------------- DATE SELECTION ----------------
try:
    min_date = date.today()
    max_date = date.today() + timedelta(days=90)

    stored_date = st.session_state.get("travel_date", min_date)
    
    # Fix invalid stored date
    if stored_date < min_date or stored_date > max_date:
        stored_date = min_date

    travel_date = st.date_input(
    "📅 Travel Date",
    min_value=min_date,
    max_value=max_date,
    value=stored_date

)
    st.session_state.travel_date = travel_date
except Exception:
    st.error("Something went wrong with date selection")
# ---------------- SEARCH FLIGHTS ----------------
if st.button("Search Flights", use_container_width=True):
    st.session_state.flights = []  # clear old search results

    if not source or not destination:
        st.warning("Please select both source and destination.")

    elif source == destination:
        st.error("Source and destination cannot be the same.")

    else:
        conn = get_connection()
        if conn:
            try:
                cursor = conn.cursor()

                today = date.today()
                now_time = datetime.now().strftime("%H:%M")

                if travel_date == today:
                    cursor.execute("""
                        SELECT flight_id, airline, flight_number,
                               departure_time, arrival_time,
                               economy_price, business_price, travel_date
                        FROM flights
                        WHERE source = ?
                          AND destination = ?
                          AND travel_date = ?
                          AND departure_time > ?
                    """, (source, destination, str(travel_date), now_time))
                else:
                    cursor.execute("""
                        SELECT flight_id, airline, flight_number,
                               departure_time, arrival_time,
                               economy_price, business_price, travel_date
                        FROM flights
                        WHERE source = ?
                          AND destination = ?
                          AND travel_date = ?
                    """, (source, destination, str(travel_date)))

                flights = cursor.fetchall()
                st.session_state.flights = flights
                # Redirect to search results page
                st.switch_page("pages/search_results.py")
                

            except Exception as e:
                st.error(f"❌ Error fetching flights: {e}")

            finally:
                conn.close()




