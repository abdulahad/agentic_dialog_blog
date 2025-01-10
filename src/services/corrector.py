import os
from dotenv import load_dotenv
from src.OpenAIClient import Client
import streamlit as st
from src.services.promptReader import promptReader

class Corrector(promptReader):

    def __init__(self, text, prompt, thread=None):
        super().__init__(prompt_folder_path='prompts/correction')
        self.text = text
        self.prompt = prompt
        self._set_client()
        self._set_thread(thread)
        self._set_corrector_id()

    def _set_thread(self, thread):
        # Create thread
        if thread == None:
            self.thread = self.client.beta.threads.create()
        else:
            self.thread = thread

    def _set_client(self):
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        self.client = Client(api_key)

    def _set_corrector_id(self):
        """ 
        The correction assistant id will always appear as such: correction_assistant
        """
        assistant_id = self.client.load_assistant_id("correction_assistant")
        if assistant_id == None:
            raise ValueError("There is no correction assistant specified in the env variables")
        else:
            self.assistant_id = assistant_id

    def apply_prompt_to_text(self):

        print(f"Thread name: ", self.thread.id)

        # Make edits
        self.provide_text_version(self.thread)
        self.provide_instructions(self.thread)
        self.make_edits(self.thread)
        
        # Retrieve result
        result = self.client.beta.threads.messages.list(thread_id=self.thread.id).data[0].content[0].text.value 

        # Update vars + Set up triggers for UI update
        st.session_state['saved_text'] = result
        st.session_state['applied_prompt'] = True
        return result
    
    def provide_text_version(self, thread):
        # Give the assistant the user brief as context
        vars = {'text': self.text}
        prompt = self.load_prompt(file_name='provide_text_version.txt', vars=vars)
        _ = self.client.add_prompt_to_thread(thread_id=thread.id, prompt=prompt)
        self.client.runAssistant(self.assistant_id, thread.id, info_msg=f"Providing text version to corrector....")

    def provide_instructions(self, thread):
        # Give the assistant the user brief as context
        vars = {'instructions': self.prompt}
        prompt = self.load_prompt(file_name='provide_instructions.txt', vars=vars)
        _ = self.client.add_prompt_to_thread(thread_id=thread.id, prompt=prompt)
        self.client.runAssistant(self.assistant_id, thread.id, info_msg=f"Giving instructions to corrector....")

    def make_edits(self, thread):
        prompt = self.load_prompt(file_name='make_edits.txt', vars=None)
        _ = self.client.add_prompt_to_thread(thread_id=thread.id, prompt=prompt)
        self.client.runAssistant(self.assistant_id, thread.id, info_msg=f"Making edits....")