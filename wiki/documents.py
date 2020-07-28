from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import Wiki
from core.documents import DefaultDocument, ngram_analyzer


@registry.register_document
class WikiDocument(DefaultDocument):
    id = fields.TextField()
    tags = fields.ListField(fields.TextField())
    read_access = fields.ListField(fields.KeywordField())
    type = fields.KeywordField(attr="type_to_string")
    title = fields.TextField(
        analyzer=ngram_analyzer
    )
    description = fields.TextField(
        analyzer=ngram_analyzer
    )

    class Index:
        name = 'entities'

    class Django:
        model = Wiki

        fields = [
            'created_at',
            'updated_at'
        ]
