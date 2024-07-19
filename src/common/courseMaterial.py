# Import the required libraries
import streamlit as st
import fitz
import io
from PIL import Image
from src.common.logger import Logger

# Create the logger object
logger = Logger.get_logger()

class CourseMaterial:
    """
    This class is used to display the course material in the Streamlit app.

    Attributes:
    course_links (list): The list of course links.
    course_names_slides (list): The list of course names.
    videos (list): The list of video links.
    transcripts (list): The list of transcript files.
    """
    def __init__(self):
        """
        The constructor for the CourseMaterial class.
        """
        if "course_index" not in st.session_state:
            st.session_state.course_index_slides = 0
            st.session_state.course_index_videos = 0
            st.session_state.page_num = 0

        self.slides_links = st.session_state.config_param["SLIDES_LINKS"]
        self.course_names_slides = st.session_state.config_param["COURSE_NAMES_SLIDES"]
        self.course_names_videos = st.session_state.config_param["COURSE_NAMES_VIDEOS"]
        self.videos_links = st.session_state.config_param["VIDEOS_LINKS"]
        self.transcripts = st.session_state.config_param["TRANSCRIPTS_FILES"]
    

    def show_slides(self):
        """
        This function is used to display the slides in the Streamlit app.
        """
        logger.info("Logged in to Course Material - Slides")
        # Display the header
        st.header("Course Material - Slides", divider="blue")

        # Handle slide navigation
        def slide_handle_change():
            st.session_state.course_index_slides = st.session_state.config_param["COURSE_NAMES_SLIDES"].index(st.session_state.slides_nav)
            st.session_state.page_num = 0
            logger.info(f"Selected Module for Slides: {st.session_state.course_index_slides}")

        # Display the dropdown to select the modulex
        st.selectbox("Modules",self.course_names_slides, index=st.session_state.course_index_slides, key = "slides_nav", on_change=slide_handle_change)
            
        # Display the dropdown to select the course
        with st.spinner('Wait for it...'):

            url = self.slides_links[st.session_state.course_index_slides]
            doc = fitz.open(url)
            total_pages = len(doc)

            # Display a single page from the pdf as image
            def display_page(page_num):
                page = doc.load_page(page_num)  # load the page
                pix = page.get_pixmap()  # render page to an image
                img = Image.open(io.BytesIO(pix.tobytes()))
                st.image(img, use_column_width=True)

            display_page(st.session_state.page_num)
                                
            # Navigation buttons for the slides
            col1, _, center, _, col2 = st.columns([1, 4, 1, 4, 1])
            with col1:
                if st.button('⇦', use_container_width=True):
                    if st.session_state.page_num > 0:
                        st.session_state.page_num -= 1
                        st.rerun()

            with col2:
                if st.button('⇨', use_container_width=True):
                    if st.session_state.page_num < total_pages - 1:
                        st.session_state.page_num += 1
                        st.rerun()

            with center:
                st.caption(f'Page {st.session_state.page_num + 1}/{total_pages}', )


        # Navigation buttons for the modules
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            if st.session_state.course_index_slides>0:
                
                if st.button("Previous Module", use_container_width=True):
                    st.session_state.course_index_slides-=1
                    st.session_state.page_num = 0
                    st.rerun()            
    
        with col3:
            if st.session_state.course_index_slides<len(self.slides_links)-1:
                
                if st.button("Next Module", use_container_width=True):
                    st.session_state.course_index_slides+=1
                    st.session_state.page_num = 0
                    st.rerun()


    def show_videos(self):
        """
        Functionality to display the videos in the Streamlit app.
        """
        logger.info("Logged in to Course Material - Videos")

        # Display the header
        st.header("Course Material - Videos", divider='blue')

        # Handle video navigation
        def video_handle_change():
            st.session_state.course_index_videos = st.session_state.config_param["COURSE_NAMES_VIDEOS"].index(st.session_state.video_nav)
            logger.info(f"Selected Module for Video: {st.session_state.course_index_videos}")

        # Display the dropdown to select the module
        st.selectbox("Modules",self.course_names_videos, index=st.session_state.course_index_videos, key = "video_nav", on_change=video_handle_change)

        # Display the video
        st.markdown(self.videos_links[st.session_state.course_index_videos], unsafe_allow_html=True)
        
        

        # Navigation buttons for the modules
        st.write(" ")
        col1, _, col2, _, col3 = st.columns([1, 1, 1, 1, 1])
        with col1:
            if st.session_state.course_index_videos>0:
                
                if st.button("Previous Module", use_container_width=True):
                    st.session_state.course_index_videos-=1
                    st.session_state.page_num = 0
                    st.rerun()            
    
        with col3:
            if st.session_state.course_index_videos<len(self.videos_links)-1:
                
                if st.button("Next Module", use_container_width=True):
                    st.session_state.course_index_videos+=1
                    st.session_state.page_num = 0
                    st.rerun()

