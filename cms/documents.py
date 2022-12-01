from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import Page
from core.documents import DefaultDocument, custom_analyzer
from core.utils.convert import tiptap_to_text


@registry.register_document
class CmsDocument(DefaultDocument):
    id = fields.KeywordField()
    is_archived = fields.BooleanField()
    tags = fields.ListField(fields.TextField(
        fields={'raw': fields.KeywordField()}
    ))
    tags_matches = fields.ListField(fields.TextField(
        fields={'raw': fields.KeywordField()}
    ))
    category_tags = fields.ListField(fields.KeywordField(attr='category_tags_index'))

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

    def prepare_description(self, instance):
        return tiptap_to_text(instance.rich_description)

    def prepare_tags(self, instance):
        return [x.lower() for x in instance.tags]

    def get_queryset(self):
        return super().get_queryset().filter(page_type='text')

    def should_index_object(self, obj):
        return obj.page_type == 'text'

    class Index:
        name = 'page'

    class Django:
        model = Page

        fields = [
            'created_at',
            'updated_at',
            'published'
        ]
