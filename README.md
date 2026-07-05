# Flyora
# ✈️ Airline Booking Platform

A multi-page **Airline Ticket Booking System** built using **Python** and **Streamlit**, with **SQLite** as the database. This project covers the complete flow of an airline booking website — from searching flights to seat selection, passenger details, payment, and booking confirmation.

---

## 📌 Features

- 🔐 **User Authentication** — Login and account creation with secure password hashing (Werkzeug)
- 🔍 **Flight Search** — Search flights by source, destination, and travel date
- 💺 **Dynamic Seat Selection** — Interactive seat map with window/aisle/middle seat detection, based on airline-specific aircraft layouts
- 🧑‍💼 **Passenger Details** — Name and email validation (including email domain/MX record check)
- 💳 **Payment Simulation** — Multiple payment modes: Card, UPI, and Net Banking, each with its own validation logic
- 📄 **Booking Confirmation** — Booking summary with downloadable ticket and automated email confirmation
- 📋 **Your Bookings Dashboard** — View Active, Cancelled, and Past bookings, with a 9-hour cancellation policy and cancellation email notifications

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend / UI | Streamlit |
| Database | SQLite |
| Authentication | Werkzeug (password hashing) |
| Email Notifications | smtplib (SMTP) |
| Email Validation | dnspython (MX record lookup) |
| Environment | Python Virtual Environment (venv) |

---

## 📁 Project Structure

```
airline-booking-platform/
│
├── app.py                  # Main entry point — home page with flight search
├── aircraft_config.py       # Stores seat arrangement/layout data for each airline & class
├── database.py               # Creates and manages the SQLite database (users, flights, seats, bookings)
├── requirements.txt          # Project dependencies
│
├── pages/                     # All other application pages
│   ├── login.py               # Login & account creation
│   ├── search_results.py     # Displays flight search results
│   ├── booking.py            # Seat selection page
│   ├── passenger_details.py   # Passenger detail form & validation
│   ├── payment.py            # Payment methods & processing
│   ├── confirmation.py       # Booking confirmation & email/ticket download
│   └── your_bookings.py      # View & manage existing bookings
│
└── venv/                     # Python virtual environment (not tracked in version control)
```

---

## ⚙️ How It Works

1. **`app.py`** is the main file — the user selects source, destination, and travel date to search flights.
2. Search results are handled in the **`pages/search_results.py`** file, which displays available flights.
3. On selecting a flight, **`pages/booking.py`** loads the seat layout from **`aircraft_config.py`** and shows a live seat map based on availability fetched from the database.
4. **`pages/passenger_details.py`** collects and validates passenger information.
5. **`pages/payment.py`** lets the user choose a payment method and simulates the transaction.
6. On successful payment, a booking record is created in the database (via **`database.py`**), and the user is redirected to **`pages/confirmation.py`**, where the ticket is generated and emailed.
7. **`pages/your_bookings.py`** lets users view and cancel their bookings, subject to a cancellation policy.

---

## 🗄️ Database Design (SQLite)

- **users** — stores registered user credentials (hashed passwords)
- **flights** — stores flight details (airline, route, timing, pricing)
- **seats** — stores seat-level data per flight (seat number, class, booking status)
- **bookings** — stores booking transactions (linked to user, flight, and seat)

---

## 🚀 Setup & Installation

```bash
# 1. Clone the repository
git clone <repository-link>
cd airline-booking-platform

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the database tables
python database.py

# 5. Run the application
streamlit run app.py
```

---

## 📧 Email Configuration

The app sends booking confirmation and cancellation emails using Gmail's SMTP server. Add the following to your Streamlit `secrets.toml`:

```toml
EMAIL = "your-email@gmail.com"
APP_PASSWORD = "your-app-password"
```

---

## 📚 Project Info

<!-- - **Developed as:** Semester 3 Academic Project -->
- **Language:** Python
- **Web Framework:** Streamlit
- **Database:** SQLite

---

## 🙌 Future Improvements

- Integration with a real payment gateway
- Admin panel for managing flights and viewing all bookings
- Deployment on cloud (Streamlit Cloud / Render / AWS)
