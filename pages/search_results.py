import streamlit as st
from datetime import datetime

st.markdown("""
<style>
/* Hide sidebar nav already exists in your code */
[data-testid="stSidebarNav"] {display: none;}
            
/* Flight card hover effect */
.card {
    padding:10px;
    border:1px solid #ccc;
    border-radius:8px;
    margin-bottom:10px;
    transition: transform 0.2s ease-in-out;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.card:hover {
    transform: scale(1.02);
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    if st.button("🔍 Back to Search Routes"):
        st.switch_page("app.py")


st.title("✈️ Flight Results")
st.divider()

if "login_success_message" in st.session_state:
    st.toast(st.session_state.login_success_message)
    del st.session_state.login_success_message


if "flights" not in st.session_state or not st.session_state.flights:
    st.warning("⚠️ No search results found. Go back and search again.")
    st.stop()

flight_found = False
for f in st.session_state.flights:
    flight_id, airline, flight_number, dep, arr, eco_price, bus_price, flight_date_str = f
    flight_date = datetime.strptime(flight_date_str, "%Y-%m-%d").date()

    # Combine date and departure time
    departure_datetime = datetime.strptime(
    f"{flight_date_str} {dep}",
    "%Y-%m-%d %H:%M")

# Skip flights whose departure time has passed
    if departure_datetime < datetime.now():
        continue
    flight_found = True

    with st.container():
        st.markdown(f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong>✈️ {airline} ({flight_number})</strong><br>
                    Route: {st.session_state.source} → {st.session_state.destination}<br>
                    Date: {flight_date.strftime('%d-%b-%Y')}<br>
                    Departure: {dep} | Arrival: {arr}
                </div>
                <div>
                    Economy: ₹{eco_price}<br>
                    Business: ₹{bus_price}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


        if st.session_state.user_id:
            if st.button("Book Now", key=f"book_{flight_id}"):
                st.session_state.selected_seats = []  # ← ADD THIS LINE (clear old seats)
                st.session_state.selected_flight_id = flight_id
                st.session_state.selected_flight_details = {
                    "flight_id": flight_id,
                    "airline": airline,
                    "flight_number": flight_number,
                    "source": st.session_state.source,
                    "destination": st.session_state.destination,
                    "travel_date": flight_date_str,
                    "departure_time": dep,
                    "arrival_time": arr,
                    "eco_price": eco_price,
                    "bus_price": bus_price
                }                

                st.switch_page("pages/booking.py")
        else:
            if st.button("Login to Book", key=f"login_{flight_id}"):
                    # st.session_state.pending_flight_id = flight_id   # TEMP only
                    st.session_state.redirect_page = "pages/search_results.py"
                    st.switch_page("pages/login.py")
if not flight_found:
            st.info("✈️ No flights are available for the selected route and date.")       