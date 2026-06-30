import streamlit as st
import re
from database import get_connection
from datetime import date
import time
import uuid

st.set_page_config(page_title="Payment", page_icon="💳", layout="centered")

st.markdown("""
<style>
/* Hide sidebar nav already exists in your code */
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    if st.button("Back to Passenger Details"):
        st.switch_page("pages/passenger_details.py")

with st.sidebar:
    if st.button("Go to Confirmation"):
        st.switch_page("pages/confirmation.py")

# ------------------- SESSION PROTECTION -------------------
if "user_id" not in st.session_state:
    st.warning("Please login first.")
    if st.button("Go to Login"):
        st.switch_page("pages/login.py")
    st.stop()

if "booking_info" not in st.session_state:
    st.warning("No booking info found. Please select seats first.")
    if st.button("Go to Booking"):
        st.switch_page("pages/booking.py")
    st.stop()

if "passenger_name" not in st.session_state:
    st.warning("Passenger details missing. Please fill details first.")
    if st.button("Go to Passenger Details"):
        st.switch_page("pages/passenger_detail.py")
    st.stop()
    

# ------------------- SAFE BOOKING ID GENERATION -------------------

def generate_unique_booking_id():
    conn = get_connection()
    cursor = conn.cursor()
    while True:
        new_id = "BKG-" + str(uuid.uuid4())[:8].upper()
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_id=?", (new_id,))
        if cursor.fetchone()[0] == 0:
            conn.close()
            return new_id

# Only generate once per transaction
if "current_booking_id" not in st.session_state:
    st.session_state["current_booking_id"] = generate_unique_booking_id()

booking_id = st.session_state["current_booking_id"]


# ------------------- PAYMENT STATUS HELPERS -------------------
def check_payment_done(booking_id):
    """Check in DB if payment is already done for this booking_id"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_id=? AND payment_done=1", (booking_id,))
    done = cursor.fetchone()[0] > 0
    conn.close()
    return done

