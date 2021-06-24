from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import Blog
from core.documents import DefaultDocument, custom_analyzer


@registry.register_document
class BlogDocument(DefaultDocument):
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

    class Index:
        name = 'blog'

    class Django:
        model = Blog

        fields = [
            'created_at',
            'updated_at',
            'published'
        ]
