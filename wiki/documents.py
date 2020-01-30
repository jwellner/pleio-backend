from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import Wiki
from core.documents import DefaultDocument


@registry.register_document
class WikiDocument(DefaultDocument):
    id = fields.StringField()
    tags = fields.ListField(fields.StringField())
    read_access = fields.ListField(fields.StringField())
    type = fields.KeywordField(attr="type_to_string")

    class Index:
        name = 'entities'

    class Django:
        model = Wiki
        
        fields = [
            'title',
            'description',
            'created_at',
            'updated_at'
        ]
