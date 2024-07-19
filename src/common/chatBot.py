# Import the required libraries
import random
import time
import ast
import json
import streamlit as st
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_openai import OpenAIEmbeddings
from src.common.customHybridRetriever import Retriever
from src.common.logger import Logger

# Create the logger object
logger = Logger.get_logger()

class ChatBot:
    """
    Class to handle the chatbot functionality.

    Attributes:
    OPENAI_KEY (str): The OpenAI key.
    OPENAI_MODEL (str): The OpenAI model.
    embeddings (OpenAIEmbeddings): The OpenAI embeddings.
    chat_model (ChatOpenAI): The OpenAI chat model.
    chat_history (str): The chat history.
    """
    def __init__(self):
        """
        The constructor for the ChatBot class.
        """
        if "openai_key" not in st.session_state:
            OPENAI_KEY = st.secrets["OPENAI_KEY"]
            st.session_state.openai_key = OPENAI_KEY
        self.OPENAI_MODEL =  st.secrets["OPENAI_MODEL"]
        self.embeddings = OpenAIEmbeddings(api_key=st.session_state.openai_key)
        self.chat_model = ChatOpenAI(temperature=0, model_name=self.OPENAI_MODEL, openai_api_key=st.session_state.openai_key)
        self.chat_history = ""
        st.session_state.retriever = Retriever()
        st.session_state.retriever._load_params()
    
    def get_question_context(self, question):
        """
        Function to get the context for the given question.
        
        Args:
        question (str): The question.
        
        Returns:
        str: The context for the question.
        """
        logger.info(f"Getting the context for the question: {question}")
        if "retriever" not in st.session_state:
            st.session_state.retriever = Retriever()
            st.session_state.retriever._load_params()
        return st.session_state.retriever.parse_response_with_rerank(question)
    
    def resolve_question(self, question):
        """
        Function to resolve the question using the ambiguity resolution prompt.

        Args:
        question (str): The question.

        Returns:
        str: The resolved question.
        """
        logger.info(f"Resolving the ambiguity for the question: {question}")
        # Create the language model
        llm = ChatOpenAI(model=self.OPENAI_MODEL, temperature=0, api_key=st.session_state.openai_key)
    
        # Load the ambiguity resolution prompt
        ambiguity_resolution_prompt = json.load(open("data/prompts.json", "r"))["AMBIGUITY_RESOLUTION_PROMPT"]
        prompt = PromptTemplate(
            template=ambiguity_resolution_prompt,
            input_variables=["history", "question"]
        )
        
        # Format the prompt
        _input = prompt.format_prompt(history=self.chat_history.split("\nUser:")[-3:], question=question)

        # Get the response
        output = llm(_input.to_messages())
        return output.content

    def get_response(self, question):
        """
        Function to get the response to the given question.

        Args:
        question (str): The question.

        Returns:
        dict: The response to the question.
        """
        logger.info(f"Getting the response for the question: {question}")
        # Resolve the question
        question = self.resolve_question(question)

        # Create the output parser
        response_schemas = [
                ResponseSchema(name="answer", description="Your answer to the given question in markdown format", type = 'markdown'),
                ResponseSchema(name="follow_up_questions", description="A list of 3 follow-up questions that the user may have based on the question.", type = 'list')
            ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()

        # Get the context
        context = self.get_question_context(question)
        logger.info(f"Context for the question {question}: {context}")
        # Get the response prompt
        response_prompt = json.load(open("data/prompts.json", "r"))["RESPONSE_PROMPT"]


   
        # Create the prompt
        prompt = ChatPromptTemplate(
            messages=[
                HumanMessagePromptTemplate.from_template(response_prompt + st.session_state.config_param["DOCUMENT_LINK"] + ".'")
            ],
            input_variables=["history", "context", "question"],
            partial_variables={"format_instructions": format_instructions}
        )

        # Format the prompt
        _input = prompt.format_prompt(history=self.chat_history.split("\nUser:")[-3:], context=context, question=question)

        # Get the response
        output = self.chat_model(_input.to_messages())
        
        valid_json = False
        runs = 0
        while (valid_json == False):
            try:
                # Parse the output
                json_output = output_parser.parse(output.content)
                valid_json = True
                logger.info(f"Response for the question {question}: {output.content}")

                # Update the chat history
                self.chat_history += f"""\n
                User: {question}
                You: {str(json_output['answer'])}"""

            except Exception as e:
                # If the output is not in JSON format, regenerate the answer for 5 runs
                logger.warning(f"Error in parsing the response for the question {question}: {e}")
                runs+=1
                if runs < 4:

                    # Load the error prompt
                    retry_prompt = json.load(open("data/prompts.json", "r"))["RETRY_PROMPT"]
                    error_prompt = ChatPromptTemplate(
                        messages=[
                                HumanMessagePromptTemplate.from_template(retry_prompt)
                                ],
                        input_variables=["e","history","context","question"],
                        partial_variables={"format_instructions": format_instructions}
                    )

                    # Format the error prompt
                    _error_input = error_prompt.format_prompt(e=e, history=self.chat_history.split("\nUser:")[-3:], context = context, question=question)

                    # Get the response
                    output = self.chat_model(_error_input.to_messages())

                # If the answer cannot be generated, return an error message
                else:
                    return {'answer': f"Something went wrong! Please try again!",
                        'follow_up_questions': []}
                    
        return json_output

    
            
    def main(self):
        """
        The main function to run the chatbot.
        """
        
        logger.info("Logged in to the chatbot.")
        # Get the user information
        name = st.session_state.user_info['name']

        # Set the key owner
        if "keyOwner" not in st.session_state:
            st.session_state.keyOwner = "QU"

        # Front-end chat memory
        INITIAL_MESSAGE = [{"role": "assistant",
                "content": f'Hello {name}! How can I help you today? '}]
        
        # Set the messages
        if "messages" not in st.session_state:
            st.session_state["messages"] = INITIAL_MESSAGE

        # Set the question per session
        if "question_per_session" not in st.session_state:
            st.session_state.question_per_session = 0
      
        # Display the chatbot UI
        st.header(f"QuCopilot - {st.session_state.config_param['APP_NAME']}", divider= "blue")
        st.markdown("""
        <p style='text-align: left; font-size:12px;'><i>Note: </i>
            <i>QuCopilot</i> is an experimental AI-bot that utilizes information for this particular course. You can experiment with QuCopilot a few times for free. Later, you can use your own <a href="{key_link}">OpenAI key</a> for further usage.
            <br />
            Quantuniversity does not store or use this key outside of your current usage. Quantuniversity is not responsible for misuse of the key and is not liable for any charges other than for the current use of the QuCopilot. Use QuCopilot at your own risk.
        </p>
        """.format(url=st.session_state.config_param["DOCUMENT_LINK"], key_link="https://platform.openai.com/docs/quickstart#:~:text=First%2C%20create%20an%20OpenAI%20account,not%20share%20it%20with%20anyone"), unsafe_allow_html=True)

        if st.session_state.keyOwner != "None":

            # Streamed response emulator
            def response_generator(question):
                with st.spinner("Getting you the answer..."):
                    response = self.get_response(question)
                for word in response['answer']:
                    yield word
                    time.sleep(random.random()/100)

            # Display chat messages from history on app rerun
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Accept user input
            if prompt:= st.chat_input("Message QuCopilot..."):
                logger.info(f"User message: {prompt}")
    
                st.session_state.question_per_session += 1
                if st.session_state.question_per_session == st.session_state.config_param["CHATBOT_QUESTIONS_LIMIT"]:
                    st.session_state.keyOwner = 'None'

                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                # Display user message in chat message container
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    response = st.write_stream(response_generator(prompt))
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})


        else:
            logger.warning("User has exhausted free trial.")
            st.warning("You have exhausted your free trial. Enter your OpenAI key below to continue.")
            st.session_state.openai_key = st.text_input('OpenAI key:',type="password")

            if st.button("Submit Key", type="secondary"):
                logger.info("Key submitted.")

                # Check if the key is valid
                try:
                    self.chat_model = ChatOpenAI(temperature=0, model_name = self.OPENAI_MODEL, openai_api_key = st.session_state.openai_key)
                    # Check if key is valid
                    self.get_response("Hello")
                    st.session_state.keyOwner = "USER"
                    logger.info("Key accepted.")
                    st.rerun()
                except Exception as e:
                    logger.error(e)
                    logger.warning("Invalid key entered.")
                    st.error("Invalid key. Please try again.")

