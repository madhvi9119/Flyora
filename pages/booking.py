import streamlit as st
from aircraft_config import AIRCRAFTS
from database import get_connection

st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none;}

            /* Window seat button */
    .stButton button[key*="window"] { background-color: #e3f2fd; }
    /* Aisle seat button */
    .stButton button[key*="aisle"] { background-color: #f1f8e9; }
    /* Middle seat button */
    .stButton button[key*="middle"] { background-color: #fff3e0; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    if st.button(" Back to Flights"):
        st.switch_page("pages/search_results.py")


# ---------- SESSION STATE DEFAULTS ----------

# if "num_passengers" not in st.session_state:
#     st.session_state.num_passengers = 1
if "selected_seat_class" not in st.session_state:
    st.session_state.selected_seat_class = None
if "last_class" not in st.session_state:   
    st.session_state.last_class = None
if "selected_seats" not in st.session_state:
    st.session_state.selected_seats = []
if "total_amount" not in st.session_state:
    st.session_state.total_amount = 0
if "num_passengers" not in st.session_state:
    if "booking_info" in st.session_state:
        st.session_state.num_passengers = st.session_state.booking_info.get(
            "num_passengers", 1
        )
    else:
        st.session_state.num_passengers = 1

def get_seat_type(seat_number, total_cols):
    """
    Returns 'window', 'aisle', or 'middle' for standard single-aisle layouts.
    Works for total_cols = 2, 4, 6, 8... (even numbers).
    """
    letter = seat_number[-1]
    col_letters = ["A", "B", "C", "D", "E", "F", "G", "H"][:total_cols]  # extendable
    col_index = col_letters.index(letter)

    # Window: first or last column
    if col_index == 0 or col_index == total_cols - 1:
        return "window"

    # Aisle: middle two columns (for even total_cols)
    if total_cols % 2 == 0:
        aisle_left = total_cols // 2 - 1
        aisle_right = total_cols // 2
        if col_index in (aisle_left, aisle_right):
            return "aisle"

    # Otherwise it's a middle seat
    return "middle"


def calculate_total_amount(flight, seat_class, num_passengers):
    """
    Calculate the total amount for a flight booking.
    """
    if seat_class == "Economy":
        price_per_passenger = flight.get("eco_price", 0)
    elif seat_class == "Business":
        price_per_passenger = flight.get("bus_price", 0)
    else:
        price_per_passenger = 0
    
    total_amount = price_per_passenger * num_passengers
    return total_amount


# PROTECT BOOKING PAGE
if st.session_state.get("user_id") is None:
    st.warning("⚠️ Login required to access booking.")

    if st.button("Go to Login"):
        st.switch_page("pages/login.py")

    st.stop()


# Check flight selection
if st.session_state.get("selected_flight_id") is None:
    st.warning("No flight selected. Please search flights first.")

    if st.button("Go to Search Flights"):
        st.switch_page("pages/search_results.py")

    st.stop()

    
st.title("Flight Booking")

flight = st.session_state.get("selected_flight_details")
if not flight:
    st.error("Flight details not found. Please go back and select a flight.")
    st.stop()
if flight:
    
    current_flight_id = flight["flight_id"]
    
    if "current_booking_flight_id" not in st.session_state:
        st.session_state.current_booking_flight_id = current_flight_id
    
    # Only reset if user switched to a DIFFERENT flight
    if st.session_state.current_booking_flight_id != current_flight_id:
        st.session_state.last_class = None
        st.session_state.selected_seats = []
        # st.session_state.num_passengers = 1   # ADD THIS LINE
        st.session_state.current_booking_flight_id = current_flight_id

    st.subheader("Selected Flight Details")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.write("**Airline**")
        st.info(flight["airline"])

    with col2:
        st.write("**Route**")
        st.info(f'{flight["source"]} → {flight["destination"]}')

    with col3:
        st.write("**Date**")
        st.info(flight["travel_date"])

    with col4:
        st.write("**Time**")
        st.info(f'{flight["departure_time"]} → {flight["arrival_time"]}')
    

st.divider()

st.subheader("Passenger Details")

num_passengers = st.number_input(
    "Number of Passengers",
    min_value=1,max_value=6,
    step=1, 
    # value=st.session_state.get("num_passengers", 1),
    key="num_passengers"
)
seat_class = st.radio(
    "Select Class",
    ["Economy", "Business"],
     key="selected_seat_class"

)
if not seat_class:
    st.info("Please select seat class to continue")
    st.stop()


st.divider()

if seat_class and num_passengers > 0:
    total_amount = calculate_total_amount(flight, seat_class, num_passengers)
    st.session_state["total_amount"] = total_amount

if seat_class:
    if st.session_state.last_class is None:
        st.session_state.last_class = seat_class
    elif st.session_state.last_class != seat_class:
        st.session_state.selected_seats.clear()
        st.session_state.last_class = seat_class


# ---------- STEP 1: AUTO AVAILABILITY CHECK ----------
try:
    airline = flight["airline"]
    flight_id = flight["flight_id"]

    # Get aircraft layout
    layout = AIRCRAFTS[airline][seat_class]
    rows = layout["rows"] 
    cols = layout["cols"]
    seat_labels = ["A", "B", "C", "D", "E", "F"][:cols]

    total_seats = rows * cols
    # Get booked seats count from DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) 
        FROM seats 
        WHERE flight_id = ? AND class_name = ? AND is_booked = 1
        """,
        (flight_id, seat_class)
    )
    booked_seats = cursor.fetchone()[0]
    conn.close()

    available_seats = total_seats - booked_seats

except KeyError:
    st.error(" Aircraft configuration missing.")
    st.stop()

except Exception as e:
    st.error(" Error checking seat availability.")
    st.exception(e)
    st.stop()

# ---------- STEP 2: VALIDATE AVAILABILITY ----------
if available_seats < num_passengers:
    st.error("Not enough seats available for the selected class.")
    st.stop()
    
try:
    conn = get_connection()
    cursor = conn.cursor()
    # ====== AUTO-CREATE SEATS IF NEEDED ======
    cursor.execute("""
        SELECT COUNT(*) FROM seats 
        WHERE flight_id = ? AND class_name = ?
    """, (flight["flight_id"], seat_class))
 
    seats_exist = cursor.fetchone()[0] > 0
    
    if not seats_exist:
        # Create all seats for this class
        st.info("📋 Setting up seat map for this flight...")
        for r in range(1, rows + 1):
            for c in seat_labels:
                seat_no = f"{r}{c}"
                cursor.execute("""
                    INSERT INTO seats(flight_id, seat_number, class_name, is_booked)
                    VALUES (?, ?, ?, 0)
                """, (flight["flight_id"], seat_no, seat_class))
        conn.commit()
        st.success(f"✓ Created {rows * len(seat_labels)} available seats")
        st.rerun()
    cursor.execute("""
        SELECT seat_number FROM seats
        WHERE flight_id = ? AND class_name = ? AND is_booked = 1
    """, (flight["flight_id"], seat_class))

    booked_seat = {row[0] for row in cursor.fetchall()}
    # Build a dictionary with seat status and type                                                                                                
    seat_dict = {}
    for r in range(1, rows + 1):
        for c in seat_labels:
            seat_no = f"{r}{c}"
            is_booked = seat_no in booked_seat
            is_selected = seat_no in st.session_state.selected_seats

            if is_booked:
                status = "booked"
            elif is_selected:
                status = "selected"
            else:
                status = "free"

            seat_dict[seat_no] = {
            "status": status,
            "type": get_seat_type(seat_no, cols)   # <-- your new function
        }
    conn.close()

except Exception as e:
    st.error("Error loading booked seats")
    st.exception(e)
    st.stop()
st.subheader(f"{seat_class} Seat Selection")
st.write("⬛ Booked  🟩 Selected  ⬜ Available")

# --- Render seat grid ---
for r in range(1, rows + 1):
    # Create columns with an aisle gap if columns are even
    if cols % 2 == 0:
        half = cols // 2
        left_labels = seat_labels[:half]
        right_labels = seat_labels[half:]
        # column widths: left half, narrow gap, right half
        col_ui = st.columns([1] * half + [0.3] + [1] * half)
        seat_positions = left_labels + ["gap"] + right_labels
    else:
        col_ui = st.columns(cols)
        seat_positions = seat_labels

    for i, c in enumerate(seat_positions):
        if c == "gap":
            continue

        seat_no = f"{r}{c}"
        seat = seat_dict[seat_no]   # fetch status & type

        # Determine button label and disabled state
        if seat["status"] == "booked":
            label = f"⬛ {seat_no}"
            disabled = True
        elif seat["status"] == "selected":
            label = f"🟩 {seat_no}"
            disabled = False
        else:
            label = f"⬜ {seat_no}"   # clearer: white square for available
            
        # Only booked seats are disabled
        disabled = seat["status"] == "booked"
        # Tooltip with seat type
        tooltip = f"{seat['type'].title()} seat"

        # Render button
        if col_ui[i].button(
            label,
            key=f"seat_{seat_class}_{seat['type']}_{seat_no}",
            disabled=disabled,
            help=tooltip
        ):    # If already selected → deselect
                # Toggle / Replace logic
            if seat_no in st.session_state.selected_seats:
                st.session_state.selected_seats.remove(seat_no)
            else:
                # If limit reached → replace last seat instead of blocking all buttons
                if len(st.session_state.selected_seats) >= num_passengers:
                    st.session_state.selected_seats.pop(0)
                st.session_state.selected_seats.append(seat_no)
                # if len(st.session_state.selected_seats) < num_passengers:
                #     st.session_state.selected_seats.append(seat_no)
                #     st.rerun()
                # else:
                #     st.toast(
                #          f"You can select only {num_passengers} seat(s). "
                #                  "Please deselect a seat first.")
            st.rerun()

            

st.divider()
# if len(st.session_state.selected_seats) > num_passengers:
#     st.session_state.selected_seats = st.session_state.selected_seats[:num_passengers]

#st.info(f"🪑 Selected {len(st.session_state.selected_seats)} / {num_passengers} seats")

if st.session_state.selected_seats:
    st.success("Selected Seats: " + ", ".join(st.session_state.selected_seats))
# Dynamic total based on currently selected seats
price_per_passenger = flight.get("eco_price" if seat_class=="Economy" else "bus_price", 0)
current_total = len(st.session_state.selected_seats) * price_per_passenger
st.session_state.total_amount = current_total
st.divider()

# ---------- Booking Summary & Total Amount ----------
if "total_amount" in st.session_state and st.session_state.num_passengers > 0:
    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.success(f"**Selected Seats:** {len(st.session_state.selected_seats)} / {st.session_state.num_passengers}")
    with col_right:
        st.info(f"**Total Amount:** ₹{current_total}")
else:
    st.warning("Please select seat class and number of passengers.")

# --- Confirm button ---
confirm_disabled = len(st.session_state.selected_seats) != num_passengers

if confirm_disabled:
    st.warning(
        f"Please select exactly {num_passengers} seat(s). "
        f"You have selected {len(st.session_state.selected_seats)} seat(s)."
    )

if st.button(" Confirm Booking", disabled=confirm_disabled):
    st.session_state.booking_confirmed = True
    st.session_state.booking_info = {
        "flight_id": flight["flight_id"],
        "airline": flight["airline"],
        "flight_number": flight["flight_number"],
        "source": flight["source"],
        "destination": flight["destination"],
        "travel_date": flight["travel_date"],
        "departure_time": flight["departure_time"],
        "arrival_time": flight["arrival_time"],
        "seat_class": seat_class,
        "selected_seats": st.session_state.selected_seats.copy(),
        "total_amount": st.session_state.total_amount,
        "num_passengers": num_passengers  

    }
 # Save passenger count for back navigation
    # st.session_state.num_passengers = num_passengers

    st.success("Seats selected. Redirecting to payment...")
    st.switch_page("pages/passenger_details.py")




    
