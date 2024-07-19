# Import the required libarries
import json
import streamlit as st
from src.common.home import Home
from src.common.chatBot import ChatBot
from src.common.courseMaterial import CourseMaterial
from src.s3.getFiles import load_files_from_s3, get_updated_config_list
from src.common.reference import Reference
from src.common.quiz import Quiz
from src.common.contactForm import ContactForm
from src.demos.whatIf import WhatIf
from src.demos.calculations import BiasAuditCalculations
from src.demos.contractSummarizer import ContractSummarizer
from src.common.logger import Logger
from src.common.sidebar import sidebar
from src.demos.myReports import MyReports

# Instantiate the logger
logger = Logger.get_logger()
config_list = get_updated_config_list()


def refresh_application():
    """
    Function to refresh the application based on the user's selection.
    """
    # Refresh the application if it is updated
    if st.session_state.prev_application != st.session_state.active_application:
        logger.info(
            f"Logging into application: {st.session_state.active_application}")
        if st.session_state['active_application'] in {"COLCPL", "CALLAW", "EUAIA"}:
            st.session_state.page_home = Home()
            return
        if st.session_state['active_application'] not in {"CONSU"}:
            if "retriever" in st.session_state:
                del st.session_state['retriever']
            if "messages" in st.session_state:
                del st.session_state['messages']
            st.session_state.page_chatbot = ChatBot()
            st.session_state.page_home = Home()
            st.session_state.page_quiz = Quiz()
            if "ques_count_per_module" in st.session_state:
                del st.session_state["ques_count_per_module"]
                del st.session_state["current_question"]
                del st.session_state["show_explanation"]

            st.session_state.page_reference = Reference()
            st.session_state.page_courseMaterial = CourseMaterial()
            st.session_state.page_contact_form = ContactForm()
        if st.session_state['active_application'] == 'AEDT':
            st.session_state.page_home = Home()
            st.session_state.page_what_if_analysis = WhatIf()
            st.session_state.page_bias_audit = BiasAuditCalculations()
            st.session_state.page_myReports = MyReports()
        st.session_state.prev_application = st.session_state.active_application


st.set_page_config(page_title="AlgoAudit", layout="wide", page_icon="🏬")


_, logout_button_space = st.columns([0.9, 0.1])
if logout_button_space.button("Logout", use_container_width=True, type="primary"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.switch_page("pages/login.py")

sidebar(disabled_button="")


if "user_info" not in st.session_state:
    st.session_state.user_info = {}
    st.session_state.allowed_config = {}
    st.switch_page("pages/login.py")

if "prev_application" not in st.session_state:
    st.session_state.prev_application = ""

if "config_param" not in st.session_state:
    st.session_state.config_param = None


def set_config_param():
    print("Set config param called", st.session_state.prev_application, st.session_state.active_application, st.session_state.config_param)
    # Set the configuration parameters
    params = st.session_state.config_list[st.session_state['active_application']]
    st.session_state.config_param = params

    with st.spinner("Fetching latest files..."):
        # Download the latest files from S3
        load_files_from_s3(
            params["S3_BUCKET_PREFIX"], params["LOCAL_PATH"])

    # Refresh the application with the new parameters
    refresh_application()


if st.session_state.user_info and st.session_state.allowed_config:

    mapping = {
        "AEDT":"New York Automated Employement Decision Tools (AEDT)",
        "COLCPL": "Colorado Law Concerning Consumer Protections In Interactions With AI Systems Course ",
        "CALLAW": "California AI Transparency ACT",
        "EUAIA": "EU AI Act",
    }
    reverse_mapping = {
        "New York Automated Employement Decision Tools (AEDT)":"AEDT",
        "Colorado Law Concerning Consumer Protections In Interactions With AI Systems Course":"COLCPL",
        "California AI Transparency ACT":"CALLAW",
        "EU AI Act":"EUAIA",
    }

    for key in config_list:
        if key in st.session_state.allowed_config['courses']:
            reverse_mapping[config_list[key]["APP_NAME"]] = key
            mapping[key] = config_list[key]["APP_NAME"]

    st.session_state.config_list = json.load(
        open("data/config_list.json", "r"))

    # Display the application options
    # application_options = st.session_state.allowed_config['courses']
    # application = application_options[0]

    # Show a dropdown to select the application
    st.session_state['active_application'] = reverse_mapping[st.sidebar.selectbox("Select Application:", mapping.values(
    ), disabled=True if not st.session_state.user_info else False, on_change=set_config_param)]
    print("Selected application", st.session_state['active_application'])
    application_index = st.session_state.allowed_config['courses'].index(
        st.session_state.active_application)

    # Get the allowed pages for the selected application
    allowed_pages = st.session_state.allowed_config['allowed_pages'][application_index]

    if "Quiz" in allowed_pages:
        allowed_pages[allowed_pages.index("Quiz")] = "Assessment"
    if "QuBot" in allowed_pages:
        allowed_pages[allowed_pages.index("QuBot")] = "QuCopilot"
    if "Contact Form" in allowed_pages:
        allowed_pages[allowed_pages.index("Contact Form")] = "Feedback Page"

    # Show the pages based on the user's selection
    st.session_state.page = st.sidebar.radio("Select a Page:", allowed_pages,
                                             disabled=True if not st.session_state.user_info else False)

    set_config_param()
else:
    st.switch_page("pages/login.py")
set_config_param()
# Display the selected pages
if "page" in st.session_state:
    try:
        if st.session_state.page == "Home":
            st.session_state.page_home.main()
        elif st.session_state.page == "Course Material - Slides":
            st.session_state.page_courseMaterial.show_slides()
        elif st.session_state.page == "Course Material - Videos":
            st.session_state.page_courseMaterial.show_videos()
        elif st.session_state.page == "QuCopilot":
            if st.session_state.active_application == "CONSU":
                if "clicked_contract_contents" in st.session_state and st.session_state.clicked_contract_contents:
                    st.session_state.page_chatbot.main()
                else:
                    st.header("QuCopilot", divider="blue")
                    st.warning(
                        "Please upload a contract in 'Contract Summarizer' to access Chat Bot.")
            else:
                st.session_state.page_chatbot.main()
        elif st.session_state.page == "Assessment":
            st.session_state.page_quiz.main()
        elif st.session_state.page == "Reference PDF":
            st.session_state.page_reference.main()
        elif st.session_state.page == "What If Analysis":
            st.session_state.page_what_if_analysis.main()
        elif st.session_state.page == "Bias Audit":
            st.session_state.page_bias_audit.main()
        elif st.session_state.page == "Use Cases":
            st.session_state.page_use_cases.main()
        elif st.session_state.page == "Feedback Page":
            st.session_state.page_contact_form.main()
        elif st.session_state.page == "My Reports":
            st.session_state.page_myReports.main()
        elif st.session_state.page == "Contract Summarizer":
            st.session_state.page_contract_summarizer.main()
    except Exception as e:
        logger.error("Exception: ", e)
        st.error(e)

