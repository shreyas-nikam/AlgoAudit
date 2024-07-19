# Import the libraries
import json
import base64
import streamlit as st
from supabase import Client, create_client


@st.cache_data()
def decode_data(encoded_data: str):
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
        return data
    except Exception as e:
        return None

### ############################################################ ###
### ######################## Streamlit UI ###################### ###
### ############################################################ ###


st.set_page_config(page_title="AlgoAudit", layout="wide", page_icon="🏬")

st.title("AlgoAudit")

if 'supabaseDB' not in st.session_state:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    st.session_state.supabase_skillbridge_table = st.secrets["SUPABASE_SKILLBRIDGE_TABLE"]
    supabase: Client = create_client(url, key)
    st.session_state.supabaseDB = supabase

if "user_info" not in st.session_state:
    # st.session_state.user_info = {"email":"uddhav@qusandbox.com", "name":"Uddhav", "s3_dir":"uddhav@qusandbox.com", }
    st.session_state.user_info = {}
    st.switch_page("pages/login.py")

if "allowed_config" not in st.session_state:
    st.session_state.allowed_config = None


if not st.session_state.user_info:
    st.switch_page("pages/login.py")
else:
    if st.session_state.user_info["examine_access_key"]:
        st.session_state.allowed_config = decode_data(
            st.session_state.user_info["examine_access_key"])
    st.switch_page("pages/examine.py")
