from django.utils import timezone
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import A, Q, Search

from core.constances import SEARCH_ORDER_BY
from core.lib import get_acl, tenant_schema
from core.models import Tag
from core.models.tags import flat_category_tags


def delete_document_if_found(uuid):
    for index in registry.get_indices():
        result = index.search().filter(Q("term", id=uuid)).execute()
        if result:
            result[0].delete()


class QueryBuilder():

    def __init__(self, q, user, date_from, date_to):
        self.s = Search(index='_all').query(
            Q('simple_query_string', query=q, fields=[
                'title^3',
                'name^3',
                'email',
                'description',
                'tags_matches^3',
                'file_contents',
                'introduction',
                'comments.description',
                'owner.name'
            ]
              )
            | Q('nested', path='user_profile_fields', ignore_unmapped=True, query=Q('bool', must=[
                Q('match', user_profile_fields__value=q),
                Q('terms', user_profile_fields__read_access=list(get_acl(user)))
            ]))
        ).filter(
            'terms', read_access=list(get_acl(user))
        ).filter(
            'term', tenant_name=tenant_schema()
        ).filter(
            'range', created_at={'gte': date_from, 'lte': date_to}
        ).exclude(
            'term', is_active=False
        ).query('bool', filter=[
            Q('range', published={'gt': None, 'lte': timezone.now()}) |
            Q('terms', type=['group', 'user'])
        ])

    def maybe_filter_owners(self, owner_guids):
        if owner_guids:
            self.s = self.s.filter('terms', owner_guid=owner_guids)

    def maybe_filter_subtypes(self, subtypes):
        if subtypes:
            self.s = self.s.query('terms', type=subtypes)

    def maybe_filter_container(self, container_guid):
        # Filter on container_guid (group.guid)
        if container_guid:
            self.s = self.s.filter('term', container_guid=container_guid)

    def maybe_filter_tags(self, tags, strategy):
        if tags:
            tags_matches = list(Tag.translate_tags(tags))
            if strategy == 'any':
                self.s = self.s.filter('terms', tags_matches=tags_matches)
            else:
                for tag in tags_matches:
                    self.s = self.s.filter('terms', tags_matches=[tag])

    def maybe_filter_categories(self, categories, strategy):
        if categories:
            for category in categories:
                matches = [*flat_category_tags(category)]
                if matches:
                    if strategy != 'all':
                        # Categories: match-any
                        self.s = self.s.filter(
                            'terms', category_tags=matches
                        )
                    else:
                        # match-all
                        for single_match in matches:
                            self.s = self.s.filter(
                                'terms', category_tags=[single_match]
                            )

    def filter_archived(self, filter_archived):
        self.s = self.s.filter('term', is_archived=bool(filter_archived))

    def order_by(self, sort_order, direction):
        if sort_order == SEARCH_ORDER_BY.title:
            self.s = self.s.sort({'title.raw': {'order': direction}})
        elif sort_order == SEARCH_ORDER_BY.timeCreated:
            self.s = self.s.sort({'created_at': {'order': direction}})
        elif sort_order == SEARCH_ORDER_BY.timePublished:
            self.s = self.s.sort({'published': {'order': direction}})

    def add_aggregation(self):
        a = A('terms', field='type')
        self.s.aggs.bucket('type_terms', a)
