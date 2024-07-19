# Import libraries
import streamlit as st
from src.common.logger import Logger

# Create the logger object
logger = Logger.get_logger()

class Home:
    """
    Function to display the home page of the Streamlit app.
    """    

    def main(self):
        """
        Function to display the home page of the Streamlit app.
        """
        logger.info("Logged in to Home Page")
        st.header(st.session_state.config_param["APP_NAME"], divider= "blue")
        st.markdown(st.session_state.config_param["HOME_PAGE_INTRODUCTION"], unsafe_allow_html=True)
        st.divider()
        st.caption("© 2024 [QuantUniversity](https://www.quantuniversity.com/). All Rights Reserved.")
        st.caption(f"The purpose of this demonstration is solely for educational use and illustration. Any reproduction of this demonstration requires prior written consent from QuantUniversity.")
