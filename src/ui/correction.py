from src.ui.baseClassUI import baseClassUI
import streamlit as st
import time
import streamlit.components.v1 as components

class UIHandlerCorrection(baseClassUI):
    def __init__(self, prefix, language, current_meta_stuff):
        self.prefix = prefix
        self.language = language
        self.current_meta_stuff = current_meta_stuff
        self._initialize_variables()

    def _initialize_variables(self):
        vars_exist: bool = f'{self.prefix}_seo_analysis' in st.session_state
        self.score = st.session_state[f'{self.prefix}_seo_analysis']['rating'] if vars_exist else ['-', '-', ',-/-']
        self.content_checklist = st.session_state[f'{self.prefix}_seo_analysis']['content_checklist'] if vars_exist else '_Pas de contenu a analyser, lancez une redaction pour commencer_'

    def display_ui(self):
        self._display_seo_report()

        if f'{self.prefix}_seo_analysis' in st.session_state: 
            self._display_correction_area()

    def ColourWidgetText(self, wgt_txt, wch_colour = '#000000'):
        htmlstr = """<script>var elements = window.parent.document.querySelectorAll('*'), i;
                        for (i = 0; i < elements.length; ++i) { if (elements[i].innerText == |wgt_txt|) 
                            elements[i].style.color = ' """ + wch_colour + """ '; } </script>  """

        htmlstr = htmlstr.replace('|wgt_txt|', "'" + wgt_txt + "'")
        components.html(f"{htmlstr}", height=0, width=0)

    def get_checklist_color(self, value):
        if value >= 80:
            color = '#158237' # Green
        elif value >= 50:
            color = '#D95A00' # Orange
        else:
            color = '#FF2B2B' # Red
        return color

    def get_ai_score_color(self, value):
        if value <= 20:
            color = '#158237' # Green
        elif value < 50:
            color = '#D95A00' # Orange
        else:
            color = '#FF2B2B' # Red
        return color

    def _display_seo_report(self):
        print("CONTENT CHECKLIST:\n", self.content_checklist)
        with st.expander("**Analyse SEO**"):
            st.markdown(self.content_checklist)

        with st.container(border=False, height=None):
            st.write("")
            col1, col2, col3, _, _, _ = st.columns(6)
            word_count_info = self.score[2].split(',')  # (Hex color, fraction of words)
            col1.metric("Score Digitad", str(self.score[0]) + '%')
            col2.metric("Taux de rédaction avec de l'IA", str(self.score[1]) + '%')
            col3.metric("\# de Mots Actuel/# de Mots Cible", word_count_info[1])
            st.divider()
            # if not self.score[2] == '-/-':
            #     self.ColourWidgetText(word_count_info[1], word_count_info[0])
            # if not self.score[0] == '-':
            #     checklist_color = self.get_checklist_color(int(self.score[0]))
            #     self.ColourWidgetText(f"{self.score[0]}%", checklist_color)
            # if self.score[1] != '-' and self.score[1] != 'N/A':
            #     ai_color = self.get_ai_score_color(int(self.score[1]))
            #     self.ColourWidgetText(f"{self.score[1]}%", ai_color)

    def _button_click_behaviour(self):
        if st.session_state['button_text'] == 'Modifier le texte':
            st.session_state['button_text'] = 'Sauvegarder'
        else:
            st.session_state['button_text'] = 'Modifier le texte'
            st.session_state['final_versions'].update_text(self.language, st.session_state['text'])

    def _display_correction_area(self):
        st.header('Contenu Corrigé')

        if 'button_text' not in st.session_state:
            st.session_state['button_text'] = 'Modifier le texte'
        if 'text' not in st.session_state:
            st.session_state['text'] = st.session_state['final_versions'].get_text(self.language)

        st.button(st.session_state['button_text'], on_click=self._button_click_behaviour)

        if (('applied_prompt' in st.session_state) and (st.session_state['applied_prompt'])) or (f'{self.prefix}_first_show_correction_1' not in st.session_state):
            st.session_state['applied_prompt'] = False
            st.session_state[f'{self.prefix}_first_show_correction_1'] = None
            with st.container(border=True):
                text_to_stream = st.session_state['final_versions'].get_text(self.language)
                st.write_stream(self._stream_data(text_to_stream))

        elif st.session_state['button_text'] == 'Modifier le texte':
            with st.container(border=True):
                st.write(st.session_state['final_versions'].get_text(self.language))
        else:
            st.session_state['text'] = st.text_area(label='Modifiez le texte', label_visibility='collapsed', value=st.session_state['final_versions'].get_text(self.language), height=500)

        with st.container():
            self.current_user_prompt = st.chat_input("Demandez des modifications")
        st.session_state['meta'] = ""
        with st.container():
            self.generate_meta = st.button("Générer un meta titre et une meta description.")
            if self.current_meta_stuff != None:
                with st.container(border=True):
                    st.write("**Meta Titre:**")
                    st.write(f"{self.current_meta_stuff['meta_title']}")
                    st.write("**Meta Description:**")
                    st.write(f"{self.current_meta_stuff['meta_description']}")
                st.session_state['meta'] = f"**Meta Titre:**\n\n{self.current_meta_stuff['meta_title']}\n\n **Meta Description:**\n\n{self.current_meta_stuff['meta_description']}"
            else:
                st.info("Generez un meta titre et une meta description en cliquant le button au-dessus")

        return

    def _stream_data(self, data: str):
        for word in data.split(" "):
            yield word + " "
            time.sleep(0.02)

    def get_user_input(self):
        return {
            'current_user_prompt':self. __dict__.get('current_user_prompt', None),
            'generate_meta': self.__dict__.get('generate_meta', None)
        }
