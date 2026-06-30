import streamlit as st
import re
from database import get_connection
from werkzeug.security import generate_password_hash, check_password_hash 


st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)
# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Login",
    page_icon="✈️",
    layout="centered")

with st.sidebar:
    st.title("Navigation")
    if st.button("Continue without login"):
        # Clear any previous redirect just in case
        if "redirect_page" in st.session_state:
            del st.session_state.redirect_page
        st.switch_page("app.py")  # go to home / main page


# ---------------- SESSION STATE ----------------
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"  # 'login' or 'create_account'
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None

st.title("User Authentication")

# ---------------- LOGGED-IN VIEW ----------------
if st.session_state.user_id is not None:
    if "redirect_page" in st.session_state:
        page = st.session_state.redirect_page
        del st.session_state.redirect_page
        st.switch_page(page)
        st.stop()

    else:
        st.switch_page("app.py")
        st.stop()

# ---------------- LOGIN MODE ----------------
elif st.session_state.auth_mode == "login":
    st.subheader("Login")
    
    # ---------------- SHOW CREATE ACCOUNT MESSAGE IF EXISTS ----------------
    if "account_created_message" in st.session_state:
        st.success(st.session_state.account_created_message)
        del st.session_state.account_created_message  # remove after showing once

    username = st.text_input("Username", key="login_login_user")
    password = st.text_input("Password", type="password", key="login_login_pass")


    if st.button("Login"):
        # ---------------- VALIDATION ----------------
        if not username.strip() or not password.strip():
            st.error("⚠️ Both username and password are required.")
        else:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, password FROM users WHERE username=?",(username.strip(),))
            user = cursor.fetchone()
            conn.close()

            if user:
                # ← CHANGED: Now we check the hashed password
                user_id, db_username, password_hash = user
                if check_password_hash(password_hash, password):  # ← USE THIS LINE
                    st.session_state.user_id = user_id
                    st.session_state.username = db_username
                    st.session_state.login_success_message = f"Welcome {db_username}!"
                    st.session_state.auth_mode = "login"

                    # Redirect to the page user was trying to access or home
                    if "redirect_page" in st.session_state:
                        page = st.session_state.redirect_page
                        del st.session_state.redirect_page
                        st.switch_page(page)
                    else:
                        st.switch_page("app.py")
                else:
                    st.error("Invalid username or password. Please try again.")
            else:
                st.error("Invalid username or password. Please try again.")

    st.write("Don't have an account?")
    if st.button("Create New Account"):
        st.session_state.auth_mode = "create_account"
        st.rerun()

# ---------------- CREATE ACCOUNT MODE ----------------
elif st.session_state.auth_mode == "create_account":
    st.subheader("Create New Account")
    new_username = st.text_input("New Username", key="create_user")
    st.caption("Username: letters, numbers, underscore, no spaces")

    new_password = st.text_input("New Password", type="password", key="create_pass")

    if st.button("Create Account"):

        new_username = new_username.strip()
        new_password = new_password.strip()

        # ---------------- VALIDATION ----------------
        username_pattern = r'^[A-Za-z][A-Za-z0-9_]*$'  # starts with letter, letters/numbers/_
        
        if not new_username.strip() or not new_password.strip():
            st.error("⚠️ Both username and password are required.")
        elif not re.match(username_pattern, new_username):
            st.error("⚠️ Username must start with a letter and contain only letters, digits, or underscore (_).")
        elif len(new_password) < 6:
            st.error("⚠️ Password must be at least 6 characters long.")
        else:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE username=?", (new_username,))

            if cursor.fetchone():
                st.error("❌ Username already exists.")
            else:
                # ← CHANGED: Hash the password before storing
                password_hash = generate_password_hash(new_password)  # ← ADD THIS LINE
                cursor.execute("INSERT INTO users (username, password) VALUES (?,?)",
                               (new_username, password_hash))  # ← Store hash, not plain text
                conn.commit()
                st.session_state.account_created_message = f"✅ Account '{new_username}' created! You can now login."
               
                st.session_state.auth_mode = "login"
                st.rerun()
            conn.close()

    if st.button("Back to Login"):
        st.session_state.auth_mode = "login"
        st.rerun()