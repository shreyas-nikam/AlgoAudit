# import the required libraries
import streamlit as st
import streamlit.components.v1 as components
from src.common.logger import Logger

# Create the logger object
logger = Logger.get_logger()

class ContactForm:
    """
    This class is used to display the contact form in the Streamlit app.
    """
    def main(self):
        """
        The main function to display the contact form.
        """
        logger.info("Logged in to Contact Form")
        # Display the contact form header
        st.header("Contact Form", divider="blue")

        # Display the contact form
        st.write("For any technical issues, comments or feedback, please reach out to us. We would love to hear from you!")
        components.html(f"""<iframe src={st.session_state.config_param['CONTACT_FORM_LINK']} width="640" height="900" frameborder="0" marginheight="0" marginwidth="0">Loading…</iframe>""", width=640, height=900)