from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
import google.generativeai as gemini
import streamlit as st


# Singleton class for LLM
def singleton(cls, *args, **kw):
    instances = {}
    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton

class LLM:
    """
    Singleton class for LLM

    Attributes:
    config: Configuration for the LLM
    llm: ChatOpenAI object for the LLM

    Methods:
    get_response(prompt) - get the response from the LLM
    """
    def __init__(self, llm="chatgpt"):
        self.llm_type = llm
        if llm=="chatgpt":
            self.llm = ChatOpenAI(model=st.secrets["OPENAI_MODEL"], 
                              temperature=1, 
                              api_key=st.secrets["OPENAI_KEY"])
        elif llm=="gemini":
            gemini.configure(api_key=st.secrets["GEMINI_API_KEY"])
            self.llm = gemini.GenerativeModel(model_name = "gemini-pro")

    def change_llm_type(self, llm_type):
        self.llm_type = llm_type
        if llm_type=="chatgpt":
            self.llm = ChatOpenAI(model=st.secrets["OPENAI_MODEL"], 
                              temperature=1, 
                              api_key=st.secrets["OPENAI_KEY"])
        elif llm_type=="gemini":
            gemini.configure(api_key=st.secrets["GEMINI_API_KEY"])
            self.llm = gemini.GenerativeModel(model_name = "gemini-pro")
        
    def get_response(self, prompt, inputs=None):
        # Create the chain
        if self.llm_type=="chatgpt":
            chain = LLMChain(llm=self.llm, prompt=prompt)
            print("Prompt", prompt)
            print("Chain", chain)
            response = chain.invoke(input=inputs)['text']
            print("Invocation", chain.invoke(input=inputs))
            print("Response", response)
            return response
        elif self.llm_type=="gemini":
            if inputs is None:
                inputs = {}
            response = self.llm.generate_content(
                prompt.invoke(inputs).to_string(),
            )
            return response.text
