import uuid

from django_tenants.utils import parse_tenant_config_path

from core.constances import USER_ROLES
from core.models.tags import Tag, TagSynonym, EntityTag
from core.resolvers.query_tags import resolve_list_tags
from core.tasks.elasticsearch_tasks import elasticsaerch_index_document


def resolve_merge_tags(_, info, input):
    # pylint: disable=redefined-builtin
    assert is_admin(info), "Not allowed"
    assert Tag.objects.filter(label=input['tag']).exists(), "Tag does not exist"
    assert Tag.objects.filter(label=input['synonym']).exists(), "Synonym does not exist"

    # 1) Tag(synonym) krijgt een tijdelijke andere naam, om conflicten te voorkomen
    s_tag = Tag.objects.get(label=input['synonym'])
    s_tag.label = str(uuid.uuid4())
    s_tag.save()

    # 2) Synonym(synonym) van Tag(tag)
    tag = Tag.objects.get(label=input['tag'])
    TagSynonym.objects.create(label=input['synonym'], tag=tag)
    for s_synonym in s_tag.synonyms.all():
        s_synonym.tag = tag
        s_synonym.save()

    for ref in EntityTag.objects.filter(tag=s_tag):
        if not EntityTag.objects.filter(entity_id=ref.entity_id, tag=tag).exists():
            # 3) EntityTag's moeten het id van Tag(tag) krijgen
            ref.tag = tag
            ref.save()
        else:
            # 3b) Tag bestaat al op de entity, dan mag deze weg.
            ref.delete()

        # 3c) ... en de _tag_summary moet worden geüpdate
        ref.entity.save()

    s_tag.delete()

    # 4) update de index van alle documenten.
    for ref in EntityTag.objects.filter(tag=tag):
        elasticsaerch_index_document.delay(parse_tenant_config_path(""), ref.entity_id)

    return resolve_list_tags(_, info)


def resolve_extract_tag_synonym(_, info, input):
    # pylint: disable=redefined-builtin
    assert is_admin(info), "Not allowed"
    assert Tag.objects.filter(label=input['tag']).exists(), "Tag does not exist"
    assert TagSynonym.objects.filter(label=input['synonym']).exists(), "Synonym does not exist"

    # 0) Tag waar het synonym in zit, voor updaten van content
    tag = Tag.objects.get(label=input['tag'])

    # 1) Synonym(synonym) wordt opgeheven.
    TagSynonym.objects.filter(label=input['synonym']).delete()

    # 2) Nieuwe Tag(synonym)
    s_tag = Tag.objects.create(label=input['synonym'])

    # 3) EntityTag's met author_label(synonym) krijgen Tag(synonym)
    for ref in EntityTag.objects.filter(author_label__iexact=input['synonym']):
        ref.tag = s_tag
        ref.save()

        # 3b) ... en _tag_summary moet worden geüpdate
        ref.entity.save()

        # 4a) update de index van de gewijzigde documenten.
        elasticsaerch_index_document.delay(parse_tenant_config_path(""), ref.entity_id)

    # 4b) update de index van de andere documenten.
    for ref in EntityTag.objects.filter(tag=tag):
        elasticsaerch_index_document.delay(parse_tenant_config_path(""), ref.entity_id)

    return resolve_list_tags(_, info)


def is_admin(info):
    user = info.context['request'].user
    return user.is_authenticated and user.has_role(USER_ROLES.ADMIN)
