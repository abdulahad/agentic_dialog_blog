from streamlit import set_page_config
import base64
import streamlit.components.v1 as components
import streamlit as st
from pathlib import Path

class PageConfig():

    def __init__(self, page_title: str, is_initial_page: bool = False):
        self.page_title = page_title
        self.is_initial_page = is_initial_page

    def setup_page(self):
        set_page_config(page_title=self.page_title,
                        page_icon='images/small_logo.png',
                        layout='wide')

    def set_header_with_logo(self):
        def get_base64_of_bin_file(png_file):
            with open(png_file, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()

        logo_path = Path("images/logo.png")
        if not logo_path.is_file():
            st.error("Logo file not found. Please check the file path.")
            return

        base64_logo = get_base64_of_bin_file(str(logo_path))

        # Test just image
        st.image("images/logo.png")

        # Use HTML and CSS to make the image a scrolling banner
        components.html(
            f"""
            <style>
            .header-banner {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 4.0rem;
                background-image: url('data:image/png;base64,{base64_logo}');
                background-size: contain;
                background-repeat: no-repeat;
                background-color: white;
                z-index: 1000;
            }}
            .css-1aumxhk {{
                width: 200px;  /* Minimum width for the sidebar */
            }}
            </style>
            <div class="header-banner"></div>
            <script>
            // Ensure the content is not hidden behind the fixed header
            document.body.style.paddingTop = "4.0rem";
            </script>
            """,
            width=0, height=0
        )

    def configurate_page(self):
        self.setup_page()
        self.set_header_with_logo()

        if self.page_title == 'Correction':
            prefix = 'redaction'
            language = st.session_state['original_language'] if 'original_language' in st.session_state else None
        elif self.page_title == 'Correction Traduction':
            prefix = 'traduction'
            language = st.session_state['translate_language'] if 'translate_language' in st.session_state else None
        else:
            return
        return prefix, language
