import os
from dotenv import load_dotenv
from src.OpenAIClient import Client
import streamlit as st
from src.services.promptReader import promptReader

class MetaGenerator(promptReader):

    def __init__(self, article, keyword):
        super().__init__(prompt_folder_path='prompts/meta_generation')
        self.article = article
        self.keyword = keyword
        self._set_client()

    def _set_client(self):
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        self.client = Client(api_key)

    def generate_title(self):
        prompt_vars = {'article': self.article, 'keyword': self.keyword}
        prompt = self.load_prompt('meta_title_prompt.txt', vars=prompt_vars)
        instructs = self.load_prompt('meta_system_instruction.txt', vars=None)
        return self.client.send_prompt_to_chatgpt(prompt=prompt, version='4', system_instructions=instructs)
    
    def generate_desc(self):
        prompt_vars = {'article': self.article, 'keyword': self.keyword}
        prompt = self.load_prompt('meta_description_prompt.txt', vars=prompt_vars)
        instructs = self.load_prompt('meta_system_instruction.txt', vars=None)
        return self.client.send_prompt_to_chatgpt(prompt=prompt, version='4', system_instructions=instructs)