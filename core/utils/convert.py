import json
import logging
from core.lib import is_valid_json, draft_to_html
from core.utils import tiptap_schema
from prosemirror.model import Node
from prosemirror.model import DOMSerializer

logger = logging.getLogger(__name__)


def is_draft(json_string):
    if not is_valid_json(json_string):
        return False

    data = json.loads(json_string)

    return isinstance(data, dict) and isinstance(data.get("blocks", None), list)

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


def draft_to_tiptap(draft_string):
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-locals
    """
    Use to convert DraftJS JSON to TipTap JSON
    """

    if not is_draft(draft_string):
        return draft_string

    draft = json.loads(draft_string)

    tiptap = {
        'type': 'doc',
        'content': []
    }


    # draftjs <-> tiptap headers
    map_headers = {
        "header-one": 2,
        "header-two": 2,
        "header-three": 3,
        "header-four": 4,
        "header-five": 5,
        "header-six": 5
    }

    # draftjs <->
    map_styles = {
        "BOLD": "bold",
        "UNDERLINE": "underline",
        "ITALIC": "italic"
    }

    def entityForKey(key):
        return draft["entityMap"][f"{key}"]

    def text_to_content(block):
        content = []

        def get_marks(index):
            in_marks = []

            for i in block['inlineStyleRanges']:
                if index in range(i['offset'], i['offset'] + i['length']):
                    if map_styles.get(i["style"], None):
                        in_marks.append({
                            'type': map_styles[i["style"]]
                        })

            for i in block['entityRanges']:
                entity = entityForKey(i["key"])

                if entity["type"] == "LINK" and index in range(i['offset'], i['offset'] + i['length']):
                    in_marks.append({
                        'type': 'link',
                        'attrs': {
                            'href': entity['data'].get('url', ''),
                            'target': entity['data'].get('target', None)
                        }
                    })

            return in_marks

        content = []
        prev_marks = None

        for idx, letter in enumerate(block["text"]):
            marks = get_marks(idx)

            if prev_marks != marks:
                content.append({
                    "type": "text",
                    "text": ""
                })

                if len(marks) > 0:
                    content[-1]["marks"] = marks

            content[-1]["text"] += letter

            prev_marks = marks

        return content

    for block in draft["blocks"]:

        if block["type"] in map_headers.keys():
            tiptap['content'].append({
                'type': 'heading',
                'attrs': {
                    'level': map_headers[block["type"]]
                },
                'content': text_to_content(block)
            })

        elif block["type"] in ["paragraph", "section", "article", "code-block"]:
            tiptap['content'].append({
                'type': 'paragraph',
                'content': text_to_content(block)
            })

        elif block["type"] == "intro":
            tiptap['content'].append({
                'type': 'paragraph',
                'content': text_to_content(block),
                'attrs': {
                    'intro': True
                }
            })

        elif block["type"] == "blockquote":
            tiptap['content'].append({
                'type': 'blockquote',
                'content': text_to_content(block)
            })

        elif block["type"] in ["unordered-list-item", "ordered-list-item"]:
            list_type = "bulletList" if block["type"] == "unordered-list-item" else "orderedList"
            # prepaire Tiptap listItem
            list_item = {
                'type': 'listItem',
                'content': [
                    {
                        'type': 'paragraph',
                        'content': text_to_content(block)
                    }
                ]
            }

            if len(tiptap['content']) > 0 and tiptap['content'][-1]['type'] == list_type:
                # Handle nested lists
                if block["depth"] > 0:

                    # check if previous was also nested then add else create new
                    if tiptap['content'][-1]["content"][-1]["content"][-1]["type"] == list_type:
                        tiptap['content'][-1]["content"][-1]["content"][-1]["content"].append(list_item)
                    else:
                        tiptap['content'][-1]["content"][-1]["content"].append({
                            'type': list_type,
                            'content': [list_item]
                        })
                else:
                    # Listitem in existing list
                    tiptap['content'][-1]["content"].append(list_item)
            else:
                # Add new list
                tiptap['content'].append({
                    'type': list_type,
                    'content': [list_item]
                })

        elif block["type"] == "atomic":
            if len(block["entityRanges"]) > 0:
                key = block["entityRanges"][0]["key"]
                entity = entityForKey(key)
                if entity["type"] == "IMAGE":

                    caption = None

                    if entity["data"].get("caption", None):
                        caption = draft_to_html(entity["data"]["caption"])

                    tiptap["content"].append({
                        'type': 'image',
                        'attrs': {
                            'src': entity["data"].get("src", ""),
                            "size": entity["data"].get("size", None),
                            "alt": entity["data"].get("alt", None),
                            "caption": caption
                        }
                    })
                if entity["type"] == "VIDEO":
                    tiptap["content"].append({
                        'type': 'video',
                        'attrs': {
                            "platform": entity["data"]["platform"],
                            "guid": entity["data"].get("guid", ""),
                            "title": entity["data"].get("title", "")
                        }
                    })

        elif block["type"] == "unstyled":
            entity = None
            if len(block["entityRanges"]) == 1:
                entity = entityForKey(block["entityRanges"][0]["key"])
                if entity:
                    offset = block["entityRanges"][0]["offset"]
                    length = block["entityRanges"][0]["length"]
                    text = block["text"][:block["entityRanges"][0]["offset"]]
                    text += block["text"][offset+length:]
                    block["text"] = text

            if len(block["text"]) > 0:
                if (
                        len(tiptap["content"]) > 0 and
                        tiptap["content"][-1].get("attrs", None) and
                        tiptap["content"][-1]["attrs"].get("unstyled", None)
                    ): 
                    tiptap["content"][-1]["content"].append({'type': 'hardBreak'})
                    tiptap["content"][-1]["content"].extend(text_to_content(block))
                else:
                    tiptap["content"].append({
                        'type': 'paragraph',
                        'content': text_to_content(block),
                        'attrs': {
                            'unstyled': True
                        }
                    })
            elif not entity:
                # add hardBreak if empty text node and previous is also unstyled
                if (
                        len(tiptap["content"]) > 0 and
                        tiptap["content"][-1].get("attrs", None) and
                        tiptap["content"][-1]["attrs"].get("unstyled", None)
                    ): 
                    tiptap["content"][-1]["content"].append({'type': 'hardBreak'})

            if entity and entity["type"] == "DOCUMENT":
                tiptap["content"].append({
                    'type': 'file',
                    'attrs': {
                        "mimeType": entity["data"].get("mimeType", None),
                        "name": entity["data"].get("name"),
                        "size": entity["data"].get("size", 0),
                        "url": entity["data"].get("url")
                    }
                })

        else:
            logger.error("Unhandled block: \"%s\"", block['type'])
            logger.error(block)

    return json.dumps(tiptap)
