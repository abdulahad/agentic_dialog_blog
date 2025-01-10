import pandas as pd
import streamlit as st
import os
from dotenv import load_dotenv, dotenv_values
from src.ui.baseClassUI import baseClassUI
from openai import OpenAI
from dotenv import load_dotenv

# This should be moved along with search_assistants_by_metadata_key to a different class that has as parent class the OpenAIClient
load_dotenv()
print("Oopenkey",os.getenv('OPENAI_API_KEY'))
client = OpenAI(default_headers={"OpenAI-Beta": "assistants=v2"})

class UIHandlerRedaction(baseClassUI):
    """ Related to redacteur.py and seo_optimisation.py """
    def __init__(self, placeholder_length=None, placeholder_brief=None, placeholder_links=None, placeholder_keywords=None):
        self.placeholder_length = placeholder_length
        self.placeholder_brief = placeholder_brief
        self.placeholder_links = placeholder_links
        self.placeholder_keywords = placeholder_keywords

    # This should be moved along with client instantiation at top of the file to a different class that has as parent class the OpenAIClient
    def search_assistants_by_metadata_key(self, key, value):
        response = client.beta.assistants.list()
        matching_assistants = []
        for assistant in response:
            matching_assistants.append(assistant)
        # for assistant in response:
        #     metadata = assistant.metadata
        #     if metadata.get(key, False) and value.lower() in str(metadata[key]).lower():
        #         matching_assistants.append(assistant)
        
        return matching_assistants
    
    def format_assistant_display(self, x):
        if x == None:
            return None
        else:
            return x.name   
        
    def get_default_tone(self):
        if self.assistant == None:
            return None
        else:
            metadata = self.assistant.metadata
            default_tone = metadata.get("DEFAULT_TONE", None)
            return default_tone

    def dataframe_to_string(self, df):
        return "\n".join([f"[{row['Expressions']}]({row['Liens']})" for _, row in df.iterrows()])

    def display_ui(self):

        col_width, col_2, _ = st.columns([0.3, 0.3, 0.4])
        
        with col_width:
            client_option = self.search_assistants_by_metadata_key(key='IS_WRITING_ASSISTANT', value='True') # This should be moved, see comment about function def
            self.assistant = st.selectbox("Selectionnez le client:", client_option, index=None, placeholder="Choissisez une option", format_func=self.format_assistant_display)

        # Selection format of final text
        with col_width:
            format_text_option = ["Blog", "Page Service", "Page Locale", "Page Categorie", "Page Produit"]
            self.format = st.selectbox("Selectionnez le format:", format_text_option, index=None, placeholder="Choissisez une option")

        with col_width:
            language_option = ["Francais", "Anglais"]
            self.original_language = st.selectbox("Selectionnez la langue de rédaction:", language_option, index=None, placeholder="Choissisez une option")

        with col_2:
            self.text_length = st.text_input("Entrez la longueur cible du texte en nombre de mots", value=self.placeholder_length, placeholder="e.g., 1500")

        with col_2:
            self.theme = st.text_input("Entrez le mot-clé principal", value=None, placeholder="e.g., optimisation SEO")

        self.key_words = st.text_area("Ajouter ici les termes que vous souhaitez voir dans le contenu (minimum 20):", height=100, value=self.placeholder_keywords, placeholder="ChatGPT x3, IA x1, communication x2, ...")

        check_box = True
        #check_box = st.checkbox("Activer l'amélioration du text avec Claude", value = True)
        if check_box:
            self.ton = st.text_area("Rajoutez avec précision le ton et style spécifique de cet article", height=100, max_chars=512, value=self.get_default_tone(), placeholder="e.g., Accessible and friendly, yet professional. The tone should promote collaboration and participation, reflecting the company's professionalism and approachability. Write using emotion, anecdotes.")
            self.check = True
        else:
            self.check = None
            self.ton = None

        self.user_brief = st.text_area("Collez le brief ici:", height=300, value=self.placeholder_brief, placeholder="Collez le brief dans le format Hn")

        #self.links = st.text_area("Rajoutez des liens ici [lien; mots associés]:", height=100, value=self.placeholder_links, placeholder="[www.google.com; Google Search], [www.bing.com; Bing Search], ...")
        st.caption(":grey[Rajoutez des liens et leurs expressions associée ici:]")
        data_links = [{"Expressions":"",
                       "Liens":""}]
        df = pd.DataFrame(data_links)
        link_data = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True)
        self.links = self.dataframe_to_string(link_data)

    def format_user_input_value(self, value):
        if isinstance(value, str) and not value.strip(): # If the value is an empty string, replace with a None value
            return None
        else:
            return value

    def get_user_input(self):
        """ Return all user input on call and save user_input to session_state """
        missing_input = False
        user_input = dict()
        for key, value in self.__dict__.items():
            value = self.format_user_input_value(value)
            # Handle input from necessary fields
            if key in ['assistant', 'format', 'original_language', 'user_brief', 'theme']:
                if value == None:
                    word_map = {'assistant': 'assistant', 'format': 'format', 'original_language': 'redaction language', 'user_brief': 'brief', 'theme': 'mot clef principal'}
                    st.error(f"You have forgotten to specify a value for the {word_map[key]}.")
                    missing_input = True
                else:
                    st.session_state[key] = value
                    user_input[key] = value

            elif key in ['text_length', 'key_words', 'links', 'ton', 'check']:
                if value == None and key != 'check':
                    word_map = {'text_length': 'text length', 'key_words': 'key words', 'links': 'links', 'ton': 'ton et style'}
                    if (key == 'text_length') and (value == None): # If user doesn't specify length, will create a reasonable length based off of the size of the plan
                        st.info("You have not set a value for text_length, the length of your content will therefore reflect the size of the brief")
                        st.session_state[key] = 'Any reasonable length given the size of the brief'
                        user_input[key] = 'Any reasonable length given the size of the brief'
                        continue
                    elif not key == 'ton':
                        st.info(f"You have not set a value for {word_map[key]}")
                    elif key == 'ton' and self.check == True: # Only raise any info message if the tone box is present on the user's page
                        st.info(f"You have not set a value for '{word_map[key]}', Claude text improvement will still occur, but without the additional tone and style instructions")

                st.session_state[key] = value
                user_input[key] = value

        if missing_input:
            return None
        else:
            return user_input
