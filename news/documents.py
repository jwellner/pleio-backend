from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import News
from core.documents import DefaultDocument


@registry.register_document
class NewsDocument(DefaultDocument):
    id = fields.KeywordField()
    tags = fields.ListField(fields.TextField())
    read_access = fields.ListField(fields.KeywordField())
    type = fields.KeywordField(attr="type_to_string")

    class Index:
        name = 'entities'

    class Django:
        model = News

        fields = [
            'title',
            'description',
            'created_at',
            'updated_at'
        ]
