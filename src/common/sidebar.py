import streamlit as st

from src.common.logger import Logger
logger = Logger.get_logger()




def sidebar(disabled_button):
    if "user_info" not in st.session_state:
        st.session_state.user_info = {}
        st.switch_page("pages/login.py")

    st.sidebar.image("https://www.quantuniversity.com/assets/img/logo5.jpg", use_column_width="always")
    st.sidebar.divider()
    