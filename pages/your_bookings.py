import streamlit as st
from database import get_connection
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Your Bookings", page_icon="📄", layout="centered")

st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

st.title("📄 Your Bookings")


def send_cancellation_email(
    to_email,
    booking_id,
    airline,
    flight_number,
    source,
    destination,
    travel_date,
    departure_time,
    arrival_time,
    seat_class,
    seats,
    total_amount
):

    from_email =  st.secrets["EMAIL"]
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

        <h2 style="color:red;">
            ❌ Booking Cancelled Successfully
        </h2>

        <hr>

        <p><b>Booking ID:</b> {booking_id}</p>

        <p><b>Airline:</b>
        {airline} {flight_number}</p>

        <p><b>Route:</b>
        {source} → {destination}</p>

        <p><b>Travel Date:</b>
        {travel_date}</p>

        <p><b>Departure:</b>
        {departure_time}</p>

        <p><b>Arrival:</b>
        {arrival_time}</p>

        <p><b>Seat Class:</b>
        {seat_class}</p>

        <p><b>Seats:</b>
        {', '.join(seats)}</p>

        <hr>

        <h3>
            Refund Amount: ₹{total_amount}
        </h3>

        <p>
            Your refund will be processed within 5–7 working days.
        </p>

    </div>

    </body>
    </html>
    """

    try:

        message = MIMEMultipart()

        message["From"] = from_email
        message["To"] = to_email
        message["Subject"] = "❌ Flight Booking Cancelled"

        message.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.send_message(message)

    except Exception as e:
        st.error(f"Email failed: {e}")

with st.sidebar:
    if st.button("Home"):
        st.switch_page("app.py")

# ---------------- LOGIN CHECK ----------------
if st.session_state.get("user_id") is None:
    st.warning("⚠️ You must login to view your bookings.")
    st.switch_page("pages/login.py")
    st.stop()

try:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            b.id,
            b.booking_id,
            b.flight_id,
            b.seat_id,
            b.travel_date,
            b.price,
            b.booking_time,
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
        WHERE b.user_id = ?
        ORDER BY b.booking_time DESC
    """, (st.session_state.user_id,))

    bookings = cursor.fetchall()
    conn.close()

    if not bookings:
        st.info("No bookings found.")
        st.stop()

    now_dt = datetime.now()

    grouped = {}

    for b in bookings:

        booking_id = b[1]

        travel_date = datetime.strptime(b[4], "%Y-%m-%d").date()
        departure_time = datetime.strptime(b[12], "%H:%M").time()
        arrival_time = datetime.strptime(b[13], "%H:%M").time()

        departure_datetime = datetime.combine(travel_date, departure_time)
        arrival_datetime = datetime.combine(travel_date, arrival_time)

        if b[7] == "CANCELLED":
            status_type = "CANCELLED"
        elif now_dt >= arrival_datetime:
            status_type = "COMPLETED"
        elif now_dt >= departure_datetime:
            status_type = "COMPLETED"
        else:
            status_type = "ACTIVE"

        if booking_id not in grouped:
            grouped[booking_id] = {
                "rows": [],
                "airline": b[8],
                "flight_number": b[9],
                "source": b[10],
                "destination": b[11],
                "travel_date": b[4],
                "departure_time": b[12],
                "arrival_time": b[13],
            }

        grouped[booking_id]["rows"].append((b, status_type))
    # ---------------- SHOW CANCELLATION TOAST ----------------
    for key in list(st.session_state.keys()):

        if key.startswith("cancel_email_"):

            st.toast(
            "📧 Booking cancelled and confirmation email sent successfully!"
        )

            del st.session_state[key]
    # ---------------- TABS ----------------
    tab1, tab2, tab3 = st.tabs(["🟢 Active", "🔴 Cancelled", "⚫ Past"])

    active_grouped = {}
    cancelled_grouped = {}
    past_grouped = {}

    for booking_id, data in grouped.items():

        rows = data["rows"]

        has_cancelled = any(r[1] == "CANCELLED" for r in rows)
        has_active = any(r[1] == "ACTIVE" for r in rows)

        if has_cancelled and not has_active:
            cancelled_grouped[booking_id] = data
        elif all(r[1] == "COMPLETED" for r in rows):
            past_grouped[booking_id] = data
        else:
            active_grouped[booking_id] = data

    # ======================================================
    # ✈️ ACTIVE TAB
    # ======================================================
    with tab1:
        for booking_id, data in active_grouped.items():

            rows = data["rows"]

            seats = [r[0][14] for r in rows]
            class_name = rows[0][0][15]
            total_amount = sum([r[0][5] for r in rows])

            departure_datetime = datetime.combine(
                datetime.strptime(data['travel_date'], "%Y-%m-%d").date(),
                datetime.strptime(data['departure_time'], "%H:%M").time()
            )

            allow_cancel = (departure_datetime - now_dt).total_seconds() > 9 * 3600

            with st.expander(
                f"✈️ {data['airline']} {data['flight_number']} | 🟢 ACTIVE"
            ):
                st.markdown("### ✈️ Flight Details")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Route**")
                    st.write(f"{data['source']} → {data['destination']}")

                    st.markdown("**Seats**")
                    st.write(", ".join(seats))

                    st.markdown("**Class**")
                    st.write(class_name)

                with col2:
                    st.markdown("**Date**")
                    st.write(data['travel_date'])

                    st.markdown("**Departure**")
                    st.write(data['departure_time'])

                    st.markdown("**Arrival**")
                    st.write(data['arrival_time'])

                    st.markdown("**Total Paid**")
                    st.write(f"₹{total_amount}")

                st.divider()

                if allow_cancel:
                    if st.button("Cancel Booking", key=f"cancel_{booking_id}"):

                        conn = get_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                        UPDATE seats
                        SET is_booked = 0
                        WHERE seat_id IN (
                            SELECT seat_id
                            FROM bookings
                            WHERE booking_id = ?
                        )
                    """, (booking_id,))
                        
                        cursor.execute("""
                            UPDATE bookings
                            SET status = 'CANCELLED'
                            WHERE booking_id = ?
                        """, (booking_id,))

                        conn.commit()
                        cursor.execute("""
                            SELECT user_email
                            FROM bookings
                            WHERE booking_id = ?
                            LIMIT 1
                        """, (booking_id,))

                        user_email = cursor.fetchone()[0]

                        send_cancellation_email(
                            to_email=user_email,
                            booking_id=booking_id,
                            airline=data["airline"],
                            flight_number=data["flight_number"],
                            source=data["source"],
                            destination=data["destination"],
                            travel_date=data["travel_date"],
                            departure_time=data["departure_time"],
                            arrival_time=data["arrival_time"],
                            seat_class=class_name,
                            seats=seats,
                            total_amount=total_amount
)
                        conn.close()

                        st.session_state[f"cancel_email_{booking_id}"] = True
                        st.rerun()

                else:
                    st.button("Cancellation Closed (9-hour rule)", disabled=True)

    # ======================================================
    # 🔴 CANCELLED TAB
    # ======================================================
    with tab2:
        for booking_id, data in cancelled_grouped.items():

            rows = data["rows"]
            seats = [r[0][14] for r in rows]
            class_name = rows[0][0][15]
            total_amount = sum([r[0][5] for r in rows])

            with st.expander(
                f"✈️ {data['airline']} {data['flight_number']} | 🔴 CANCELLED"
            ):

                col1, col2 = st.columns(2)

                with col1:
                    st.write("Route:", f"{data['source']} → {data['destination']}")
                    st.write("Seats:", ", ".join(seats))
                    st.write("Class:", class_name)

                with col2:
                    st.write("Date:", data['travel_date'])
                    st.write("Departure:", data['departure_time'])
                    st.write("Arrival:", data['arrival_time'])
                    st.write(f"₹{total_amount}")

                st.error("Booking Cancelled")

    # ======================================================
    # ⚫ PAST TAB
    # ======================================================
    with tab3:
        for booking_id, data in past_grouped.items():

            rows = data["rows"]
            seats = [r[0][14] for r in rows]
            class_name = rows[0][0][15]
            total_amount = sum([r[0][5] for r in rows])

            with st.expander(
                f"✈️ {data['airline']} {data['flight_number']} | ⚫ COMPLETED"
            ):

                col1, col2 = st.columns(2)

                with col1:
                    st.write("Route:", f"{data['source']} → {data['destination']}")
                    st.write("Seats:", ", ".join(seats))
                    st.write("Class:", class_name)

                with col2:
                    st.write("Date:", data['travel_date'])
                    st.write("Departure:", data['departure_time'])
                    st.write("Arrival:", data['arrival_time'])
                    st.write(f"₹{total_amount}")

                st.info("Flight Completed")

except Exception as e:
    st.error(f"Something went wrong: {e}")


    