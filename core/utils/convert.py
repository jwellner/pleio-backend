import json
import logging
from core.lib import is_valid_json
from core.utils import tiptap_schema
from prosemirror.model import Node
from prosemirror.model import DOMSerializer
from django.utils.text import Truncator

logger = logging.getLogger(__name__)


def is_tiptap(json_string):
    if not is_valid_json(json_string):
        return False

    data = json.loads(json_string)

    return isinstance(data, dict) and data.get("type", None) == "doc"

def tiptap_to_html(s):
    if not is_tiptap(s):
        return s

    doc = json.loads(s)
    try:
        doc_node = Node.from_json(tiptap_schema, doc)
        html = DOMSerializer.from_schema(tiptap_schema).serialize_fragment(doc_node.content)
    except Exception as e:
        logger.error(e)
        html = s
    return str(html)

def tiptap_to_text(json_string):

    if not is_tiptap(json_string):
        return json_string

    doc = json.loads(json_string)

    def get_text(node):
        text = ""
        if node['type'] == 'text':
            text += node['text']
        elif node['type'] == 'hardBreak':
            text += "\n"
        elif node['type'] == 'mention':
            text += '@' + node['attrs']['label']
        else:
            for item in node.get('content', []):
                text += get_text(item)
            text += "\n"
        return text

    text = ""

    for node in doc.get('content', []):
        text += get_text(node)
        text += "\n"

    return text

def truncate_rich_description(description):
    return Truncator(tiptap_to_text(description)).words(26)
