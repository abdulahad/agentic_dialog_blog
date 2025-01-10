from src.services.promptReader import promptReader

class Translator(promptReader):

    def __init__(self, client, text, target_language, max_chunk, key_words):
        super().__init__(prompt_folder_path='prompts/translation')
        self.client = client
        self.text = text
        self.target_language = target_language
        self.max_chunk = max_chunk
        self.key_words = key_words

    def chunk_text(self):
        paragraphs = self.text.split('\n')
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 1 <= self.max_chunk:
                current_chunk += paragraph + "\n"
            else:
                chunks.append(current_chunk)
                current_chunk = paragraph + "\n"

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def translate_chunk(self, chunk):
        vars = {'target_language': self.target_language, 'key_words': self.key_words, 'chunk': chunk}
        prompt = self.load_prompt(file_name='translate_chunk.txt', vars=vars)     
        translated_chunk = self.client.send_prompt_to_chatgpt(prompt, version='4')
        return translated_chunk

    def translate_text(self):
        print("Working on translating text...")
        chunks = self.chunk_text()
        translated_chunks = []

        for chunk in chunks:
            translated_chunks.append(self.translate_chunk(chunk))

        translated_text = "\n".join(translated_chunks)

        return translated_text
