import streamlit as st
from src.page_config import PageConfig
from dotenv import load_dotenv, dotenv_values, unset_key
import os
import time
from io import BytesIO
import docx2txt
from openai import OpenAI
from src.ui.settings import UIHandlerSettings
import pandas as pd

load_dotenv()
client = OpenAI(default_headers={"OpenAI-Beta": "assistants=v2"})

def create_assistant(uploaded_files, client_name, system_prompt, default_tone):
    if uploaded_files:
        # Check the file type
        # for file in uploaded_files:
        #     if file.type not in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/pdf", "text/plain"]:
        #         st.error("Unsupported file format. Please upload a DOCX, PDF, or TXT file.")
        #         return None

        all_files = get_all_guideline_files('./data/writing_assistant_files/')
        
        for uploaded_file in uploaded_files:
            file_content = uploaded_file.getvalue()
            file_obj = BytesIO(file_content)
            file_obj.name = uploaded_file.name
            all_files.append(file_obj)
        
        try:
            # Create vector store
            vector_store = client.beta.vector_stores.create(name=f"{client_name}")
            
            # Upload files to vector store
            file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id,
                files=all_files
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")
        else:
            st.success("Files uploaded successfully to the vector store!")
            st.write(file_batch.file_counts)

        try:
            # Create the assistant with the uploaded file
            assistant = client.beta.assistants.create(
                instructions=f"{system_prompt}",
                name=f"{client_name}",
                model="gpt-4o",
                tools=[{"type": "file_search"}],
                metadata={'IS_WRITING_ASSISTANT': 'True',
                          'IS_SEO_ANALYSIS_ASSISTANT': 'False',
                          'IS_SEO_OPTIMIZATION_ASSISTANT': 'False',
                          'IS_CORRECTION_ASSISTANT': 'False',
                          'DEFAULT_TONE': default_tone}
            )

            assistant_updated = client.beta.assistants.update(
                assistant_id=assistant.id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return ":red[assistant creation has failed]"
        else:
            st.success(f"The assistant has succesfully been created")
            return assistant_updated
    else:
        st.error("Please upload a file.")

# Define function to read all `.docx` files from a directory
def get_all_guideline_files(directory_path):
    file_list = []
    for file_name in os.listdir(directory_path):
        if file_name.endswith('.docx'):
            file_path = os.path.join(directory_path, file_name)
            with open(file_path, 'rb') as file:
                file_content = file.read()
                file_obj = BytesIO(file_content)
                file_obj.name = file_name
                file_list.append(file_obj)
        else:
            st.error(f"Can't load file {file_name} due to incompatible file type.")
    return file_list

def add_assistant_to_env(assistant_id, client_name):
    env_path = '.env'
    # Generate the new key based on the assistant name
    new_key = f"blog_writer_id_{client_name}"
    # Set the new key-value pair in the .env file
    with open(env_path, 'a') as env_file:
        env_file.write(f'\n{new_key} = {assistant_id}')

def remove_assistant_from_env(assistant_id):
    env_file = '.env'
    env_vars = dotenv_values(env_file)
    key_to_remove = None
    for key, value in env_vars.items():
        if value == assistant_id:
            key_to_remove = key
            break
    if key_to_remove:
        unset_key(env_file, key_to_remove)
        return True
    else:
        return False
    
def get_assistant_id_from_env(client_name):
    env_path = '.env'
    # Generate the key to be searched based on the client name
    key_to_search = f"blog_writer_id_{client_name}"

    # Read the .env file
    with open(env_path, 'r') as env_file:
        lines = env_file.readlines()

    # Search for the key and retrieve its value
    for line in lines:
        if line.strip().startswith(f"{key_to_search} ="):
            # Extract the value part after the '=' sign and strip any whitespace
            assistant_id = line.split('=', 1)[1].strip()
            return assistant_id

def delete_vector(assistant_id):
    # retrieve assistant details
    assistant_details = client.beta.assistants.retrieve(f"{assistant_id}")
    vector_store_ids = getattr(assistant_details.tool_resources.file_search, 'vector_store_ids', None)
    if len(vector_store_ids) == 0:
        st.write('Pas de vecteur associé à cet assistant...')
    else:
        vector_store_ids = assistant_details.tool_resources.file_search.vector_store_ids[0]
        # delete associated files
        if len(assistant_details.tool_resources.file_search.vector_store_ids) > 1:
            for vector in vector_store_ids:
                delete_file(vector)
        else:
            delete_file(assistant_id)
        #delete vector store
        deleted_vector_store = client.beta.vector_stores.delete(
            vector_store_id=f"{vector_store_ids}",
        )
        st.write(deleted_vector_store)

def delete_file(assistant_id):
    assistant_details = client.beta.assistants.retrieve(f"{assistant_id}")
    vector_id = assistant_details.tool_resources.file_search.vector_store_ids[0]
    # retrieve file associated with vector
    vector_store_files = client.beta.vector_stores.files.list(
        vector_store_id=f"{vector_id}"
    )

    for file in range(len(vector_store_files.data)):
    # Deleting the files using the extracted IDs
        try:
            deleted_files = client.files.delete(vector_store_files.data[file].id)
            st.write(deleted_files)

        except Exception as e:
            st.error(f"Error deleting files: {e}")

def delete_files_from_df(selected_file_df):
    """ The input is a dataframe that contains all selected files for deletion """
    file_ids = selected_file_df['File id']
    for file_id in file_ids:
        deleted_file = client.files.delete(file_id)
        st.write(deleted_file)

def delete_assistant(assistant_id):
    # fetch associated file ID
    assistant_details = client.beta.assistants.retrieve(f"{assistant_id}")
    vector_store_ids = assistant_details.tool_resources.file_search.vector_store_ids
    if len(vector_store_ids) > 0:
        delete_vector(assistant_id)
    # delete assistant
    assistant_status = client.beta.assistants.delete(assistant_id)
    return assistant_status

def upload_file_to_existing_assistant(assistant_id, uploaded_files, client_name):
    if not uploaded_files:
        st.error("Please upload a file.")
        return None

    # Assuming the first uploaded file is the one you want to use
    file = uploaded_files

    # # Check the file type
    # if file.type not in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/pdf", "text/plain"]:
    #     st.error("Unsupported file format. Please upload a DOCX, PDF, or TXT file.")
    #     return None

    # Retrieve assistant details
    assistant_details = client.beta.assistants.retrieve(assistant_id)


    # check if vector store exists and create it if not
    vector_store_ids = getattr(assistant_details.tool_resources.file_search, 'vector_store_ids', None)

    if len(vector_store_ids) == 0:
        st.write("no vector associated with this assistant creating one...")
        vector_store = client.beta.vector_stores.create(name=f"{client_name}")
        vector_store_id = vector_store.id

            # Read file content
        file_content = file.getvalue()

        # Create a file-like object
        file_obj = BytesIO(file_content)
        file_obj.name = file.name  # Set the name attribute

        # Upload the file directly
        upload_response = client.beta.vector_stores.files.upload(
            vector_store_id=f"{vector_store_id}",
            file=file_obj,
        )
        st.write(upload_response)

        assistant_updated = client.beta.assistants.update(
            assistant_id=assistant_id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )
        st.write(assistant_updated)

        return assistant_updated

    else:
        vector_store_id = assistant_details.tool_resources.file_search.vector_store_ids[0]
        # Read file content
        file_content = file.getvalue()

        # Create a file-like object
        file_obj = BytesIO(file_content)
        file_obj.name = file.name  # Set the name attribute

        # Upload the file directly
        upload_response = client.beta.vector_stores.files.upload(
            vector_store_id=f"{vector_store_id}",
            file=file_obj,
        )


        st.write(upload_response)
        time.sleep(1)
    return vector_store_id

def is_valid_assistant_name(client_name, writing_assistants):
    for assistant in writing_assistants:
        if assistant.name == client_name:
            break
    else:
        return True
    return False

def search_assistants_by_metadata_key(key, value):
    response = client.beta.assistants.list()
    matching_assistants = []

    for assistant in response:
        metadata = assistant.metadata
        if metadata.get(key, False) and value.lower() in str(metadata[key]).lower():
            matching_assistants.append(assistant)
    
    return matching_assistants

def modify_assistant_tone(assistant, new_tone):
    metadata = assistant.metadata
    metadata['DEFAULT_TONE'] = new_tone
    client.beta.assistants.update(
            assistant_id=assistant.id,
            metadata=metadata,
        )
    return

#### Setting up page config
config = PageConfig(page_title='Paramètres')
config.configurate_page()

ui_handler = UIHandlerSettings()
tab1, tab2, tab3 = st.tabs(["Créer un Agent", "Modifier un Agent", "Supprimer un Agent"])

with tab1:
    writing_assistants = search_assistants_by_metadata_key(key='IS_WRITING_ASSISTANT', value='True')
    ui_handler.display_assistant_creation()
    user_input = ui_handler.get_assistant_creation_vars()
    if user_input['uploaded_files'] and user_input['client_name']:
        if is_valid_assistant_name(user_input['client_name'], writing_assistants):
            if st.button("Create Assistant"):
                assistant = create_assistant(user_input['uploaded_files'], user_input['client_name'], user_input['system_prompt'], user_input['default_tone'])
                st.write(assistant)
        else:
            st.error("An assistant with this name already exists, please change the name before continuing.")

with tab2:
    writing_assistants = search_assistants_by_metadata_key(key='IS_WRITING_ASSISTANT', value='True')
    ui_handler.display_assistant_modification(writing_assistants, client)
    user_input = ui_handler.get_assistant_modification_vars()

    # Replacing all knowledge files flow
    if user_input['delete_files']:
        print(user_input['selected_files'])
        print("Type of selected files: ", type(user_input['selected_files']))
        if isinstance(user_input['selected_files'], pd.DataFrame):
            try:
                delete_files_from_df(user_input['selected_files'])
            except Exception as e:
                st.error(f"Encountered an error when trying to update the assistant")
                raise Exception(e)
            else:
                st.success("Succesfully updated the assistant")
                with st.spinner("Reloading assistant..."):  # This is a massive hack XD, the deletion of the vector files happens too slowly on OpenAI's end, so we wait until they update on their end before continuing
                    time.sleep(4)
                    st.rerun() # To reload the dataframe
        else:
            st.error("Veuillez televerser des documents pour remplacer le fichier knowledge existant.")

    # Adding files to knowledge flow
    elif user_input['add_files']:
        if user_input['uploaded_files']:
            try:
                vector_store_id = upload_file_to_existing_assistant(user_input['assistant'].id, user_input['uploaded_files'], user_input['assistant'].name)
                # Add back default instruction files
            except Exception as e:
                st.error(f"Encountered an error when trying to update the assistant")
                raise Exception(e)
            else:
                st.success("Succesfully updated the assistant")

        else:
            st.error("Veuillez televerser des documents pour remplacer le fichier knowledge existant.")

    elif user_input['change_tone']:
        try:
            modify_assistant_tone(user_input['assistant'], user_input['default_tone'])
        except Exception as e:
            st.error(f"Encountered an error when trying to update the assistant")
            raise Exception(e)
        else:
            st.success("Succesfully updated the assistant")    

with tab3:
    writing_assistants = search_assistants_by_metadata_key(key='IS_WRITING_ASSISTANT', value='True')
    ui_handler.display_assistant_deletion(writing_assistants)
    user_input = ui_handler.get_assistation_deletion_vars()

    if user_input['delete_button_pressed']:
        print("Deleting assistant")

        try:
            assistant_status = delete_assistant(user_input['assistant'].id)  # Replace with actual deletion logic
            st.write(assistant_status)
        except Exception as e:
            st.error(f"Ran into an error when trying to delete the assistant: {e}")
        else:
            st.success(f"Successfully deleted the assistant.")

        st.session_state['delete_button_pressed'] = False
