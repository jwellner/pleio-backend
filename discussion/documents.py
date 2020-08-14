from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import Discussion
from core.documents import DefaultDocument, custom_analyzer


@registry.register_document
class DiscussionDocument(DefaultDocument):
    id = fields.KeywordField()
    tags = fields.ListField(fields.TextField())
    read_access = fields.ListField(fields.KeywordField())
    type = fields.KeywordField(attr="type_to_string")
    title = fields.TextField(
        analyzer=custom_analyzer,
        search_analyzer="standard",
        boost=2
    )
    description = fields.TextField(
        analyzer=custom_analyzer,
        search_analyzer="standard"
    )

    class Index:
        name = 'discussion'

    class Django:
        model = Discussion

        fields = [
            'created_at',
            'updated_at'
        ]
