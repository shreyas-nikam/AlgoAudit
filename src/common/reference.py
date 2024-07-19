# Import the required libraries
import streamlit as st
from src.common.logger import Logger

# Create the logger object
logger = Logger.get_logger()

class Reference:
    """
    This class is used to display the reference PDF in the Streamlit app.
    """
    def main(self):
        """
        The main function to display the reference PDF.
        """
        logger.info("Logged in to Reference PDF")
        st.header("Reference PDF", divider="blue")
        st.write(f"You can refer the original PDF Document [here]({st.session_state.config_param['DOCUMENT_LINK']}).")