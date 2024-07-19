import re
import json
import base64
import streamlit as st
from supabase import Client, create_client
from pathlib import Path
from src.common.logger import Logger
logger = Logger.get_logger()

st.set_page_config(page_title="AlgoAudit", layout="wide", page_icon="🏬")

access_key_mapping = json.load(open(Path("./data/access_key_mapping.json"), "r"))

def decode_data(encoded_data):
    """
    This function is used to decode the data from the access key.

    Args:
    encoded_data (str): The encoded data from the access key.

    Returns:
    bool: The boolean value indicating the success of the decoding process.
    """
    try:
        # Double decoding
        decoded_data = base64.b64decode(encoded_data)
        decoded_data = base64.b64decode(decoded_data)

        # convert the data back to json
        decoded_data = decoded_data.decode("utf-8")

        # convert the json data back to a dictionary
        data = json.loads(decoded_data)

        if "courses" not in data or "allowed_pages" not in data:
            raise Exception("Invalid Key")

        if "allowed_config" not in st.session_state:
            st.session_state.allowed_config = data
        return True
    except Exception as e:
        return False


def validate_email(email):
    """
    This function is used to validate the email address.

    Args:
    email (str): The email address to be validated.

    Returns:
    bool: The boolean value indicating the validity of the email address.
    """
    # Regular expression for basic email validation
    pattern = r'^(?!\.)[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    else:
        return False


def validate_name(name):
    """
    This function is used to validate the name.

    Args:
    name (str): The name to be validated.

    Returns:
    bool: The boolean value indicating the validity of the name.
    """
    # Regular expression for name validation (alphabetic characters only)
    pattern = r'^[a-zA-Z ]+$'
    if re.match(pattern, name):
        return True
    else:
        return False


def validate_password(password):
    """
    This function is used to validate the name.

    Args:
    name (str): The name to be validated.

    Returns:
    bool: The boolean value indicating the validity of the name.
    """
    # Regular expression for name validation (alphabetic characters only)

    if len(password) > 8:
        return True
    else:
        return False


def validate_linkedIn_profile(linkedin_profile):
    """
    This function is used to validate the linkedIn profile.

    Args:
    linkedin_profile (str): The linkedIn profile to be validated.

    Returns:
    bool: The boolean value indicating the validity of the linkedIn profile.
    """
    # Regular expression for linkedIn profile validation
    pattern = r'(?:https:\/\/www\.)?linkedin\.com\/in\/[a-zA-Z0-9-]+'
    return re.match(pattern, linkedin_profile)

def get_linkedIn_profile_id(linkedin_profile):
    """
    This function is used to extract the linkedIn profile id from the linkedIn profile link.
    
    Args:
    linkedin_profile (str): The linkedIn profile link.
    
    Returns:
    str: The linkedIn profile id.

    """
    pattern = r"(?:https:\/\/www\.)?linkedin\.com\/in\/([a-zA-Z0-9-]+)"
    match = re.search(pattern, linkedin_profile)
    if match:
        return match.group(1)  # Returns the captured group, which is the username
    else:
        return ""


def encode_password(password):
    # Encoding the string
    bytes_password = base64.b64encode(password.encode("utf-8"))
    string_password = bytes_password.decode('utf-8')
    return string_password


if 'supabaseDB' not in st.session_state:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    st.session_state.supabase_skillbridge_table = st.secrets["SUPABASE_SKILLBRIDGE_TABLE"]
    st.session_state.supabaseDB = create_client(url, key)

if "user_info" not in st.session_state:
    st.session_state.user_info = {}

st.markdown(f"<h1 style='text-align: center;'>AlgoAudit: Register</h1>",
            unsafe_allow_html=True)
_, central_col, _ = st.columns([.2, .6, .2])

with central_col:
    # Display the sign in form
    st.markdown("<p style='text-align: center;'>Enter the following information to proceed</p>",
                unsafe_allow_html=True)

    name = st.text_input(
        "Name:", placeholder="Enter your name")
    email = st.text_input(
        "Email ID:", placeholder="Enter email address")
    password = st.text_input(
        "Password:", placeholder="Enter password", type="password")
    agree = st.checkbox(
        f"""I read and agree to QuantUniversity's [Privacy Policy](https://www.quantuniversity.com/privacy.html) and Terms & Conditions*""")

    st.write(' ')
    _, central_col1, central_col2, _ = central_col.columns(
        [.15, .30, .30, .15])
    if central_col2.button("Sign In", use_container_width=True):
        st.switch_page("pages/login.py")

    if central_col1.button('Proceed', use_container_width=True, type="primary"):
        # Perform validations
        if not name:
            st.error("Please enter your name.")
            logger.warning("Name not entered.")
        if not email:
            st.error("Please enter your email.")
            logger.warning("Email not entered.")
        elif not validate_email(email):
            st.error("Invalid email format. Please enter a valid email address.")
            logger.warning("Invalid Email.")
        elif not password:
            st.error("Please enter your password.")
            logger.warning("Password not entered.")
        elif not validate_password(password):
            st.error("Please enter a valid password (length greater than 8).")
            logger.warning("Invalid password.")
        elif not agree:
            st.error(
                "Please read and agree the QuantUniversity's [Privacy Policy](https://www.quantuniversity.com/privacy.html).")
            logger.warning("Privacy Policy not agreed.")
        else:
            logger.info("Registration Successful.")
            password = encode_password(password)
            user_data = {
                'name': name,
                'email': email.lower(),
                'password': password,
            }

            logger.info(f"user_data: \n {user_data}")
            try:
                data, count = st.session_state.supabaseDB.table(
                    st.session_state.supabase_skillbridge_table).insert(user_data).execute()
                st.session_state.user_info = data[1][0]
            except Exception as e:
                logger.error(f"Error: {e}")
                st.error("Email already in use. Please register with a different email.")
                st.stop()
            st.switch_page("Home.py")

st.write("\n\n")
st.divider()
st.caption("*This demo and application are for educational purposes only and are provided as illustrations. The interpretations of the law are prepared by QuantUniversity to offer our understanding of the law. However, this information should not be considered legal advice. Users are advised to consult with a qualified attorney for legal interpretation tailored to their organization's situation. QuantUniversity bears no liability for any consequences resulting from the interpretation or implementation.")
