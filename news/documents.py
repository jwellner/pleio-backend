from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import News
from core.documents import DefaultDocument, custom_analyzer


@registry.register_document
class NewsDocument(DefaultDocument):
    id = fields.KeywordField()
    tags = fields.ListField(fields.TextField())
    read_access = fields.ListField(fields.KeywordField())
    type = fields.KeywordField(attr="type_to_string")
    title = fields.TextField(
        analyzer=custom_analyzer
    )
    description = fields.TextField(
        analyzer=custom_analyzer
    )

    class Index:
        name = 'entities'

    class Django:
        model = News

        fields = [
            'created_at',
            'updated_at'
        ]
