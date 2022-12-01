from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry
from .models import Question
from core.models import Comment
from core.documents import DefaultDocument, custom_analyzer
from core.utils.convert import tiptap_to_text


@registry.register_document
class QuestionDocument(DefaultDocument):
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
    comments = fields.ObjectField(properties={
        'description': fields.TextField(analyzer=custom_analyzer, search_analyzer="standard")
    })

    def get_instances_from_related(self, related_instance):
        root_container = related_instance.get_root_container()
        if isinstance(related_instance, Comment) and isinstance(root_container, Question):
            return root_container
        return None

    def prepare_description(self, instance):
        return tiptap_to_text(instance.rich_description)

    def prepare_comments(self, instance):
        return list(map(lambda comment: {"description": tiptap_to_text(comment.rich_description)}, list(instance.get_flat_comment_list())))

    def prepare_tags(self, instance):
        return [x.lower() for x in instance.tags]

    class Index:
        name = 'question'

    class Django:
        model = Question

        fields = [
            'created_at',
            'updated_at',
            'published'
        ]

        related_models = [Comment]
