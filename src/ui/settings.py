import streamlit as st
from dotenv import dotenv_values
import pandas as pd
import datetime

class UIHandlerSettings():

    def __init__(self):
        pass

    def load_default_system_prompt(self, file_name='default_system_prompt.txt'):
        with open(f'prompts/{file_name}', 'r') as file:
            prompt = file.read()
        return prompt
    
    @st.experimental_dialog("Are you sure?")
    def confirmation_pop_up(self, assistant):
        st.write("This action will delete all information associated with the following assistant:")
        st.write(f":red[{assistant.name}]")
        st.write("")

        verification_code = st.text_input("Enter verification code to delete the assistant", type="password")

        if st.button("Yes", help="This action is not reversible"):
            if verification_code == "admin007":
                print("Setting session state var as True")
                st.session_state['delete_button_pressed'] = True
                st.session_state['show_confirmation'] = False
                st.rerun()
            else:
                st.error("You shall not pass !!!")
        else:
                st.session_state['show_confirmation'] = False
    
    def get_assistant_creation_vars(self):
        return self.creation_input

    def get_assistant_modification_vars(self):
        return self.modification_input

    def get_assistation_deletion_vars(self):
        return self.deletion_input

    def display_assistant_creation(self):
        # Create a file uploader widget to allow users to upload files
        col_width, _ = st.columns([0.3, 0.7])
        with col_width:
            client_name = st.text_input("Entrez le nom du client")

        # Streamlit file uploader
        accept_multiple_files = True # Setting false for consistency, but works
        uploaded_files = st.file_uploader("Insérer le profil client (brief de rédaction général, page \"à propos\", offre de service...)",
                                          accept_multiple_files=accept_multiple_files, type=['docx','pdf', 'html', 'txt'])
        # Necessary formatting of user_input, or else error
        if not accept_multiple_files:
            uploaded_files = [uploaded_files]

        system_prompt = st.text_area("Modifier le system prompt ici", height=300, value=self.load_default_system_prompt())
        default_tone = st.text_area("Specifier le ton par défaut de la rédaction ici", height=200, max_chars=512, placeholder="e.g., Accessible and friendly, yet professional. The tone should promote collaboration and participation, reflecting the company's professionalism and approachability. Write using emotion, anecdotes.")

        self.creation_input = {'client_name': client_name, 'uploaded_files': uploaded_files, 'system_prompt': system_prompt, 'default_tone': default_tone}

    def format_assistant_display(self, x):
        if x == None:
            return None
        else:
            return x.name   
        
    def load_assistant_tone(self, assistant):
        if assistant == None:
            return None
        else:
            default_tone = assistant.metadata.get("DEFAULT_TONE", None)
            return default_tone
        
    def format_assistant_files(self, client, assistant):
        # Get files for an assistant
        assistant_details = client.beta.assistants.retrieve(assistant.id)
        vector_store_ids = assistant_details.tool_resources.file_search.vector_store_ids
        if not vector_store_ids:
            return []
        else:
            # retrieve files associated with vector
            vector_file_list = client.beta.vector_stores.files.list(
                vector_store_id=vector_store_ids[0],  # Assuming there is only one vector store associated with an assistant (this is our convention)
                filter='completed'  # This removes any failed uploads from appearing (like secret files, backup word docs aswell: w/ format ~<shortened file name>)
            ).data
            return [client.files.retrieve(file.id) for file in vector_file_list]

    def format_file_dataframe(self, files):
        data = []
        for file in files:
            data.append({
                'Date created': datetime.datetime.fromtimestamp(file.created_at),
                'File name': file.filename,
                'File id': file.id,
            })

        return pd.DataFrame(data)
    
    def get_file_display_config(self):
        return {
            "Date created": st.column_config.DatetimeColumn(
                "Date Created", help="The date that the file was added", width='medium'
            ),
            "File name": st.column_config.TextColumn(
                "File Name", help="The name of the file", width='medium'
            ),
            "File id": st.column_config.TextColumn(
                "File ID", help="The identifier of the file", width='medium'
            )
        }
    
    def display_streamlit_dataframe(self, pd_dataframe, column_config):
        return st.dataframe(
            pd_dataframe,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
        )

    def display_assistant_modification(self, writing_assistants, client):
        assistant = st.selectbox("Selectionnez l'assistant à modifier:", writing_assistants, format_func=self.format_assistant_display)

        st.write("#### Rajoutez des fichiers a l'assistant")
        uploaded_files = st.file_uploader("Insérer un nouveau fichier profil client", accept_multiple_files=False,
                                            type=['docx','pdf', 'html', 'txt'])
        
        add_files = st.button("Ajouter le fichier au knowledge existant")

        st.write("#### Fichiers knowledge de l'assistant")
        assistant_files = self.format_assistant_files(client, assistant) #
        if not assistant_files:
            st.info("There are no files associated with this assistant.")
            selected_files = None
            delete_files = False
        else:
            files_dataframe = self.format_file_dataframe(assistant_files)
            file_config = self.get_file_display_config()
            st_dataframe = self.display_streamlit_dataframe(files_dataframe, file_config)
            selected_files = files_dataframe.iloc[st_dataframe.selection.rows]

            delete_files = st.button("Supprimer les fichiers selectionnes")
        
        st.write("#### Ton et style de l'assistant")
        default_tone = st.text_area("Modifier le ton et style de l'agent ici", height=200, max_chars=512, value=self.load_assistant_tone(assistant), placeholder="e.g., Accessible and friendly, yet professional. The tone should promote collaboration and participation, reflecting the company's professionalism and approachability. Write using emotion, anecdotes.")
        change_tone = st.button("Changer le ton et style de l'agent")

        self.modification_input = {'assistant': assistant, 'uploaded_files': uploaded_files, 'delete_files': delete_files, 'selected_files': selected_files, 'add_files': add_files, 'change_tone': change_tone, 'default_tone': default_tone}
    
    def display_assistant_deletion(self, writing_assistants):
        assistant = st.selectbox("Selectionnez l'assistant à supprimer:", writing_assistants, format_func=self.format_assistant_display)

        if 'delete_button_pressed' not in st.session_state:
            st.session_state['delete_button_pressed'] = False

        if 'show_confirmation' not in st.session_state:
            st.session_state['show_confirmation'] = False

        if st.button("Supprimer Assistant"):
            st.session_state['show_confirmation'] = True

        if st.session_state['show_confirmation']:
            self.confirmation_pop_up(assistant)

        self.deletion_input = {'assistant': assistant, 'delete_button_pressed': st.session_state.get('delete_button_pressed', False)}
