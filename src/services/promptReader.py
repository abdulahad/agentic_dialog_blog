import streamlit as st

class promptReader():

    def __init__(self, prompt_folder_path):
        self.folder_path = prompt_folder_path
        self.associated_service = prompt_folder_path.split('/')[1]

    def load_prompt(self, file_name, vars: dict = None):
        with open(f'{self.folder_path}/{file_name}', 'r', encoding='utf-8') as file:
            prompt = file.read()
            if vars != None:
                prompt = self.replace_vars(prompt, vars)
        if st.session_state['DISPLAY_PROMPT_OUTPUT_BACKEND']:
            print("--------------------------------")
            print(f"Prompt {file_name} from {self.associated_service} step")
            print(f"Using the following prompt:")
            print(prompt)
        return prompt

    def replace_vars(self, prompt: str, vars: dict):
        return prompt.format(**vars)