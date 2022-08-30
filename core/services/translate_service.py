import json
import warnings

import requests

from autotranslate.services import BaseTranslatorService
from django.conf import settings
from requests import HTTPError


class DeeplTranslatorService(BaseTranslatorService):
    BASE_URL = 'https://api-free.deepl.com/v2/translate'

    def __init__(self):
        pass

    def translate_string(self, text, target_language, source_language='en'):
        try:
            print('[INFO][PAID] Doing deepl request')
            conf = {
                'auth_key': settings.DEEPL_TOKEN,
                'text': text,
                'source_lang': source_language.upper(),
                'target_lang': target_language.upper(),
            }

            response = requests.get(self.BASE_URL, data=conf, timeout=10)
            response.raise_for_status()
            print("TRANSLATION", response.text, response.status_code)
            return json.loads(response.text)['translations'][0]['text']
        except HTTPError:
            warnings.warn("Error while translating {}. Have you set it up properly?".format(text))

    def translate_strings(self, strings, target_language, source_language='en', optimized=True):

        result = []

        for s in strings:
            text = self.translate_string(s, target_language, source_language)
            result.append(text)

        return tuple(result)
