from ariadne import ScalarType

from core.utils.tiptap_parser import Tiptap

secure_rich_text = ScalarType('SecureRichText')


@secure_rich_text.value_parser
def secure_prosemirror_value_parser(value):
    if value:
        tiptap = Tiptap(value)
        tiptap.check_for_external_urls()
    return value
