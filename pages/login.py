# Import the required libraries
import re
import streamlit as st

import uuid
import base64
import json
from supabase import create_client, Client

from src.common.logger import Logger
logger = Logger.get_logger()

st.set_page_config(page_title="AlgoAudit", layout="wide", page_icon="🏬")

# Create Supabase client
if 'supabaseDB' not in st.session_state:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    st.session_state.supabase_skillbridge_table = st.secrets["SUPABASE_SKILLBRIDGE_TABLE"]
    st.session_state.supabaseDB = create_client(url, key)

# Create a session state to store user information
if "user_info" not in st.session_state:
    st.session_state.user_info = {}


def validate_credentials(email, password):
    try : 
        data, count = st.session_state.supabaseDB.table(st.session_state.supabase_skillbridge_table).select('*').eq('email', email).execute()

        if data[1]:
            user_profile = data[1][0]
            string_password = user_profile['password']
            encoded_password = string_password.encode('utf-8')
            db_password = base64.b64decode(encoded_password).decode("utf-8")
            if password == str(db_password).lower():
                st.session_state.user_info = user_profile
                return True
            else:
                logger.error("Wrong Password")
                return False
        else:
            logger.error("Wrong Email")
            return False
    except Exception as e:
        logger.error(f"Login error : {e} ")
        return False


st.markdown(f"<h1 style='text-align: center;'>AlgoAudit: Login</h1>", unsafe_allow_html=True)
_, central_col, _ = st.columns([.2, .6, .2])

with central_col:
    
    email = st.text_input("Email ID:", placeholder="Enter email address")
    password = st.text_input("Password:", placeholder="Enter password", type="password")
    
    st.write(' ')
    _, central_col1, central_col2, _ = central_col.columns(
        [.15, .30, .30, .15])
    if central_col1.button('Proceed', use_container_width=True, type="primary"):
        logger.info(f"Login Attempted: Email: {email}")
        # Perform validations
        if not validate_credentials(email.lower(), str(password).lower()):
            st.error("Wrong email or password entered.")
            logger.warning("Wrong email or password entered.")
        else:
            logger.info("Login Successful.")
            st.switch_page("Home.py")

    if central_col2.button('Register', use_container_width=True):
        st.switch_page("pages/register.py")

st.write("\n\n")
st.divider()
st.caption("*This demo and application are for educational purposes only and are provided as illustrations. The interpretations of the law are prepared by QuantUniversity to offer our understanding of the law. However, this information should not be considered legal advice. Users are advised to consult with a qualified attorney for legal interpretation tailored to their organization's situation. QuantUniversity bears no liability for any consequences resulting from the interpretation or implementation.")
