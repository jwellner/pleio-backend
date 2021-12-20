import json
import requests

from autotranslate.services import BaseTranslatorService
from django.conf import settings

class DeeplTranslatorService(BaseTranslatorService):

    BASE_URL = 'https://api-free.deepl.com/v2/translate'
 
    def __init__(self):
        pass

    def translate_string(self, text, target_language, source_language='en'):

        print('[INFO][PAID] Doing deepl request')
        conf = {
            'auth_key': settings.DEEPL_TOKEN,
            'text': text,
            'source_lang': source_language.upper(),
            'target_lang': target_language.upper(),
        }

        resp = requests.get(self.BASE_URL, data = conf)
        print("TRANSLATION", resp.text, resp.status_code)
        text = json.loads(resp.text)['translations'][0]['text']

        return text

    def translate_strings(self, strings, target_language, source_language='en', optimized=True):

        result = []

        for s in strings:
            text = self.translate_string(s, target_language, source_language)
            result.append(text)

        return tuple(result)