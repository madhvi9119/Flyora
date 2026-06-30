import streamlit as st
import re
import dns.resolver

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Passenger Details", page_icon="✈️", layout="centered")

st.markdown("""
<style>
/* Hide sidebar nav already exists in your code */
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)
with st.sidebar:
    if st.button("Booking"):
        st.switch_page("pages/booking.py")
# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>

/* Hide sidebar navigation */
[data-testid="stSidebarNav"] {display: none;}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, #e3f2fd, #ffffff);
}

.stTextInput {
    margin-top: -11px;
    margin-bottom: 7px ;
}

/* Card container */
.passenger-card {
    background-color: #ffffff;
    padding: 18px ;
    border-radius: 10px;
    box-shadow: 0px 4px 14px rgba(0,0,0,0.06);
    max-width: 380px;
    margin:  auto;
    transition: 0.3s ease-in-out;
}


.passenger-card:hover {
    box-shadow: 0px 12px 35px rgba(0,0,0,0.15);
    transform: translateY(-3px);
}

/* Title */
.passenger-title {
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    color: #003366;
    margin-bottom: 25px;
}

/* Input field focus effect */
.stTextInput>div>div>input {
    border-radius: 8px;
    border: 2px solid #ddd;
    padding: 10px;
    transition: 0.3s;
}

.stTextInput>div>div>input:focus {
    border-color: #007BFF;
    box-shadow: 0px 0px 8px rgba(0,123,255,0.4);
}

/* Button Styling */
.stButton>button {
    width: 100%;
    background-color: #003366;
    color: white;
    border-radius: 8px;
    padding: 10px;
    font-weight: bold;
    transition: 0.3s;
}

.stButton>button:hover {
    background-color: #0055aa;
    transform: scale(1.03);
}

# .back-button button {
#     background-color: #f0f2f6;
#     color: #003366;
#     border-radius: 8px;
#     font-weight: bold;
#     transition: 0.3s;
# }

# .back-button button:hover {
#     background-color: #003366;
#     color: white;
#     transform: scale(1.05);
# }
          
</style>
""", unsafe_allow_html=True)

if "passenger_validated" not in st.session_state:
    st.session_state.passenger_validated = False


# ---------------- VALIDATION FUNCTIONS ----------------

def validate_username(uname):
    pattern = r"^[A-Za-z ]+$"
    return re.match(pattern, uname)

def validate_email_format(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email)

def validate_email_domain(email):
    domain = email.split("@")[1]
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return True
    except:
        return False

# ---------------- PASSENGER CARD ----------------

with st.container():

    st.markdown("""
    <div class="passenger-card">
        <div class="passenger-title">Passenger Details</div>
    """, unsafe_allow_html=True)



    # Required label
    st.markdown("Full Name <span style='color:red;'>*</span>", unsafe_allow_html=True)
    uname = st.text_input("Full Name", key="username", value=st.session_state.get("passenger_name", ""), label_visibility="collapsed")

    st.markdown("Email Address <span style='color:red;'>*</span>", unsafe_allow_html=True)
    email = st.text_input("Email Address", key="email", value=st.session_state.get("passenger_email", ""), label_visibility="collapsed")

    proceed_clicked = st.button("Proceed to Payment")

    if proceed_clicked:

        errors = []

        # Username Validation
        if not uname:
            errors.append("Full Name is required")
        elif not validate_username(uname):
            errors.append("Full Name should contain only letters and spaces")

        # Email Validation
        if not email:
            errors.append("Email is required")
        elif not validate_email_format(email):
            errors.append("Invalid email format")
        elif not validate_email_domain(email):
            errors.append("Email domain does not exist (No MX record found)")

        if errors:
            for error in errors:
                st.error(error)
            st.session_state.passenger_validated = False  # <-- add this

        else:
            st.session_state.passenger_name = uname
            st.session_state.passenger_email = email
            st.session_state.passenger_validated = True   # <-- add this
            
            st.success("Passenger details validated successfully ✅")
            # 🔥 Directly Go To Payment Page
            st.switch_page("pages/payment.py")