from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import Event
from core.models import Comment
from core.documents import DefaultDocument, custom_analyzer


@registry.register_document
class EventDocument(DefaultDocument):
    id = fields.KeywordField()
    tags = fields.ListField(fields.TextField())
    read_access = fields.ListField(fields.KeywordField())
    type = fields.KeywordField(attr="type_to_string")
    title = fields.TextField(
        analyzer=custom_analyzer,
        search_analyzer="standard",
        boost=2,
        fields={'raw': fields.KeywordField()}
    )
    description = fields.TextField(
        analyzer=custom_analyzer,
        search_analyzer="standard"
    )
    comments = fields.ObjectField(properties={
        'description': fields.TextField(analyzer=custom_analyzer, search_analyzer="standard")
    })

    def get_instances_from_related(self, related_instance):
        return related_instance.container

    class Index:
        name = 'event'

    class Django:
        model = Event

        fields = [
            'created_at',
            'updated_at',
            'published'
        ]

        related_models = [Comment]
