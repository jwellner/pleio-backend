from django.db.models import Q
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django_tenants.utils import parse_tenant_config_path
from elasticsearch_dsl import analysis, analyzer
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
    container_guid = fields.KeywordField()

    def prepare_tenant_name(self, instance):
        # pylint: disable=unused-argument
        return parse_tenant_config_path("")

    def prepare_container_guid(self, instance):
        if hasattr(instance, 'group') and instance.group:
            return instance.group.id

        return ""


@registry.register_document
class UserDocument(DefaultDocument):
    id = fields.KeywordField()
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

    profile = fields.ObjectField(properties={
        "user_profile_fields": fields.ObjectField(properties={
            'key': fields.KeywordField(),
            'name': fields.KeywordField(),
            'value': fields.TextField(analyzer=custom_analyzer,
                                      fields={'raw': fields.KeywordField()}),
            'value_date': fields.DateField(),
            'value_list': fields.ListField(fields.KeywordField()),
            'read_access': fields.ListField(fields.KeywordField()),
        })
    })

    last_online = fields.DateField()

    memberships = fields.NestedField(properties={
        'group_id': fields.KeywordField(attr='group.id'),
        'type': fields.KeywordField(),
        'admin_weight': fields.IntegerField(),
    })

    def prepare_last_online(self, instance):
        return instance.profile.last_online

    def prepare_profile(self, instance):
        return {"user_profile_fields": [{'key': f.key,
                                         'name': f.name,
                                         'value': f.value_field_indexing,
                                         'value_date': f.value_date,
                                         'value_list': f.value_list_field_indexing,
                                         'read_access': f.read_access} for f in
                                        instance.profile.user_profile_fields.all()
                                        ]}

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


@registry.register_document
class GroupDocument(DefaultDocument):
    id = fields.KeywordField()
    tags = fields.ListField(fields.TextField(
        fields={'raw': fields.KeywordField()}
    ))
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
