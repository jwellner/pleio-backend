from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django_tenants.utils import parse_tenant_config_path
from elasticsearch_dsl import analysis, analyzer

from .lib import is_schema_public
from .models.user import UserProfile, UserProfileField
from .models.group import Group, GroupMembership
from user.models import User
from core.utils.convert import tiptap_to_text

custom_asciifolding_filter = analysis.token_filter(
    "custom_asciifolding_filter",
    type="asciifolding",
    preserve_original=True
)

custom_edge_ngram_filter = analysis.token_filter(
    "custom_edge_ngram_filter",
    type="edge_ngram",
    min_gram=1,
    max_gram=30
)

custom_analyzer = analyzer(
    'custom_analyzer',
    tokenizer='standard',
    type='custom',
    filter=['lowercase', custom_asciifolding_filter, custom_edge_ngram_filter]
)


class DefaultDocument(Document):
    tenant_name = fields.KeywordField()
    owner_guid = fields.KeywordField()
    container_guid = fields.KeywordField()

    def prepare_tenant_name(self, instance):
        # pylint: disable=unused-argument
        return parse_tenant_config_path("")

    def prepare_owner_guid(self, instance):
        if hasattr(instance, 'owner') and instance.owner:
            return instance.owner.id

        return ""

    def prepare_container_guid(self, instance):
        if hasattr(instance, 'group') and instance.group:
            return instance.group.id

        return ""

    def prepare_title(self, instance):
        return instance.title.lower() if hasattr(instance, 'title') and instance.title else ''



@registry.register_document
class UserDocument(DefaultDocument):
    id = fields.KeywordField()
    is_archived = fields.BooleanField()
    type = fields.KeywordField(attr="type_to_string")
    read_access = fields.ListField(fields.TextField(attr="search_read_access"))
    is_active = fields.BooleanField()
    name = fields.TextField(
        analyzer=custom_analyzer,
        search_analyzer="standard",
        boost=5,
        fields={'raw': fields.KeywordField()}
    )
    external_id = fields.KeywordField()

    user_profile_fields = fields.NestedField(
        attr='_profile.user_profile_fields',
        properties={
            'value': fields.TextField(
                attr='value_field_indexing',
                fields={'raw': fields.KeywordField()}
            ),
            'name': fields.KeywordField(),
            'key': fields.KeywordField(),
            'read_access': fields.ListField(fields.TextField(attr="read_access")),
            'value_list': fields.ListField(fields.KeywordField(attr="value_list_field_indexing"))
        }
    )

    last_online = fields.DateField()

    memberships = fields.NestedField(properties={
        'group_id': fields.KeywordField(attr='group.id'),
        'type': fields.KeywordField(),
        'admin_weight': fields.IntegerField(),
    })

    def prepare_last_online(self, instance):
        return instance.profile.last_online

    def prepare_is_archived(self, instance):
        return not instance.is_active

    class Index:
        name = 'user'

    class Django:
        model = User

        fields = [
            'email',
            'created_at',
            'updated_at'
        ]

        related_models = [UserProfile, UserProfileField, GroupMembership]

    def get_instances_from_related(self, related_instance):
        """From Django dsl docs: If related_models is set, define how to retrieve the UserProfile instance(s) from the related model.
        The related_models option should be used with caution because it can lead in the index
        to the updating of a lot of items.
        """
        if isinstance(related_instance, UserProfile):
            return related_instance.user

        if isinstance(related_instance, GroupMembership):
            return related_instance.user

        return related_instance.user_profile.user

    def get_queryset(self):
        if is_schema_public():
            return super().get_queryset().none()
        return super().get_queryset().filter(is_superadmin=False)

    def should_index_object(self, obj):
        if is_schema_public():
            return False
        return not getattr(obj, 'is_superadmin', False)


@registry.register_document
class GroupDocument(DefaultDocument):
    id = fields.KeywordField()
    is_archived = fields.BooleanField()
    tags = fields.ListField(fields.TextField(
        fields={'raw': fields.KeywordField()}
    ))
    tags_matches = fields.ListField(fields.TextField(
        fields={'raw': fields.KeywordField()}
    ))
    category_tags = fields.ListField(fields.KeywordField(attr='category_tags_index'))

    type = fields.KeywordField(attr="type_to_string")
    read_access = fields.ListField(fields.TextField(attr="search_read_access"))
    name = fields.TextField(
        analyzer=custom_analyzer,
        search_analyzer="standard",
        boost=2
    )
    description = fields.TextField(
        analyzer=custom_analyzer,
        search_analyzer="standard"
    )
    introduction = fields.TextField(
        analyzer=custom_analyzer,
        search_analyzer="standard"
    )

    def prepare_is_archived(self, instance):
        # pylint: disable=unused-argument
        return False

    def prepare_description(self, instance):
        return tiptap_to_text(instance.rich_description)

    def prepare_tags(self, instance):
        return [x.lower() for x in instance.tags]

    class Index:
        name = 'group'

    class Django:
        model = Group

        fields = [
            'created_at',
            'updated_at'
        ]
