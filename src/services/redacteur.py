import os
from dotenv import load_dotenv
from src.OpenAIClient import Client
import openai
from anthropic import Anthropic
import streamlit as st
from src.finalTextStorage import finalTextStorage
from src.services.promptReader import promptReader

class Redacteur(promptReader):
    def __init__(self, assistant, format, original_language, user_brief, text_length, theme, key_words, links, ton, check):
        super().__init__(prompt_folder_path='prompts/redaction')        
        self.writer_id = assistant.id
        self.format = format
        self.language = original_language
        self.user_brief = user_brief
        self.text_length = text_length
        self.theme = theme
        self.key_words = key_words
        self.links = links
        self.ton = ton
        self.check = check
        self._set_client()
        self._initialize_session_state()

    def _set_client(self):
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        self.client = Client(api_key)

    def _initialize_session_state(self):
        """ Setup session data for persisting info throughout different steps """
        st.session_state['final_versions'] = finalTextStorage()

    def convert_user_brief_to_markdown(self):
        """ Converts any user brief to markdown """
        vars = {'text_length': self.text_length, 'user_brief': self.user_brief}
        prompt = self.load_prompt(file_name='convert_user_brief_to_markdown.txt', vars=vars)
        return self.client.send_prompt_to_chatgpt(prompt, version='4')

    def retrieve_number_of_sections_from_brief(self, markdown_brief):
        """ Retrieves number of sections specified in the brief """
        vars = {'markdown_brief': markdown_brief}
        prompt = self.load_prompt(file_name='retrieve_number_of_sections_from_brief.txt', vars=vars)
        return self.client.send_prompt_to_chatgpt(prompt, version='4', temperature=0.1)

    def rediger(self):
        if self.format == "Blog":
            file_name = 'blog_post_instructions.txt'
        elif self.format == "Page Service":
            file_name = 'page_service_instructions.txt'
        elif self.format == "Page Locale":
            file_name = 'page_locale_instructions.txt'
        elif self.format == "Page Categorie":
            file_name = 'page_categorie_instructions.txt'
        elif self.format == "Page Produit":
            file_name = 'page_produit_instructions.txt'
        else:
            raise ValueError(f"{self.format} is not yet handled")
        return self.write_blog(file_name)
    
    def load_additional_instructions(self, file_name):
        with open(f'prompts/additional_instructions/{file_name}', 'r') as file:
            prompt = file.read()
        if st.session_state['DISPLAY_PROMPT_OUTPUT_BACKEND']:
            print("--------------------------------")
            print(f"Loading additional instructions: {file_name}")
        return prompt
    
    def write_blog(self, file_name):
        print("Working on writing blog...")
        markdown_brief = self.convert_user_brief_to_markdown()
        st.session_state['user_brief'] = markdown_brief
        number_of_sections = self.retrieve_number_of_sections_from_brief(markdown_brief)

        additional_instructions = self.load_additional_instructions(file_name=file_name)
        # Start discussion thread with writer
        thread = self.blog_writing_setup(markdown_brief, additional_instructions)

        # Write the article sections from within discussion thread
        blog_article = self.write_blog_article_sections(number_of_sections, thread, additional_instructions)
        
        return {'media': blog_article, 'markdown_brief': markdown_brief}

    def blog_writing_setup(self, user_brief, additional_instructions):
        # Give the assistant the user brief as context
        vars = {'theme': self.theme, 'user_brief': user_brief, 'key_words': self.key_words, 'links': self.links, 'language': self.language, 'text_length': self.text_length}
        prompt = self.load_prompt(file_name='blog_writing_setup.txt', vars=vars)
        thread = self.client.beta.threads.create()
        _ = self.client.add_prompt_to_thread(thread_id=thread.id, prompt=prompt)
        self.client.runAssistant(self.writer_id, thread.id, info_msg=f"Giving assistant context...", additional_instructions=additional_instructions)
        
        # Return the discussion thread in order to continue
        return thread
    
    def write_blog_article_sections(self, number_of_sections, thread, additional_instructions):
        blog_article = ""

        # Iterate through each section of the blog, writing article as we go
        for section in range(1, int(number_of_sections)+1):
            blog_article += self.write_blog_section(section, thread, additional_instructions)
        return blog_article
    
    def write_blog_section(self, section, thread, additional_instructions):
        vars = {'section': section}
        prompt = self.load_prompt(file_name='write_blog_section.txt', vars=vars)
        _ = self.client.add_prompt_to_thread(thread_id=thread.id, prompt=prompt)
        self.client.runAssistant(self.writer_id, thread.id, info_msg=f"Writing section {section}", additional_instructions=additional_instructions)
        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
        return messages.data[0].content[0].text.value + '\n\n'

    def claude3_clean_this_text_plz(self, text, main_keyword, length, brief, key_words, links, ton):
        client = Anthropic(api_key=os.getenv('CLAUDE3_API_KEY'))
        MAX_CHUNK_SIZE = 4096
        model = "claude-3-5-sonnet-20240620"
        vars = {'main_key_word': main_keyword, 'length': length, 'brief': brief, 'key_words': key_words, 'links': links, 'ton': ton, 'text': text}

        prompt = self.load_prompt(file_name='mr_claude_clean_this_text_plz.txt', vars=vars)
        response = client.messages.create(
                model=model,
                max_tokens=MAX_CHUNK_SIZE,
                temperature=0.4,
                system=prompt,
                messages=[{"role":"user", "content": 'go'}],
        )
        improved_text = response.content[0].text

        return improved_text