import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv, dotenv_values, unset_key
import os
from io import BytesIO
import time

class VectorService(OpenAI):
    def __init__(self):
        api_key = self._get_openai_api_key()
        super().__init__(api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"})

    def _get_openai_api_key(self):
        load_dotenv()
        return os.getenv('OPENAI_API_KEY')

    def delete_vector(self, assistant_id):
        # retrieve assistant details
        assistant_details = self.beta.assistants.retrieve(f"{assistant_id}")
        vector_store_ids = getattr(assistant_details.tool_resources.file_search, 'vector_store_ids', None)
        if len(vector_store_ids) == 0:
            st.write('Pas de vecteur associé à cet assistant...')
        else:
            vector_store_ids = assistant_details.tool_resources.file_search.vector_store_ids[0]
            # delete associated files
            if len(assistant_details.tool_resources.file_search.vector_store_ids) > 1:
                for vector in vector_store_ids:
                    self.delete_file(vector)
            else:
                self.delete_file(assistant_id)
            #delete vector store
            deleted_vector_store = self.beta.vector_stores.delete(
                vector_store_id=f"{vector_store_ids}",
            )
            st.write(deleted_vector_store)

    def delete_file(self, assistant_id):
        assistant_details = self.beta.assistants.retrieve(f"{assistant_id}")
        vector_id = assistant_details.tool_resources.file_search.vector_store_ids[0]
        # retrieve file associated with vector
        vector_store_files = self.beta.vector_stores.files.list(
            vector_store_id=f"{vector_id}"
        )

        for file in range(len(vector_store_files.data)):
        # Deleting the files using the extracted IDs
            try:
                deleted_files = self.files.delete(vector_store_files.data[file].id)
                st.write(deleted_files)

            except Exception as e:
                st.error(f"Error deleting files: {e}")

class AssistantMetadataService(OpenAI):
    def __init__(self):
        api_key = self._get_openai_api_key()
        super().__init__(api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"})

    def _get_openai_api_key(self):
        load_dotenv()
        return os.getenv('OPENAI_API_KEY')

    def add_assistant_to_env(self, assistant_id, client_name):
        env_path = '.env'
        # Generate the new key based on the assistant name
        new_key = f"blog_writer_id_{client_name}"
        # Set the new key-value pair in the .env file
        with open(env_path, 'a') as env_file:
            env_file.write(f'\n{new_key} = {assistant_id}')

    def remove_assistant_from_env(self, assistant_id):
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

    def get_assistant_id_from_env(self, client_name):
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

class AssistantService(VectorService, AssistantMetadataService):
    def __init__(self):
        super().__init__()

    # Define function to read all `.docx` files from a directory
    def get_all_guideline_files(self, directory_path):
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

    def is_valid_assistant_name(client_name):
        env_vars = dotenv_values('.env')
        for key in env_vars:
            env_name = key[len('blog_writer_id_'):].replace('_', ' ')
            if env_name == client_name:
                st.error('An assistant with this name already exists. If you wish to make changes to it, either modify or delete it.')
                print(f"Matching env name: {env_name}")
                break
        else:
            return True
        return False

    def create_assistant(self, uploaded_files, client_name, system_prompt):
        if uploaded_files:
            # Check the file type
            for file in uploaded_files:
                if file.type not in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/pdf", "text/plain"]:
                    st.error("Unsupported file format. Please upload a DOCX, PDF, or TXT file.")
                    return None


            all_files = self.get_all_guideline_files('./data/writing_assistant_files/')
            
            for uploaded_file in uploaded_files:
                file_content = uploaded_file.getvalue()
                file_obj = BytesIO(file_content)
                file_obj.name = uploaded_file.name
                all_files.append(file_obj)
            
            try:
                # Create vector store
                vector_store = self.beta.vector_stores.create(name=f"{client_name}")
                
                # Upload files to vector store
                file_batch = self.beta.vector_stores.file_batches.upload_and_poll(
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
                assistant = self.beta.assistants.create(
                    instructions=f"{system_prompt}",
                    name=f"{client_name}",
                    model="gpt-4o",
                    tools=[{"type": "file_search"}],
                )

                assistant_updated = self.beta.assistants.update(
                    assistant_id=assistant.id,
                    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
                )
            except Exception as e:
                st.error(f"An error occurred: {e}")
            else:
                st.success(f"The assistant has succesfully been created")

            return assistant_updated
        else:
            st.error("Please upload a file.")

    def delete_assistant(self, assistant_id):
        # fetch associated file ID
        assistant_details = self.beta.assistants.retrieve(f"{assistant_id}")
        vector_store_ids = assistant_details.tool_resources.file_search.vector_store_ids
        if len(vector_store_ids) > 0:
            self.delete_vector(assistant_id)
        # delete assistant
        assistant_status = self.beta.assistants.delete(assistant_id)
        return assistant_status
    
    def upload_file_to_existing_assistant(self, assistant_id, uploaded_files, client_name):
        if not uploaded_files:
            st.error("Please upload a file.")
            return None

        # Assuming the first uploaded file is the one you want to use
        file = uploaded_files

        # Check the file type
        if file.type not in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/pdf", "text/plain"]:
            st.error("Unsupported file format. Please upload a DOCX, PDF, or TXT file.")
            return None

        # Retrieve assistant details
        assistant_details = self.beta.assistants.retrieve(assistant_id)


        # check if vector store exists and create it if not
        vector_store_ids = getattr(assistant_details.tool_resources.file_search, 'vector_store_ids', None)

        if len(vector_store_ids) == 0:
            st.write("no vector associated with this assistant creating one...")
            vector_store = self.beta.vector_stores.create(name=f"{client_name}")
            vector_store_id = vector_store.id

                # Read file content
            file_content = file.getvalue()

            # Create a file-like object
            file_obj = BytesIO(file_content)
            file_obj.name = file.name  # Set the name attribute

            # Upload the file directly
            upload_response = self.beta.vector_stores.files.upload(
                vector_store_id=f"{vector_store_id}",
                file=file_obj,
            )
            st.write(upload_response)

            assistant_updated = self.beta.assistants.update(
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
            upload_response = self.beta.vector_stores.files.upload(
                vector_store_id=f"{vector_store_id}",
                file=file_obj,
            )

            st.write(upload_response)
            time.sleep(1)
        return vector_store_id