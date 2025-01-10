import time
import os
from dotenv import load_dotenv
import openai
import streamlit as st

class Client(openai.OpenAI):

    def __init__(self, api_key):
        super().__init__(api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"})

    def create_thread(self):
        return self.beta.threads.create()

    def send_prompt_to_chatgpt(self, prompt, version='4', temperature=0.3, system_instructions=None):
        if version not in ['4', '3.5']:
            raise ValueError(f"The chatGPT version {version} is not supported")

        if version == 4:
            model = 'gpt-4o'
        else:
            model = 'gpt-4o-mini'

        # Build message, adding system instruction if specified
        if system_instructions != None:
            messages = [
                {'role': 'system',
                 'content': system_instructions}
            ]
        else:
            messages = list()
        messages.append({"role": "user", "content": prompt})

        response = openai.chat.completions.create(
            model=f"{model}",
            messages=messages,
            temperature=temperature,
            max_tokens=4000
        ).choices[0].message.content
        if st.session_state['DISPLAY_PROMPT_OUTPUT_BACKEND']:
            print("Response:")
            print(response)
        return response

    def runAssistant(self, assistant_id, thread_id, info_msg="Starting an assistant run.", additional_instructions=None):
        print(info_msg)
        run = self.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            additional_instructions=additional_instructions
        )

        while True:
            run = self.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

            if run.status == "completed":
                print("This run has completed!")
                break
            else:
                print("Running assistant...")
                time.sleep(5)

    def add_prompt_to_thread(self, thread_id, prompt: str):
        message = self.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt,
        )
        return message

    def load_assistant_id(self, specifier, type='env'):
        """ Load assistant id using file path 
        
        specifier: either file path or environment variable name
        """

        if type not in ['env', 'file']:
            return ValueError("type variable must be either env or file")

        if type == 'file':
            try:
                with open(specifier, 'r') as file:
                    return file.readline().strip()
            except FileNotFoundError:
                print(f"Assistant ID file not found at {specifier}.")
                return None
        elif type == 'env':
            load_dotenv()
            return os.getenv(specifier)
        else:
            raise Exception("Unknown error, this should never happen")