from django.conf import settings
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import Blog


@registry.register_document
class BlogDocument(Document):
    id = fields.StringField()
    tags = fields.ListField(fields.StringField())
    read_access = fields.ListField(fields.StringField())
    type = fields.TextField(attr="type_to_string")

    class Index:
        name = settings.ELASTICSEARCH_INDEX

    class Django:
        model = Blog
        
        fields = [
            'title',
            'description',
            'created_at',
            'updated_at'
        ]
