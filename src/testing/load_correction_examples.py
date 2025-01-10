import streamlit as st
from src.finalTextStorage import finalTextStorage

def load_example():
    # Set session_state vars from redaction
    st.session_state['format'] = 'Blog'
    st.session_state['language'] = 'Francais'
    st.session_state['text_length'] = '200'
    st.session_state['theme'] = None
    st.session_state['key_words'] = None
    st.session_state['links'] = None
    st.session_state['user_brief'] = "\
            H1: Post de blog par rapport au avancements technologiques \n \
            H2: introduction \n \
            H2: Les avancements technologiques du 21ieme siecle et l'impact sur l'efficacite des travailleurs \n \
            H2: Conclusion"

    # Set session_state vars from seo_optimization (analysis really)
    st.session_state['redaction_seo_analysis'] = dict()
    st.session_state['redaction_seo_analysis']['rating'] = [42, 42, 42]
    st.session_state['redaction_seo_analysis']['issues'] = 'example issues'
    st.session_state['redaction_seo_analysis']['content_checklist'] = 'example content checklist'
    st.session_state['redaction_seo_analysis']['meta_title_checklist'] = 'example meta title checklist'
    st.session_state['redaction_seo_analysis']['meta_description_checklist'] = 'example meta description checklist'
    st.session_state['redaction_seo_analysis']['ai_detection_score'] = dict()
    st.session_state['redaction_seo_analysis']['ai_detection_score']['data'] = dict()
    st.session_state['redaction_seo_analysis']['ai_detection_score']['data']['is_gpt_generated'] = 42

    temp = finalTextStorage()
    temp.set_version(language="Francais", finalized_media="This is a sample text", seo_rating=42, is_original=True)
    st.session_state['final_versions'] = temp
    return

def load_none():
    return