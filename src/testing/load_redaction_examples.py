import streamlit as st

def load_leano_example():
    _development_length_value = '1000'
    with open('data/plan_article_leano_exemple.txt', 'r') as file:
        _development_brief_value = file.read()
    with open('data/liens_inclure_leano_exemple.txt', 'r') as file:
        _liens = ""
        for line in file.readlines():
            _liens += line + ", "
    with open('data/mot_cles_leano_exemple.txt', 'r') as file:
        _mot_cles = ""
        for line in file.readlines():
            _mot_cles += line + ", "
    
    return _development_length_value, _development_brief_value, _liens, _mot_cles

def load_quick_example():
    _development_length_value = '200'
    _development_brief_value = "\
            H1: Post de blog par rapport au avancements technologiques \n \
            H2: introduction \n \
            H2: Les avancements technologiques du 21ieme siecle et l'impact sur l'efficacite des travailleurs \n \
            H2: Conclusion"

    return _development_length_value, _development_brief_value, None, None

def load_none():
    return None, None, None, None