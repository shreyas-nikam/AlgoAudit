# Import the libraries
from pathlib import Path
import json
from PIL import Image
import base64
from io import BytesIO
import streamlit as st
from supabase import Client, create_client
from src.common.sidebar import sidebar

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



# HTML to set the background image and position circles over it
html = f"""
<style>
    .circle {{
        width: 250px;
        height: 250px;
        border-radius: 50%;
        position: absolute;
        transition: transform 0.5s ease; 
        background: linear-gradient(45deg, #d9f8ff 0%, #fff 100%);
        
    }}
    #circle1 {{ width: 350px; height: 350px; top: 0px; left: 0px; bakcground: linear-gradient(45deg, #d9f8ff 0%, #fff 100%); }}
    #circle2 {{ top: 350px; left: 400px; background: linear-gradient(135deg, #efd9ff 0%, #fff 100%); }}
    #circle3 {{ width: 400px; height: 400px; top: 80px; left: 80%; background: linear-gradient(90deg, #dad9ff 0%, #fff 100%); }}
</style>
<div class="circle" id="circle1"></div>
<div class="circle" id="circle2"></div>
<div class="circle" id="circle3"></div>
"""

# Inject HTML into Streamlit
st.markdown(html, unsafe_allow_html=True)


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
        st.session_state.allowed_config = decode_data(st.session_state.user_info["examine_access_key"])
    
    st.header("AlgoAudit.AI", divider = 'blue')
    col1, col2 = st.columns([1, 1])

    sidebar(disabled_button="")

    with col1:
        
        st.subheader("Learn, Prepare, and Validate your AI Systems")
        st.write("AlgoAudit.AI is a platform that helps you learn, prepare, and validate your AI systems. It provides a suite of tools to help you understand the data, train models, and validate the models.")

    with col2:
        st.image(Path("assets/images/home_page_image_1.png").as_posix())
    
    if st.session_state.allowed_config:
        if "courses" in st.session_state.allowed_config:
            col1.subheader("Courses")
            course = col1.selectbox("Select a course", ["Select"]+list(st.session_state.allowed_config["courses"]))
            if course!="Select":
                st.session_state.active_application = course
                st.switch_page("pages/examine.py")

    st.divider()
    st.caption("© 2021 AlgoAudit.AI. All rights reserved.")



    # st.switch_page("pages/examine.py")