def mark_payment_done(booking_id):
    """Mark the booking_id as paid in the database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET payment_done=1 WHERE booking_id=?", (booking_id,))
    conn.commit()
    conn.close()


def is_already_booked(flight_id, seats):
    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(seats))

    query = f"""
        SELECT COUNT(*) FROM seats
        WHERE flight_id = ?
        AND seat_number IN ({placeholders})
        AND is_booked = 1
    """

    cursor.execute(query, [flight_id] + seats)
    count = cursor.fetchone()[0]

    conn.close()

    return count > 0


booking_info = st.session_state["booking_info"]

# 🔒 Prevent Duplicate Booking
if is_already_booked(
        booking_info["flight_id"],
        booking_info["selected_seats"]
    ):
    
    st.error("⚠️ These seats are already booked. Payment page disabled.")
    st.stop()

total_amount = booking_info.get("total_amount", 0)


# ------------------- BOOKING SUMMARY -------------------

st.subheader("Booking Summary")

st.write(f"**Passenger:** {st.session_state.get('passenger_name')}")
st.write(f"**Email:** {st.session_state.get('passenger_email')}")

st.write(f"**Flight:** {booking_info.get('airline')} {booking_info.get('flight_number')}")
st.write(f"**Route:** {booking_info.get('source')} → {booking_info.get('destination')}")
st.write(f"**Date:** {booking_info.get('travel_date')}")
st.write(f"**Departure:** {booking_info.get('departure_time')}")
st.write(f"**Arrival:** {booking_info.get('arrival_time')}")
st.write(f"**Seat Class:** {booking_info.get('seat_class')}")
st.write(f"**Seats:** {', '.join(booking_info.get('selected_seats', []))}")
st.info(f"**Total Amount to Pay:** ₹{total_amount}")

# ------------------- SHOW BOOKING ID AND PAYMENT STATUS -------------------
st.info(f"Booking ID: {booking_id} — Payment status: {'Paid' if check_payment_done(booking_id) else 'Pending'}")

# ------------------- PAYMENT CLASSES -------------------
class Payment:
    def __init__(self, amount):
        self.amount = amount
        self.success = False

    def validate(self):
        return True

    def process_payment(self):
        self.success = True
        return self.success


class CardPayment(Payment):
    def __init__(self, amount, card_number, expiry, cvv):
        super().__init__(amount)
        self.card_number = card_number
        self.expiry = expiry
        self.cvv = cvv

    def validate(self):
        if not re.fullmatch(r"\d{16}", self.card_number):
            st.error("Card number must be 16 digits")
            return False
        if not re.fullmatch(r"\d{2}/\d{4}", self.expiry):
            st.error("Expiry must be MM/YYYY")
            return False
        if not re.fullmatch(r"\d{3}", self.cvv):
            st.error("CVV must be 3 digits")
            return False
        return True


class UPIPayment(Payment):
    def __init__(self, amount, upi_id):
        super().__init__(amount)
        self.upi_id = upi_id

    def validate(self):
        pattern = r"^[a-zA-Z0-9._\-]{2,25}@[a-zA-Z]{2,10}$"
        if not re.fullmatch(pattern, self.upi_id):
            st.error("Invalid UPI ID. Format: username@bank")
            return False
        return True


class NetBankingPayment(Payment):
    def __init__(self, amount, bank_name):
        super().__init__(amount)
        self.bank_name = bank_name

    def validate(self):
        if not self.bank_name:
            st.error("Please select a bank")
            return False
        return True


# ------------------- BOOKING MANAGER -------------------
class BookingManager:
    def __init__(self, user_id, booking_info,booking_id):
        self.user_id = user_id
        self.booking_info = booking_info
        self.booking_id = booking_id
        self.conn = get_connection()

    def book_seats(self):
        cursor = self.conn.cursor()
        try:
            flight_id = self.booking_info["flight_id"]
            email = st.session_state.get("passenger_email")
            travel_date = self.booking_info["travel_date"]
            seat_class = self.booking_info["seat_class"]
            seats = self.booking_info["selected_seats"]
            if not seats:
                raise Exception("No seats selected.")
            price_per_seat = self.booking_info["total_amount"] // len(seats)

            # 🔒 STEP 1: Check ALL seats first
            placeholders = ",".join(["?"] * len(seats))
            query = f"""
            SELECT seat_number FROM seats
            WHERE flight_id=? 
            AND seat_number IN ({placeholders})
            AND is_booked=1
        """
            cursor.execute(query, [flight_id] + seats)
        
            already_booked = cursor.fetchall()
        
            if already_booked:
                booked_list = [row[0] for row in already_booked]
                raise Exception(f"Seats already booked: {', '.join(booked_list)}")
        
# ✅ STEP 2: Mark seats as booked and create booking records    
            for seat in seats:
                # Mark existing seat as booked
                cursor.execute("""
                    UPDATE seats
                    SET is_booked = 1
                    WHERE flight_id = ?
                    AND seat_number = ?
                    AND class_name = ?
                """, (flight_id, seat, seat_class))


                # Get seat_id of that seat
                cursor.execute("""
                    SELECT seat_id
                    FROM seats
                    WHERE flight_id = ?
                    AND seat_number = ?
                    AND class_name = ?
                """, (flight_id, seat, seat_class))

                seat_id = cursor.fetchone()[0]

                # INSERT booking record
                cursor.execute("""
                    INSERT INTO bookings(booking_id, user_id, flight_id, seat_id, travel_date, user_email, price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.booking_id,
                    self.user_id,
                    flight_id,
                    seat_id,
                    travel_date,
                    email,
                    price_per_seat
                ))

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            self.conn.close()


# ------------------- PAYMENT SELECTION -------------------
method = st.radio(
    "Select Payment Method",
    ["💳 Card", "📱 UPI", "🏦 Net Banking"],
    horizontal=True , index=None
)

# ------------------- PREVENT DUPLICATE PAYMENT -------------------

booking_id = st.session_state["current_booking_id"]

# ------------------- PREVENT DUPLICATE PAYMENT -------------------
if check_payment_done(booking_id):
    st.success(f" Payment already completed for Booking ID: {booking_id}")
    st.stop()

# Get current booking_id
booking_id = st.session_state["current_booking_id"]

# Disable pay button if payment is already done for this booking
pay_button_disabled = check_payment_done(booking_id)


