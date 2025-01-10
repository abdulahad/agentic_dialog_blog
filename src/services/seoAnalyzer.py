import os
from dotenv import load_dotenv
from src.OpenAIClient import Client
import streamlit as st
import requests
from src.services.promptReader import promptReader
import re
import unicodedata
from bs4 import BeautifulSoup
import markdown2
import math

class sessionStateHandler(promptReader):
    def __init__(self, prefix):
        super().__init__(prompt_folder_path='prompts/analysis')
        self.prefix = prefix

    def _set_initial_seo_session_state(self):
        st.session_state[f'{self.prefix}_seo_analysis'] = dict()

    def _set_seo_session_state_rating(self, rating):
        st.session_state[f'{self.prefix}_seo_analysis']['rating'] = rating

    def _set_seo_session_state_content_checklist(self, content_checklist):
        st.session_state[f'{self.prefix}_seo_analysis']['content_checklist'] = content_checklist

class seoAnalyzer(sessionStateHandler):
    """ Analyzes the text used to instantiate the class along certain SEO axes """

    def __init__(self, user_brief, theme, text, links, word_limit,  keywords, prefix):
        super().__init__(prefix=prefix)
        self.user_brief = user_brief
        self.theme = theme
        self.text = text
        self.links = links
        self.word_limit = word_limit
        self._set_client()
        self._set_initial_seo_session_state()
        self.keywords = keywords

    def _set_client(self):
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        self.client = Client(api_key)

    def get_words_from_target(self):
        # Remove lines in the format [visual: <some text>]
        cleaned_text = re.sub(r'\[visual:.*?\]', '', self.text, flags=re.MULTILINE)

        # Convert markdown to plain text
        plain_text = markdown2.markdown(cleaned_text)

        # Remove HTML tags to get pure text
        soup = BeautifulSoup(plain_text, 'html.parser')
        text_only = soup.get_text()

        # Get word count from pure text
        word_count = len(text_only.split())

        # Calculate difference between word count and word limit
        diff = abs(word_count - int(self.word_limit))

        # Choose color based off of size of diff
        if diff <= (int(self.word_limit) * 0.25):
            color = '#158237'  # Green
        elif diff <= (int(self.word_limit) * 0.40):
            color = '#D95A00'  # Orange
        else:
            color = '#FF2B2B'  # Red

        # Return formatted string
        return f"{color},{word_count}/{self.word_limit}"

    def perform_seo_analysis(self):
    
        # Get quantifiable checklist (Manual - Code)
        quant_checklist, quant_stats = self.fill_quantchecklist() # Should return dict where keys are equal to the conditions and values are bool
        print(quant_checklist)

        # Get qualitative checklist (Automatic - ChatGPT) 
        quali_checklist, quali_stats = self.fill_qualichecklist() # Should return dict where keys are equal to the conditions and values are bool

        # Combine the checklists, and calculate the score
        content_checklist = f"{quant_checklist}\n{quali_checklist}"
        content_score = self.calculate_score(quant_stats, quali_stats)

        # Get AI score
        ai_detection_score = self.check_zero_gpt(self.text)

        # Get fraction of words over target words
        word_fraction = self.get_words_from_target()

        # Set state vars
        self._set_seo_session_state_rating([content_score, ai_detection_score, word_fraction])
        self._set_seo_session_state_content_checklist(content_checklist)

    def check_sentence_word_counts(self, word_limit=30, pct=0.95):
        """
        Args:
        word_limit: The word limit per sentence.
        pct: The percentage of sentences that must be under the word limit
        Returns:
        (str, bool): The sentence that will be added to the checklist, and a boolean that indicate if the condition is fulfilled or not
        """
        stripped_text = re.sub(r'(^H[1-9].*$|^#{1,9}.*$|^[\*\+\-].*$|^\d+.*$|^\|.*\|$|^\|\s*:-{1,}\s*\|.*$|^\[visual: .*?\]$)', '', self.text, flags=re.MULTILINE)

        # Split the text into sentences
        sentences = re.split(r'(?<=[.!?]) +', stripped_text)

        # Count the number of words in each sentence
        word_counts = [len(sentence.split()) for sentence in sentences]

        # Calculate the percentage of sentences under the word limit
        under_limit_count = sum(1 for count in word_counts if count <= word_limit)
        percentage_under_limit = under_limit_count / len(sentences)

        # Determine if the condition is fulfilled
        condition_met = percentage_under_limit >= pct

        # Format sentence
        if condition_met:
            checkmark = 'x'
        else:
            checkmark = ' '
        sentence = f"- [{checkmark}] {int(pct*100)}% des phrases comptent moins de {word_limit} mots. (**{int(percentage_under_limit*100)}%** des phrases répondent à cette contrainte)"

        return sentence, condition_met

    def check_paragraph_word_counts(self, floor=0, ceiling=80, pct=0.95):
        """
        Args:
        floor: The lower end of how many words are allowed per paragraph
        ceiling: The higher end of how many words are allowed per paragraph
        pct: The percentage of paragraphs that must be between the floor and ceiling
        Returns:
        (str, bool): The sentence that will be added to the checklist, and a boolean that indicate if the condition is fulfilled or not
        """

        # Strip titles and list items
        stripped_text = re.sub(r'(^H[1-9].*$|^#{1,9}.*$|^[\*\+\-].*$|^\d+.*$|^\|.*\|$|^\|\s*:-{1,}\s*\|.*$|^\[visual: .*?\]$)', '', self.text, flags=re.MULTILINE)

        # Split the text into paragraphs
        paragraphs = stripped_text.split('\n\n')

        # Calculate word counts for each paragraph
        word_counts = [len(paragraph.split()) for paragraph in paragraphs]

        # Count paragraphs within the specified word range
        within_range_count = sum(1 for count in word_counts if floor <= count <= ceiling)

        # Calculate the percentage of paragraphs within the specified range
        percentage_within_range = within_range_count / len(paragraphs)

        # Determine if the condition is met
        condition_met = percentage_within_range >= pct

        # Format the sentence
        if condition_met:
            checkmark = 'x'
        else:
            checkmark = ' '

        sentence = f"- [{checkmark}] {int(pct*100)}% des paragraphes comportent entre {floor} et {ceiling} mots. (**{int(percentage_within_range*100)}%** des paragraphes repondent a cette contrainte)"

        return sentence, condition_met

    def remove_accents(self, input_str):
        """ Removes accents and special characters from the input string. """
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

    def main_keyword_in_first_paragraph(self, character_buffer=250):
        """ Checks if the main keyword appears in the first paragraph. """

        # Normalize and remove accents from the keyword (theme) and the first paragraph
        normalized_keyword = self.remove_accents(self.theme).lower()
        normalized_first_paragraph = self.remove_accents(self.text[:500]).lower()

        # Check if the keyword is in the first paragraph
        condition_is_met = normalized_keyword in normalized_first_paragraph

        # Format sentence
        checkmark = 'x' if condition_is_met else ' '
        sentence = f"- [{checkmark}] Le mot-clé principal figure dans les {character_buffer} premiers caractères"

        return sentence, condition_is_met

    # def periods_at_end_of_bulletpoints(self):
    #     """ Checks if there are any periods at the end of bullet points in markdown formatted text. """
    #     # Find bullet points in markdown format
    #     bullet_points = re.findall(r'^[\*\-\+]\s+.*$', self.text, re.MULTILINE)
    #
    #     # Check if any bullet points end with a period
    #     has_periods = any(point.strip().endswith('.') for point in bullet_points)
    #
    #     if not has_periods:
    #         checkmark = 'x'
    #     else:
    #         checkmark = ' '
    #     sentence = f"- [{checkmark}] :green[Les listes à puces ne se terminent pas par un point.]"
    #
    #     # Return the result
    #     return sentence, not has_periods

    def no_link_beginning_content(self, character_buffer=100):
        """
        Determines if a link is present within the first X characters of the content (X is determined by the character buffer)
        """
        # Find the first markdown link in the text
        first_link_match = re.search(r'\[.*?\]\(.*?\)', self.text)

        # Check if the first link starts within the character buffer
        condition_met = True
        if first_link_match:
            condition_met = first_link_match.start() >= character_buffer

        checkmark = 'x' if condition_met else ' '

        sentence = f"- [{checkmark}] Aucun lien n'apparaît en début de contenu. (dans les {character_buffer} caractères à partir du début du contenu)"
        return sentence, condition_met

    def no_link_beginning_of_a_paragraph(self, character_buffer=10):
        """
        Determines if a link is present within the first X characters of any paragraph (X is determined by the character buffer)
        """
        # Split the text into paragraphs
        paragraphs = self.text.split('\n\n')

        # Check if any paragraph has a link within the character buffer
        condition_met = True
        for para in paragraphs:
            first_link_match = re.search(r'\[.*?\]\(.*?\)', para)
            if first_link_match and first_link_match.start() < character_buffer:
                condition_met = False
                break

        checkmark = 'x' if condition_met else ' '

        sentence = f"- [{checkmark}] Aucun lien n'apparaît en début de paragraphe. (dans les {character_buffer} caractères à partir du début d'un paragraphe)"
        return sentence, condition_met

    def no_link_beginning_of_sentence(self, character_buffer=4):
        """
        Determines if a link is present within the first X characters of any sentence (X is determined by the character buffer)
        """
        # Split the text into sentences
        sentences = re.split(r'(?<=[.!?])(?:\s+|\n\n)+', self.text)

        # Check if any sentence has a link within the character buffer
        condition_met = True
        for sent in sentences:
            first_link_match = re.search(r'\[.*?\]\(.*?\)', sent)
            if first_link_match and first_link_match.start() < character_buffer:
                condition_met = False
                break

        checkmark = 'x' if condition_met else ' '

        sentence = f"- [{checkmark}] Aucun lien n'apparaît en début de phrase. (dans les {character_buffer} caractères à partir du début d'une phrase)"
        return sentence, condition_met

    # def no_period_end_of_hn_titles(self):
    #     """ Determines if there are any periods at the end of the Hn titles"""
    #
    #     # Identify the Hn titles (e.g., H1:, H2:, H3: ...)
    #     hn_titles = re.findall(r'^(#{1,9} .+|H[1-9]: .+)$', self.text, re.MULTILINE)
    #
    #     # Determine if there is a period at the end of any of the titles
    #     condition_met = all(not title.strip().endswith('.') for title in hn_titles)
    #
    #     checkmark = 'x' if condition_met else ' '
    #     sentence = f"- [{checkmark}] :green[Les titres Hn ne se terminent pas par un point.]"
    #
    #     return sentence, condition_met

    def extract_hn_structure(self, content):
        """
        Extracts the Hn structure from the given content.

        Args:
        content (str): The content from which to extract the Hn structure.

        Returns:
        list: A list of Hn titles in the order they appear in the content.
        """
        hn_titles = re.findall(r'^(#{2,6} .+|H[2-6]: .+)$', content, re.MULTILINE) # Does not check H1 (title of article)
        hn_titles = [
            re.sub(r'^(#{1,6} |H[1-6]: )', '', self.remove_accents(title.strip())).lower()
            for title in hn_titles
            if not re.search(r'intro|introduction|conclusion', title, re.IGNORECASE)
        ]
        return hn_titles

    def final_hn_matches_plan_hn(self):
        """
        Compares the Hn structure in the initial user brief with the final text.

        Returns:
        (str, bool): The sentence that will be added to the checklist, and a boolean that indicates if the condition is fulfilled or not.
        """
        # Extract the raw Hn structure from the user brief
        # corrected_user_brief = self.client.send_prompt_to_chatgpt(prompt=f'Correct any mistakes in this text, do not change the format or content, do not make any comments before or after your answer: {self.user_brief}', version='4', temperature=0.1)
        initial_hn_structure = self.extract_hn_structure(self.user_brief)
        print("INITIAL HN STRUCTURE: ", initial_hn_structure)

        # Extract the raw Hn structure from the final text
        final_hn_structure = self.extract_hn_structure(self.text)
        print("FINAL HN STRUCTURE: ", final_hn_structure)

        # Compare the two raw Hn structures
        condition_met = initial_hn_structure == final_hn_structure
        checkmark = 'x' if condition_met else ' '

        sentence = f"- [{checkmark}] La structure du contenu est conforme à celle du plan initial."
        return sentence, condition_met

    def internal_linking_of_plan_corresponds_to_text(self, perform_associated_word_check=True):
        """
        Checks that all links inputted by the user are used in the final text.

        Returns:
        (str, bool): The sentence that will be added to the checklist, and a boolean that indicates if the condition is fulfilled or not.
        """
        if perform_associated_word_check:
            # Build markdown format links with [words](http link)
            complete_markdown_links = self.links

            print("LINKS: ", complete_markdown_links)
            # Search text for all links
            condition_met = all(self.remove_accents(markdown_link).lower() in self.remove_accents(self.text).lower() for markdown_link in complete_markdown_links)
        else:
            # Convert links to markdown format
            print("LINKS: ", self.links)

            # Check if each link from the user is present in the text
            condition_met = all(link in self.text for link in self.links)

        checkmark = 'x' if condition_met else ' '
        sentence = f"- [{checkmark}] Tous les liens sont correctement intégrés dans le contenu."
        return sentence, condition_met

    def are_words_in_bold(self, floor_count=7):
        """
        Determines if there are 5 or more words in bold in the text.

        Returns:
        tuple: A tuple containing the formatted sentence and a boolean indicating if the condition is met.
        """
        # Find all bold words in the text
        bold_words = re.findall(r'\*\*(.*?)\*\*|__(.*?)__', self.text)

        # Flatten the list of tuples and filter out empty strings
        bold_words = [word for group in bold_words for word in group if word]

        # Split the bold words into individual words and count them
        bold_word_count = sum(len(word.split()) for word in bold_words)

        # Check if there are 5 or more bold words
        condition_met = bold_word_count >= floor_count

        # Create the checkmark and sentence
        checkmark = 'x' if condition_met else ' '
        sentence = f"- [{checkmark}] Les mots liés au champ lexical du mot clé principal sont en gras"

        return sentence, condition_met

    def main_keyword_density_is_below_threshold(self):
        """
        Checks if the main keyword appears in the text at less than 2% frequency.
        Returns:
        (str, bool): The sentence that will be added to the checklist, and a boolean that indicates if the condition is fulfilled or not.
        """
        # Main keyword to check
        main_keyword = self.remove_accents(self.theme).strip().lower()
        normalized_text = self.remove_accents(self.text).lower()

        # Count occurrences of the main keyword phrase in the normalized text
        keyword_count = normalized_text.count(main_keyword)

        # Split the text into words to calculate the total word count
        text_words = normalized_text.split()
        total_words = len(text_words)

        # Calculate the keyword density
        keyword_density = round(((keyword_count / total_words) * 100), 1)

        # Check if the keyword density is less than 2%
        condition_met = keyword_density < 2

        checkmark = 'x' if condition_met else ' '
        sentence = f"- [{checkmark}] Le mot clé principal représente moins de 2% du contenu final (**{keyword_density}%**)"

        return sentence, condition_met

    def keywords_coverage_is_sufficient(self):
        """
        Checks if the text contains at least 75% of the keywords.
        Returns:
        (str, bool): The sentence that will be added to the checklist, and a boolean that indicates if the condition is fulfilled or not.
        """
        # Normalize and split keywords
        keywords = self.remove_accents(self.keywords).lower()
        keywords = [keyword.strip() for keyword in keywords.replace('\n', ',').split(',') if keyword.strip()]

        # Normalize the text
        normalized_text = self.remove_accents(self.text).lower()

        # Calculate the total number of keywords
        total_keywords = len(keywords)

        # Count the number of keywords present in the text
        keywords_present = sum(1 for keyword in keywords if keyword in normalized_text)

        # Calculate the percentage of keywords present
        coverage_percentage = math.ceil((keywords_present / total_keywords) * 100)

        # Check if the coverage is at least 75%
        condition_met = coverage_percentage >= 75

        checkmark = 'x' if condition_met else ' '
        sentence = f"- [{checkmark}] Le contenu contient au moins 75% des mots clés (**{coverage_percentage}%**)"

        return sentence, condition_met

    def contains_bullet_point_list(self):
        """
        Checks if the text contains at least one bullet point list in Markdown format.
        Returns:
        (str, bool): The sentence that will be added to the checklist, and a boolean that indicates if the condition is fulfilled or not.
        """
        # Split the text into lines
        lines = self.text.split('\n')

        # Check for lines that start with bullet point markers
        bullet_point_present = any(line.strip().startswith(('- ', '* ')) for line in lines)

        # Check if there is at least one bullet point
        condition_met = bullet_point_present

        checkmark = 'x' if condition_met else ' '
        sentence = f"- [{checkmark}] Le contenu contient au moins une liste à puces."

        return sentence, condition_met

    def contains_table(self):
        """
        Checks if the text contains at least one table in Markdown format.
        Returns:
        (str, bool): The sentence that will be added to the checklist, and a boolean that indicates if the condition is fulfilled or not.
        """
        # Split the text into lines
        lines = self.text.split('\n')

        # Initialize variables to track the presence of a table
        header_found = False
        separator_found = False

        for line in lines:
            # Check for a table header (line with pipes)
            if '|' in line and not header_found:
                header_found = True
                continue

            # Check for a separator line (line with dashes and pipes)
            if header_found and '-' in line and '|' in line:
                separator_found = True
                break

        # Condition is met if both a header and a separator are found
        condition_met = header_found and separator_found

        checkmark = 'x' if condition_met else ' '
        sentence = f"- [{checkmark}] Le contenu contient au moins un tableau."

        return sentence, condition_met


    def fill_quantchecklist(self):
        checklist = ""
        total = 0
        total_pos = 0

        sentence, is_fulfilled = self.main_keyword_in_first_paragraph()
        if is_fulfilled:
            total_pos += 10
        checklist += sentence + '\n'
        total += 10

        sentence, is_fulfilled = self.check_sentence_word_counts()
        if is_fulfilled:
            total_pos += 5
        checklist += sentence + '\n'
        total += 5

        sentence, is_fulfilled = self.check_paragraph_word_counts()
        if is_fulfilled:
            total_pos += 7
        checklist += sentence + '\n'
        total += 7

        # sentence, is_fulfilled = self.periods_at_end_of_bulletpoints()
        # if is_fulfilled:
        #     total_pos += 1
        # checklist += sentence + '\n'
        # total += 1

        if self.links is not None:
            sentence, is_fulfilled = self.no_link_beginning_content()
            if is_fulfilled:
                total_pos += 5
            checklist += sentence + '\n'
            total += 5

            sentence, is_fulfilled = self.no_link_beginning_of_a_paragraph()
            if is_fulfilled:
                total_pos += 3
            checklist += sentence + '\n'
            total += 3

            sentence, is_fulfilled = self.no_link_beginning_of_sentence()
            if is_fulfilled:
                total_pos += 3
            checklist += sentence + '\n'
            total += 3

            sentence, is_fulfilled = self.internal_linking_of_plan_corresponds_to_text()
            if is_fulfilled:
                total_pos += 8
            checklist += sentence + '\n'
            total += 8

        # sentence, is_fulfilled = self.no_period_end_of_hn_titles()
        # if is_fulfilled:
        #     total_pos += 1
        # checklist += sentence + '\n'
        # total += 1

        sentence, is_fulfilled = self.final_hn_matches_plan_hn()
        if is_fulfilled:
            total_pos += 10
        checklist += sentence + '\n'
        total += 10

        sentence, is_fulfilled = self.are_words_in_bold()
        if is_fulfilled:
            total_pos += 3
        checklist += sentence + '\n'
        total += 3

        sentence, is_fulfilled = self.main_keyword_density_is_below_threshold()
        if is_fulfilled:
            total_pos += 8
        checklist += sentence + '\n'
        total += 8

        sentence, is_fulfilled = self.keywords_coverage_is_sufficient()
        if is_fulfilled:
            total_pos += 7
        checklist += sentence + '\n'
        total += 7

        sentence, is_fulfilled = self.contains_bullet_point_list()
        if is_fulfilled:
            total_pos += 1
        checklist += sentence + '\n'
        total += 1

        sentence, is_fulfilled = self.contains_table()
        if is_fulfilled:
            total_pos += 1
        checklist += sentence + '\n'
        total += 1

        return checklist, {'total_pos': total_pos, 'total': total}
    
    def check_if_hook_condition_is_met(self):
        # Load prompt
        vars = {'article': self.text[:2000]}
        prompt = self.load_prompt(file_name='is_a_hook_method_used.txt', vars=vars)

        # SEO Analyst instructions: "think step by step, etc..."
        instructions = self.load_prompt(file_name='is_a_hook_method_used_system_instructs.txt')

        # Send prompt to ChatGPT
        return self.client.send_prompt_to_chatgpt(prompt, version='4', temperature=0.05, system_instructions=instructions)
    
    def format_analysis(self, condition, is_condition_met):
        # Load prompt
        vars = {'condition': condition, 'analysis': is_condition_met}
        prompt = self.load_prompt(file_name='format_condition_analysis.txt', vars=vars)

        # Load system instructions
        instructions = self.load_prompt(file_name='format_condition_system_instructs.txt')

        # Send prompt
        return self.client.send_prompt_to_chatgpt(prompt, version='4', temperature=0.05, system_instructions=instructions)
    
    def format_hook_condition(self, condition_is_completed, condition, recap_of_method_used=""):
        if condition_is_completed == "0":
            replace_var = "- [ ] :orange["
        elif condition_is_completed == "1":
            replace_var = "- [x] :orange["
        else:
            print("Assistant fucked up the answer of the condition ", condition)
            print("Returning with an empty checkbox")
            replace_var = "- [ ] :orange["

        return replace_var + condition[6:] + " " + recap_of_method_used + "]"
    
    def uses_hook_method_in_intro(self):

        condition = "- [ ] Le contenu contient une accroche au début"
        print("#########################################")
        print("#########################################")
        print(" ")
        # Get AI to determine if the condition is met
        is_condition_met = self.check_if_hook_condition_is_met()
        print("IS CONDITION MET: ", is_condition_met)

        # Format that result so that it can be displayed in a checkmark list
        true_or_false = self.format_analysis(condition, is_condition_met)
        if true_or_false == "1":
            is_fulfilled = True
        else:
            is_fulfilled = False

        print(" ")
        print("TRUE OR FALSE: ", true_or_false)

        formatted_condition = self.format_hook_condition(true_or_false, condition)
        print(" ")
        print("FORMATTED CONDITION: ", formatted_condition)

        return formatted_condition, is_fulfilled

    def fill_qualichecklist(self):
        # This is used for conditions that cannot be tested programmatically
        # Applies a unique function for each check
        checklist = ""
        total_pos = 0
        total = 0

        sentence, is_fulfilled = self.uses_hook_method_in_intro()
        if is_fulfilled:
            total_pos += 3
        checklist += sentence + '\n'
        total += 3

        return checklist, {'total_pos': total_pos, 'total': total}

    def calculate_score(self, stats_1, stats_2):
        total_conditions = stats_1['total'] + stats_2['total']
        total_positive = stats_1['total_pos'] + stats_2['total_pos']
        return int((total_positive/total_conditions)*100)

    def check_zero_gpt(self, text):
        url = "https://zerogpt.p.rapidapi.com/api/v1/detectText"
        payload = {"input_text": text}
        headers = {
            "x-rapidapi-key": os.getenv('ZEROGPT_API_KEY'),
            "x-rapidapi-host": "zerogpt.p.rapidapi.com",
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        value = response.json().get('data', {}).get('is_gpt_generated', 'N/A')
        value = math.floor(value) if value != 'N/A' else value
        return value