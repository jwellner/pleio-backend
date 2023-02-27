import json
import logging
from urllib.parse import urlparse
from django.db import connection
from django.core.exceptions import ValidationError
from core.lib import get_base_url

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
    
    def replace_attachment(self, original_uuid, replacement_uuid):
        for x in self.get_nodes('file'):
            if self.get_field(x, 'url') and str(original_uuid) in self.get_field(x, 'url'):
                x['attrs']['url'] = '/attachment/%s' % str(replacement_uuid)
        for x in self.get_nodes('image'):
            if self.get_field(x, 'src') and str(original_uuid) in self.get_field(x, 'src'):
                x['attrs']['src'] = '/attachment/%s' % str(replacement_uuid)

    def check_for_external_urls(self):
        local_domain = ''
        try:
            local_domain = connection.tenant.get_primary_domain().domain
        except Exception:
            pass

        content = self.tiptap_json.get("content", [])

        for item in content:
            if item.get("type") == "file":
                url = item.get("attrs", {}).get("url", "")
            elif item.get("type") == "image":
                url = item.get("attrs", {}).get("src", "")
            else:
                continue

            netloc = urlparse(url).netloc
            if netloc and netloc != local_domain:
                raise ValidationError(f"Invalid external file or image URL: {url}")