# ------------------- PAYMENT FORMS -------------------
if method == "💳 Card":

    # Card type selection
    card_type = st.radio(
        "Select Card Type",
        ["Debit Card", "Credit Card"], index=None,
        horizontal=True
    )
    # Show card fields ONLY if selected
    if card_type:

        st.subheader(f"{card_type} Details")
        card_number = st.text_input("Card Number")
        cvv = st.text_input("CVV", type="password")

        today = date.today()
        current_year = today.year
        current_month = today.month

        months = [f"{i:02}" for i in range(1, 13)]
        years = [str(y) for y in range(current_year, current_year + 11)]

        selected_month = st.selectbox("Expiry Month", months, index=current_month - 1)
        selected_year = st.selectbox("Expiry Year", years)

        expiry = f"{selected_month}/{selected_year}"

    # ---------------- EXPIRY VALIDATION ----------------
        if int(selected_year) == current_year and int(selected_month) < current_month:
            st.error(" Cannot select a past month")
            pay_button_disabled = True
        # else:
        #     pay_button_disabled = False

    # ---------------- PAY BUTTON ----------------
        
        
        if st.button("Pay Now", disabled=pay_button_disabled):
            payment = CardPayment(total_amount, card_number, expiry, cvv)
            if not payment.validate():
                st.stop()

            manager = BookingManager(st.session_state["user_id"], booking_info, booking_id)
            try:
                start_time = time.time()
                with st.spinner("Processing payment and booking seats... ⏳"):
                    if not payment.process_payment():
                        raise Exception("Payment failed")
                    manager.book_seats()
                    # Mark payment in DB
                    mark_payment_done(booking_id)
                    elapsed = time.time() - start_time
                    if elapsed < 2: time.sleep(2 - elapsed)
                

                # ---------------- REDIRECT TO CONFIRMATION PAGE ----------------
                # Save booking_id in session to fetch summary there
                # Save for confirmation page
                st.session_state["last_booking_id"] = st.session_state.pop("current_booking_id")                # Clear current booking session for next transaction
                for key in ["booking_info", "passenger_name", "passenger_email"]:
                    if key in st.session_state:
                        del st.session_state[key]

                st.success(f"✅ Payment Successful! Booking ID: {booking_id}")
                st.info("Redirecting to confirmation page...")
                time.sleep(1.5)
                st.switch_page("pages/confirmation.py")
            except Exception as e:
                st.error(f" Payment or Booking Failed: {e}")

elif method == "📱 UPI":

    upi_id = st.text_input("UPI ID")

    if st.button("Pay Now", disabled=pay_button_disabled):

        payment = UPIPayment(total_amount, upi_id)

        if not payment.validate():
            st.stop()

        
    
        manager = BookingManager(st.session_state["user_id"], booking_info, booking_id)

        try:
            start_time = time.time()
            with st.spinner("Processing payment and booking seats... ⏳"):
                if not payment.process_payment():
                    raise Exception("Payment failed")
                
                manager.book_seats()
                # Mark payment in DB

                mark_payment_done(booking_id)

                elapsed = time.time() - start_time
                if elapsed < 2:
                    time.sleep(2 - elapsed)
            
            # Save booking_id for confirmation page
            # Save for confirmation page
            st.session_state["last_booking_id"] = st.session_state.pop("current_booking_id")
            # Clear current booking session
            for key in ["booking_info", "passenger_name", "passenger_email"]:
                if key in st.session_state:
                    del st.session_state[key]

            st.success(f"✅ UPI Payment Successful! Booking ID: {booking_id}")
            st.info("Redirecting to confirmation page...")
            time.sleep(1.5)
            st.switch_page("pages/confirmation.py")
        except Exception as e:
            st.error(f"❌ Payment or Booking Failed: {e}")
        

elif method == "🏦 Net Banking":

    bank_name = st.selectbox("Select Bank", ["HDFC", "SBI", "ICICI"])

    if st.button("Pay Now", disabled=pay_button_disabled):

        payment = NetBankingPayment(total_amount, bank_name)

        if not payment.validate():
            st.stop()
        
        
        # Generate booking_id per transaction
        manager = BookingManager(st.session_state["user_id"], booking_info, booking_id)

        try:
            start_time = time.time()
            with st.spinner("Processing payment and booking seats... ⏳"):
                if not payment.process_payment():
                    raise Exception("Payment failed")
                
                manager.book_seats()
            # Mark payment in DB
                mark_payment_done(booking_id)

                elapsed = time.time() - start_time
                if elapsed < 2:
                    time.sleep(2 - elapsed)
            
            # Save booking_id for confirmation page
# Save for confirmation page
            st.session_state["last_booking_id"] = st.session_state.pop("current_booking_id")            # Clear current booking session
            for key in ["booking_info", "passenger_name", "passenger_email"]:
                if key in st.session_state:
                    del st.session_state[key]

            st.success(f"✅ Net Banking Payment Successful! Booking ID: {booking_id}")
            st.info("Redirecting to confirmation page...")
            time.sleep(1.5)
            st.switch_page("pages/confirmation.py")
        except Exception as e:
            st.error(f"❌ Payment or Booking Failed: {e}")
