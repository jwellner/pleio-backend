import json
import logging

LOGGER = logging.getLogger(__name__)

class Tiptap:

    def __init__(self, tiptap_json):
        if not tiptap_json:
            self.tiptap_json = {}
        elif isinstance(tiptap_json, str):
            try:
                self.tiptap_json = json.loads(tiptap_json)
            except json.JSONDecodeError:
                LOGGER.warning("Failed to decode json and using empty object instead: %s", tiptap_json)
                self.tiptap_json = {}
        else:
            self.tiptap_json = tiptap_json

    @property
    def mentioned_users(self):
        users = set()
        for mention in self.get_nodes('mention'):
            user = self.get_field(mention, 'id')
            if user:
                users.add(user)

        return users

    @property
    def attached_sources(self):
        sources = set()
        for image in self.get_nodes('image'):
            src = self.get_field(image, 'src')
            if src:
                sources.add(src)

        for file in self.get_nodes('file'):
            src = self.get_field(file, 'url')
            if src:
                sources.add(src)

        return sources

    def get_nodes(self, node_type):
        if (self.tiptap_json.get('type', None) == node_type):
            return [self.tiptap_json]

        nodes = []
        for node in self.tiptap_json.get('content', []):
            tiptap = Tiptap(node)
            nodes.extend(tiptap.get_nodes(node_type))

        return nodes

    def get_field(self, node, field):
        return node.get('attrs', {}).get(field, None)

    def replace_url(self, original, replacement):
        for x in self.get_nodes('file'):
            if self.get_field(x, 'url') == original:
                x['attrs']['url'] = replacement

    def replace_src(self, original, replacement):
        for x in self.get_nodes('image'):
            if self.get_field(x, 'src') == original:
                x['attrs']['src'] = replacement
