from email.mime.base import MIMEBase
import streamlit as st
from database import get_connection
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email import encoders

st.markdown("""
<style>
/* Hide sidebar nav already exists in your code */
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Booking Confirmation", page_icon="🎫", layout="centered")


st.markdown("""
<style>
.main {
    background-color: #f4f6f9;
}

.booking-card {
    background: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

.success-banner {
    background: linear-gradient(90deg, #28a745, #20c997);
    padding: 15px;
    border-radius: 10px;
    color: white;
    text-align: center;
    font-size: 20px;
    font-weight: bold;
}

.highlight {
    font-size: 18px;
    font-weight: 600;
    color: #007bff;
}

.amount-box {
    background: #fff3cd;
    padding: 12px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 18px;
    color: #856404;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ------------------- SESSION PROTECTION -------------------
if "last_booking_id" not in st.session_state:
    st.warning(" No booking found. Please complete a payment first.")
    st.stop()

booking_id = st.session_state["last_booking_id"] 

# ------------------- FETCH BOOKING DETAILS -------------------
try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
        b.booking_id,
        b.user_email,
        b.price,
        b.travel_date,
        b.status,
        f.airline,
        f.flight_number,
        f.source,
        f.destination,
        f.departure_time,
        f.arrival_time,
        s.seat_number,
        s.class_name
    FROM bookings b
    JOIN flights f ON b.flight_id = f.flight_id
    JOIN seats s ON b.seat_id = s.seat_id
    WHERE b.booking_id = ?
    """, (booking_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        st.error(" Booking not found! Please check your booking ID.")
        st.stop()

except Exception as e:
    st.error(f"Failed to fetch booking details: {e}")
    st.stop()


# ------------------- DISPLAY BOOKING SUMMARY -------------------
first_row = rows[0]

seat_class = first_row[12]
seats = [row[11] for row in rows]
total_amount = sum([row[2] for row in rows])

# ---- NOW DESIGN UI ----
st.markdown('<div class="success-banner">🎉 Booking Confirmed Successfully!</div>', unsafe_allow_html=True)
st.balloons()

st.markdown(f"""
<div class="booking-card">
    <p class="highlight">🆔 Booking ID: {booking_id}</p>
    <hr>
    <p><b>✈ Airline:</b> {first_row[5]} {first_row[6]}</p>
    <p><b>📍 Route:</b> {first_row[7]} → {first_row[8]}</p>
    <p><b>📅 Travel Date:</b> {first_row[3]}</p>
    <p><b>🕒 Departure:</b> {first_row[9]}</p>
    <p><b>🕓 Arrival:</b> {first_row[10]}</p>
    <p><b>💺 Seat Class:</b> {seat_class}</p>
    <p><b>🪑 Seats:</b> {', '.join(seats)}</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="amount-box">
     Total Amount Paid: ₹{total_amount}
</div>
""", unsafe_allow_html=True)

# st.markdown(f"📧 Confirmation sent to: **{first_row[1]}**")



# ------------------- GENERATE BOOKING TXT -------------------
def generate_booking_text(rows):
    try:
        first_row = rows[0]
        seat_class = first_row[12]
        seats = [row[11] for row in rows]
        total_amount = sum([row[2] for row in rows])

        text = f"""
=========================================
        FLIGHT BOOKING SUMMARY
=========================================

Booking ID: {first_row[0]}

Airline: {first_row[5]} {first_row[6]}

Route: {first_row[7]} → {first_row[8]}

Travel Date: {first_row[3]}

Departure Time: {first_row[9]}

Arrival Time: {first_row[10]}

Seat Class: {seat_class}

Seats Booked: {', '.join(seats)}

Booking Status: {first_row[4]}

Total Amount Paid: ₹{total_amount}

=========================================
Thank you for choosing our airline!
Have a safe journey ✈
=========================================
"""
        return text
    except Exception as e:
        st.error(f"Error generating booking text: {e}")
        return None

booking_text = generate_booking_text(rows)

# ------------------- EMAIL FUNCTION -------------------
def send_booking_email(to_email):

    from_email = st.secrets["EMAIL"]
    password = st.secrets["APP_PASSWORD"]

    html_content = f"""
    <html>
    <body style="font-family:Arial;background:#f4f6f9;padding:20px;">

    <div style="
        background:white;
        padding:25px;
        border-radius:15px;
        box-shadow:0px 4px 10px rgba(0,0,0,0.1);
    ">

        <h2 style="color:#28a745;">
            🎉 Booking Confirmed Successfully!
        </h2>

        <hr>

        <p><b>🆔 Booking ID:</b> {booking_id}</p>

        <p><b>✈ Airline:</b>
        {first_row[5]} {first_row[6]}</p>

        <p><b>📍 Route:</b>
        {first_row[7]} → {first_row[8]}</p>

        <p><b>📅 Travel Date:</b>
        {first_row[3]}</p>

        <p><b>🕒 Departure:</b>
        {first_row[9]}</p>

        <p><b>🕓 Arrival:</b>
        {first_row[10]}</p>

        <p><b>💺 Seat Class:</b>
        {seat_class}</p>

        <p><b>🪑 Seats:</b>
        {', '.join(seats)}</p>

        <hr>

        <h3 style="color:#856404;">
            Total Amount Paid: ₹{total_amount}
        </h3>

        <p>
            Thank you for choosing our airline.
            Have a safe journey! ✈
        </p>

    </div>

    </body>
    </html>
    """

    try:

        message = MIMEMultipart()

        message["From"] = from_email
        message["To"] = to_email
        message["Subject"] = "✈ Your Flight Booking Confirmation"

        message.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.send_message(message)

        return True

    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

user_email = first_row[1]

if not st.session_state.get(f"email_sent_{booking_id}"):

    if send_booking_email(user_email):

        st.session_state[f"email_sent_{booking_id}"] = True

        st.toast("📧 Your ticket has been sent to your email successfully!")

if not booking_text:
    st.warning("Booking summary not available. Cannot download or send email.")
    download_button_disabled = True
else:
    download_button_disabled = False

# # ------------------- EMAIL BUTTON -------------------
# if st.button("📧 Send Booking Summary via Email", disabled=email_button_disabled):
#     if send_booking_email(user_email, booking_text):
#         st.success(f"Booking summary sent to {user_email} successfully!")

# ------------------- DOWNLOAD BUTTON -------------------

st.download_button(
    label="📥 Download Booking Summary",
    data=booking_text,
    file_name=f"Booking_{booking_id}.txt",
    disabled=download_button_disabled
)

st.divider()

if st.button("🏠 Back to Home"):
     # Clear previous booking data
    st.session_state.selected_seats = []
    st.session_state.num_passengers = 1
    
    if "last_booking_id" in st.session_state:
        del st.session_state["last_booking_id"]
    st.switch_page("app.py")

