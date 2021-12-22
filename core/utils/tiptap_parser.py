import json

class Tiptap:

    def __init__(self, tiptap_json):
        if not tiptap_json:
            self.tiptap_json = {}
        elif isinstance(tiptap_json, str):
            self.tiptap_json = json.loads(tiptap_json)
        else:
            self.tiptap_json = tiptap_json

    @property
    def mentioned_users(self):
        users = set()
        for mention in self.get_nodes('mention'):
            user = mention.get('attrs', {}).get('id', None)
            if user:
                users.add(user)

        return users

    def get_nodes(self, node_type):
        if (self.tiptap_json.get('type', None) == node_type):
            return [self.tiptap_json]

        nodes = []
        for node in self.tiptap_json.get('content', []):
            tiptap = Tiptap(node)
            nodes.extend(tiptap.get_nodes(node_type))

        return nodes
