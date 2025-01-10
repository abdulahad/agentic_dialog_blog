import streamlit as st
from src.page_config import PageConfig

from src.services.redacteur import Redacteur
from src.services.seoAnalyzer import seoAnalyzer
from src.services.seoOptimizer import seoOptimizer

from src.ui.redaction import UIHandlerRedaction
from src.testing.load_redaction_examples import load_leano_example, load_none, load_quick_example

def clear_cache():
    for key in st.session_state.keys():
        if key != 'DISPLAY_PROMPT_OUTPUT_BACKEND':
            del st.session_state[key]

#### Setting up page config 
config = PageConfig(page_title='Rédaction', is_initial_page=True)
config.configurate_page()
page_name = 'redaction' # For setting prefix on session vars (and differentiating from traduction vars)

### Set up var for testing prompts
st.session_state['DISPLAY_PROMPT_OUTPUT_BACKEND'] = False

#### Setting up examples
# Three functions you can use here: load_leano_example, load_none or load_quick_example
example_length, example_brief, example_links, example_keywords = load_none()

#### Set up UIpyth
ui_handler = UIHandlerRedaction(example_length, example_brief, example_links, example_keywords)
ui_handler.display_ui()

#### Handle user input and redaction
if st.button('Commencer la redaction'):
    # Clear cache in case user is deciding to re-run redaction on top of an old run
    clear_cache()

    user_input = ui_handler.get_user_input()
    if user_input == None:
        st.error("Handle all issues (in red) before continuing")
    else:
        # Write initial version of the media and save it
        with st.spinner("Rédaction en cours..."):
            redacteur = Redacteur(**user_input)
            results = redacteur.rediger()
            text = results['media']

        if user_input['check']:
            with st.spinner("Amélioration du text"):
                text = redacteur.claude3_clean_this_text_plz(results['media'], user_input['theme'], user_input['text_length'], user_input['user_brief'],
                                                        user_input['key_words'], user_input['links'], user_input['ton'])
        st.session_state['user_brief'] = user_input['user_brief']
        # Analyse the text on certain SEO optimization axes 
        analyzer = seoAnalyzer(user_input['user_brief'], user_input['theme'], text, user_input['links'], user_input['text_length'], user_input['key_words'], prefix=page_name)
        with st.spinner("Analyse SEO en cours..."):
            analyzer.perform_seo_analysis()

        st.session_state['final_versions'].set_version(user_input['original_language'],
                                                                text,
                                                                st.session_state[f'{page_name}_seo_analysis']['rating'],
                                                                is_original=True)


        # for key, value in st.session_state.items():
        #     print("Key: ", key)
        #     print("Value: ", value)
        #     print("-----------------")
        st.switch_page('pages/2Correction.py')
