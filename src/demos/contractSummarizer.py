# Import the libraries
import requests
import os
import time
import fitz
import json
import base64
import tempfile
import pandas as pd
import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.ai.formrecognizer._models import AnalyzeResult
from src.common.customHybridRetriever import Retriever
from src.common.logger import Logger

# Create the logger object
logger = Logger.get_logger()

class ContractSummarizer:
    """
    This class is used to display the contract summarizer in the Streamlit app.
    
    Attributes:
    AZURE_AI_ENDPOINT (str): The Azure AI endpoint.
    AZURE_AI_KEY (str): The Azure AI key.
    """

    def __init__(self):
        """
        The constructor for the ContractSummarizer class.
        """
        self.AZURE_AI_ENDPOINT = st.secrets['AZURE_AI_ENDPOINT']
        self.AZURE_AI_KEY = st.secrets['AZURE_AI_KEY']

    def get_field_bounding_regions(self, result):
        """
        This function is used to get the bounding regions of the fields in the contract.
        
        Args:
        result (AnalyzeResult): The AnalyzeResult object.
        
        Returns:
        list: The list of bounding regions.
        """
        res = []

        fields = result.documents[0].fields
        for i in fields:
            if i == "Parties":
                for j, obj in enumerate(fields[i].value):
                    for party_obj in (obj.value):
                        res += obj.value[party_obj].bounding_regions
            else:
                res += fields[i].bounding_regions
        return res

    def get_para_bounding_regions(self, result):
        """
        This function is used to get the bounding regions of the paragraphs in the contract.
        
        Args:
        result (AnalyzeResult): The AnalyzeResult object.
        
        Returns:
        list: The list of bounding regions.
        """
        res = []
        list_of_para = result.paragraphs
        for para in list_of_para:
            temp_dict = para.bounding_regions
            res += temp_dict
        return res

    def get_fields(self, result):
        """
        This function is used to get the fields in the contract.
        
        Args:
        result (AnalyzeResult): The AnalyzeResult object.
        
        Returns:
        DataFrame: The DataFrame containing the fields.
        """
        df_column_names = ["Fields", "Value"]
        df_row = []

        try:
            fields = result.documents[0].fields
            for i in fields:
                if i == "Parties":
                    for j, obj in enumerate(fields[i].value):
                        for party_obj in (obj.value):
                            df_row.append(
                                [f"Party {j+1}: {party_obj}", obj.value[party_obj].content])
                else:
                    df_row.append([i, fields[i].content])

            df = pd.DataFrame(df_row, columns=df_column_names)
            return df
        except:
            df = pd.DataFrame(columns=df_column_names)
            return df

    def add_annotation_boxes(self, pdf_path, bounding_regions, color, annot_name):
        """
        This function is used to add annotation boxes to the PDF.
        
        Args:
        pdf_path (str): The path to the PDF file.
        bounding_regions (list): The list of bounding regions.
        color (tuple): The color of the annotation box.
        annot_name (str): The name of the annotation box.
        
        Returns:
        str: The path to the modified PDF file.
        """
        # Create a temporary file to save the modified PDF
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_pdf_path = temp_file.name

            # Open the PDF
            pdf_document = fitz.open(pdf_path)

            for region in bounding_regions:
                page_number = region.page_number - 1  # Page number starts from 0
                # Convert Point objects to (x, y) tuples
                polygon = [(point.x*72, point.y*72)
                           for point in region.polygon]

                # Get the page
                page = pdf_document[page_number]

                # Add annotation
                annot = page.add_polygon_annot(polygon)
                info = annot.info
                info["name"] = annot_name
                annot.set_info(info)

                if annot_name == "Fields":
                    annot.set_colors(stroke=color)
                    annot.update()
                else:
                    annot.set_colors(fill=color, stroke=color)
                    annot.update(opacity=0.2)

            # Save the changes to the temporary PDF file
            pdf_document.save(temp_pdf_path)
            pdf_document.close()

        return temp_pdf_path

    def display_page(self):
        """
        This function is used to display the contract summarizer in the Streamlit app.
        """
        @st.cache_data(show_spinner=False)
        def initiate_chat_bot(content):
            """
            This function is used to initiate the chat bot.
            
            Args:
            content (str): The content of the contract.
            """
            # with tempfile.TemporaryDirectory() as temp_dir:
            #     temp_file_path = os.path.join(temp_dir, "sample.txt")

            if "retriever" in st.session_state:
                del st.session_state.retriever
                st.session_state.retriever = Retriever()
            else:
                st.session_state.retriever = Retriever()
            
            if "messages" in st.session_state:
                name = st.session_state.user_info['name']
                INITIAL_MESSAGE = [{"role": "assistant",
                        "content": f'Hello {name}! How can I help you today? '}]
                del st.session_state.messages
                st.session_state["messages"] = INITIAL_MESSAGE

            if "response" in st.session_state:
                del st.session_state.response
                st.session_state.ques_session = True
                st.session_state.response = {'answer': f'Hello {name}! How can I help you today? ',
                                'followup_questions': st.session_state.config_param['CHAT_BOT_STARTER_FOLLOW_UP_QUESTIONS']}

            with open(st.session_state.config_param["CONTENT_SAMPLE_TXT"], "w") as sample_txt:
                sample_txt.write(content)

        @st.cache_resource
        def get_azure_client():
            """
            This function is used to get the Azure client.
            
            Returns:
            DocumentAnalysisClient: The DocumentAnalysisClient object.
            """
            document_analysis_client = DocumentAnalysisClient(
                endpoint=self.AZURE_AI_ENDPOINT, credential=AzureKeyCredential(
                    self.AZURE_AI_KEY)
            )
            return document_analysis_client

        @st.cache_data(show_spinner=False)
        def process_pdf(_document_analysis_client, file_content):
            """
            This function is used to process the PDF.
            
            Args:
            _document_analysis_client (DocumentAnalysisClient): The DocumentAnalysisClient object.
            file_content (bytes): The content of the PDF file.
            
            Returns:
            AnalyzeResult: The AnalyzeResult object.
            """
            try:
                poller = _document_analysis_client.begin_analyze_document(
                    "prebuilt-contract", document=file_content
                )

                result = poller.result()
                return result

            except requests.exceptions.RequestException as e:
                st.error(f"Error occurred while calling the API: {e}")
                return None

        # ------------------- STREAMLIT Session Variables -------------------- #
        if "result" not in st.session_state:
            st.session_state.result = None
            st.session_state.new_pdf = False

        if "clicked_contract_contents" not in st.session_state:
            st.session_state.clicked_contract_contents = False

        if "clicked_text_extracted" not in st.session_state:
            st.session_state.clicked_text_extracted = False

        if "clicked_publish_vectorDB" not in st.session_state:
            st.session_state.clicked_publish_vectorDB = False

        # ------------------- STREAMLIT APPLICATION --------------------------

        def reset_file_uploader():
            """
            This function is used to reset the file uploader.
            """
            st.session_state.clicked_contract_contents = False
            st.session_state.clicked_text_extracted = False
            st.session_state.clicked_publish_vectorDB = False

        # Upload PDF file
        # uploaded_file = st.file_uploader("Upload PDF", type="pdf", on_change=reset_file_uploader)
        _, btn1_column, btn2_column, _ = st.columns([0.2, 0.1, 0.3, 0.3])
        # process_uploaded_pdf = btn1_column.button(
        #     "Proceed", type="primary", use_container_width=True, on_click=reset_file_uploader)
        use_sample_file = btn2_column.button(
            "Load up the contract PDF", use_container_width=True, on_click=reset_file_uploader)

        if use_sample_file:
            json_result_path = "./data/CONSU/analyze_result.json"
            st.session_state.input_file_path = "./data/CONSU/consulting_agreement.pdf"

            # Read JSON data from the file
            with open(json_result_path, "r") as json_file:
                analyze_result_json = json.load(json_file)

            # Deserialize JSON data into an AnalyzeResult object
            st.session_state.result = AnalyzeResult.from_dict(
                analyze_result_json)

        # Check if the user clicked the "Process" button
        # if process_uploaded_pdf:
        #     if uploaded_file:
        #         document_analysis_client = get_azure_client()
        #         st.session_state.result = process_pdf(
        #             document_analysis_client, uploaded_file.getvalue()
        #         )
        #         st.session_state.input_file_path = os.path.join(
        #             "data/CONSU/", uploaded_file.name)
        #         with open(st.session_state.input_file_path, "wb") as input_file:
        #             input_file.write(uploaded_file.getvalue())
        #         st.session_state.new_pdf = True
        #     else:
        #         st.warning(
        #             "Please upload the contract OR use the Sample Contract")
        #         st.session_state.result = None
        #         st.stop()

        if st.session_state.result:
            # Get fields
            contract_fields = self.get_fields(st.session_state.result)

            paragragh_bounding_objects = self.get_para_bounding_regions(
                st.session_state.result)
            temp_pdf_path = self.add_annotation_boxes(
                st.session_state.input_file_path, paragragh_bounding_objects, (1, 1, 0), "Paragraph")

            # Add annotation boxes for fields
            field_bounding_objects = self.get_field_bounding_regions(
                st.session_state.result)
            output_pdf_path = self.add_annotation_boxes(
                temp_pdf_path, field_bounding_objects, (1, 0, 0), "Fields")

            # Display the modified PDF in Streamlit
            st.markdown(
                f"<h4 style='text-align: center;'>Annotated PDF</h4>", unsafe_allow_html=True)

            with open(output_pdf_path, "rb") as f:
                pdf_bytes = f.read()
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_display =  f"""<embed
                            class="pdfobject"
                            type="application/pdf"
                            title="Embedded PDF"
                            src="data:application/pdf;base64,{base64_pdf}"
                            style="overflow: scroll; width: 100%; height: 900px;">"""
            # base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            # pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width=100% height="1000" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

            st.divider()

            _, btn_col, _ = st.columns([0.3, 0.4, 0.3])

            # Display contract contents
            if btn_col.button("Display Contract Contents", key="display_content", type="primary", use_container_width=True) or st.session_state.clicked_contract_contents:
                st.session_state.clicked_contract_contents = True

                st.markdown(
                    f"<h4 style='text-align: center;'>Contract Contents</h4>", unsafe_allow_html=True)

                _, df_container, _ = st.columns([0.15, 0.7, 0.15])
                df_container.dataframe(
                    contract_fields, use_container_width=True, hide_index=True)

                st.divider()

            if st.session_state.clicked_contract_contents:
                _, btn_col2, _ = st.columns([0.3, 0.4, 0.3])
                if btn_col2.button("Display Extracted Text", key="display_extracted_text", type="primary", use_container_width=True) or st.session_state.clicked_text_extracted:
                    st.session_state.clicked_text_extracted = True
                    # Display extracted text
                    st.markdown(
                        f"<h4 style='text-align: center;'>Extracted Text</h4>", unsafe_allow_html=True)
                    contract_text = st.container(height=500, border=True)
                    contract_text.text(st.session_state.result.content)

                    os.remove(temp_pdf_path)
                    os.remove(output_pdf_path)
                    st.divider()

            if st.session_state.clicked_text_extracted:
                _, btn_col3, _ = st.columns([0.3, 0.4, 0.3])
                if btn_col3.button("Process Database for Chatbot", key="publish_vector", type="primary", use_container_width=True) or st.session_state.clicked_publish_vectorDB:
                    if not st.session_state.clicked_publish_vectorDB:
                        with st.spinner("Processing the contract..."):
                            content = st.session_state.result.content
                            initiate_chat_bot(content)
                            time.sleep(2)
                    st.write("")
                    st.success("Database created. You can access the Chat Bot!")
                    st.session_state.clicked_publish_vectorDB = True
                    

    def main(self):
        logger.info("Logged in to Contract Summarizer")
        self.display_page()