# coding: utf-8
import pathlib
import textwrap

import google.generativeai as genai

from IPython.display import display
from IPython.display import Markdown

genai.configure(api_key='AIzaSyD5Vid1eSzGoamZtb_vITvn98tITSX5WeY')


def to_markdown(text):
    text = text.replace('•', '  *')
    return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))


for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
