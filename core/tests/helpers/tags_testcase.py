from django.utils.timezone import localtime
from mixer.backend.django import mixer

from core.constances import ACCESS_TYPE
from core.models import Tag
from core.tests.helpers import PleioTenantTestCase, ElasticsearchTestCase
from core.utils.entity import load_entity_by_id
from user.factories import UserFactory
from user.models import User


def get_edges(data):
    if len(data.get('edges', [])) == 0:
        return []

    if not data['edges'][0].get('guid'):
        if data['edges'][0].get('entity'):
            return [edge['entity'] for edge in data['edges']]

    return data['edges']


class Template:
    # Q: Why the 'Base' wrapper?
    # A: To prevent this class to be executed without context.

    class TagsTestCaseTemplate(PleioTenantTestCase):
        graphql_payload = 'entity'
        graphql_update_mutation = 'editEntity'
        graphql_update_input = 'editEntityInput'
        graphql_add_mutation = 'addEntity'
        graphql_add_input = 'addEntityInput'
        graphql_label = None
        variables_add = {}
        model = None

        include_add_edit = True
        include_site_search = False
        include_entity_search = False
        include_activity_search = False
        include_group_search = False

        TAG_CATEGORIES = [
            {
                'name': "Fruit",
                'values': [
                    'Apple',
                    'Banana'
                    'Grape',
                    'Orange',
                ]
            },
            {
                'name': "Verdict",
                'values': [
                    'Excellent',
                    'Fine',
                    'Mediocre',
                ]
            },
        ]

        def article_factory(self, owner: User, **kwargs):
            kwargs['owner'] = owner
            kwargs.setdefault('published', localtime())
            kwargs.setdefault('read_access', [ACCESS_TYPE.logged_in])
            kwargs.setdefault('write_access', [ACCESS_TYPE.user.format(owner.guid)])
            return mixer.blend(self.model, **kwargs)

        def owner_factory(self):
            return UserFactory(email="owner@localhost")

        def local_setup(self):
            assert self.graphql_label, "Please fill in the object name for this model in the graphql schema"

            self.owner = self.owner_factory()

            self.article1 = self.article_factory(self.owner,
                                                 title="First article",
                                                 tags=["Foo", "Bar"],
                                                 category_tags=[
                                                     {"name": "Fruit", "values": ["Apple", "Grape"]},
                                                     {"name": "Verdict", "values": ["Mediocre"]},
                                                 ])

            self.article2 = self.article_factory(self.owner,
                                                 title="Second article",
                                                 tags=['Bar', 'Baz'],
                                                 category_tags=[
                                                     {"name": "Fruit", "values": ["Banana", "Grape"]},
                                                     {"name": "Verdict", "values": ["Excellent", "Fine"]},
                                                 ])

            self.article3 = self.article_factory(self.owner,
                                                 title='Never found')

            self.mutation_add = """
            mutation AddEntity($input: %s!) {
                %s(input: $input) {
                    %s {
                        ... on %s {
                            guid
                            tags,
                            tagCategories {
                                name
                                values
                            }
                        }
                    }
                }
            }
            """ % (self.graphql_add_input,
                   self.graphql_add_mutation,
                   self.graphql_payload,
                   self.graphql_label)

            self.mutation_update = """
            mutation UpdateEntity($input: %s!) {
                %s(input: $input) {
                    %s {
                        ... on %s {
                            guid
                            tags,
                            tagCategories {
                                name
                                values
                            }
                        }
                    }
                }
            }
            """ % (self.graphql_update_input,
                   self.graphql_update_mutation,
                   self.graphql_payload,
                   self.graphql_label)

            self.article = self.article_factory(self.owner)
            self.variables_update = {
                'input': {
                    'guid': self.article.guid,
                    'tags': ['Foo', 'Baz'],
                    'tagCategories': [
                        {'name': "Fruit",
                         'values': ["Apple"]},
                        {'name': "Verdict",
                         'values': ["Excellent"]}
                    ]
                }
            }

        def get_query_search(self):
            return """
            query IncludeSiteSearch($tags: [String], $categories: [TagCategoryInput], $matchStrategy: MatchStrategy) {
                search(tags: $tags, tagCategories: $categories, matchStrategy: $matchStrategy) {
                    total
                    edges {
                        ... on %s {
                            guid
                        }
                    }
                }
            }
            """ % self.graphql_label

        def get_query_entity(self):
            return """
            query IncludeEntitySearch($tags: [String], $categories: [TagCategoryInput], $matchStrategy: MatchStrategy) {
                entities(tags: $tags, tagCategories: $categories, matchStrategy: $matchStrategy) {
                    total
                    edges {
                        ... on %s {
                            guid
                        }
                    }
                }
            }
            """ % self.graphql_label

        def get_query_activity(self):
            return """
            query IncludeActvityStream($tags: [String], $categories: [TagCategoryInput], $matchStrategy: MatchStrategy) {
                activities(tags: $tags, tagCategories: $categories, matchStrategy: $matchStrategy) {
                    total
                    edges {
                        entity {
                            ... on %s {
                                guid
                            }
                        }
                    }
                }
            }
            """ % self.graphql_label

        def get_query_group(self):
            return """
            query Groups ($tags: [String], $categories: [TagCategoryInput], $matchStrategy: MatchStrategy){
                groups(tags: $tags, tagCategories: $categories, matchStrategy: $matchStrategy) {
                    total
                    edges {
                        guid
                    }
                }
            }
            """

        def test_add_with_tags(self):
            if not self.include_add_edit:
                return

            self.local_setup()
            assert self.variables_add, "Provide self.variables_add where input contains sane defaults, similar to the article_factory method."

            self.variables_add['input']['tags'] = ['Foo']
            self.variables_add['input']['tagCategories'] = [
                {"name": "Fruit", "values": ["Apple", "Grape"]},
                {"name": "Verdict", "values": ["Mediocre"]}
            ]

            self.graphql_client.force_login(self.owner)
            response = self.graphql_client.post(self.mutation_add, self.variables_add)
            entity = response['data'][self.graphql_add_mutation][self.graphql_payload]
            self.assertIsNotNone(entity['guid'])

            created_entity = load_entity_by_id(entity['guid'], [self.model])
            self.assertEqual(created_entity.tags, self.variables_add['input']['tags'])
            self.assertEqual(created_entity.category_tags, self.variables_add['input']['tagCategories'])

            self.assertEqual(entity['tags'], self.variables_add['input']['tags'])
            self.assertEqual(entity['tagCategories'], self.variables_add['input']['tagCategories'])

        def test_update_tags(self):
            if not self.include_add_edit:
                return
            self.local_setup()

            self.graphql_client.force_login(self.owner)
            response = self.graphql_client.post(self.mutation_update, self.variables_update)

            entity = response['data'][self.graphql_update_mutation][self.graphql_payload]
            self.assertEqual(entity['guid'], self.article.guid)

            self.article.refresh_from_db()
            self.assertEqual(self.article.tags, self.variables_update['input']['tags'])
            self.assertEqual(self.article.category_tags, self.variables_update['input']['tagCategories'])

            self.assertEqual(entity['tags'], self.variables_update['input']['tags'])
            self.assertEqual(entity['tagCategories'], self.variables_update['input']['tagCategories'])

        def iterate_query_search(self):
            if self.include_site_search:
                ElasticsearchTestCase.initialize_index()
                yield self.get_query_search(), "search", "query.search"
            if self.include_entity_search:
                yield self.get_query_entity(), "entities", "query.entities"
            if self.include_activity_search:
                yield self.get_query_activity(), "activities", "query.activities"
            if self.include_group_search:
                yield self.get_query_group(), "groups", "query.groups"

        def test_search_by_tag(self):
            self.local_setup()
            self.graphql_client.force_login(self.owner)

            for query, data_key, message in self.iterate_query_search():
                variables = {
                    'tags': ['Foo', 'Bar']
                }

                response = self.graphql_client.post(query, variables)
                edges = get_edges(response['data'][data_key])
                self.assertEqual(2, response['data'][data_key]['total'], msg="Unexpectedly not found exactly two matches at %s" % message)
                self.assertIn(self.article1.guid, [e['guid'] for e in edges], msg="Unexpectedly not found article1 at %s" % message)
                self.assertIn(self.article2.guid, [e['guid'] for e in edges], msg="Unexpectedly not found article2 at %s" % message)

                variables['matchStrategy'] = 'all'
                response = self.graphql_client.post(query, variables)
                edges = get_edges(response['data'][data_key])
                self.assertEqual(1, response['data'][data_key]['total'], msg="Unexpectedly not found exactly two matches at %s" % message)
                self.assertIn(self.article1.guid, [e['guid'] for e in edges], msg="Unexpectedly not found article1 at %s" % message)

        def test_search_by_incomplete_category(self):
            self.local_setup()
            self.graphql_client.force_login(self.owner)

            for query, data_key, message in self.iterate_query_search():
                variables = {
                    'categories': [{'name': 'Fruit', 'values': []}]
                }

                response = self.graphql_client.post(query, variables)
                guids = [e['guid'] for e in get_edges(response['data'][data_key]) if e.get('guid')]
                self.assertEqual(4, len(guids), msg="Unexpectedly not found exactly two matches at %s" % message)
                self.assertIn(self.article.guid, guids, msg="Unexpectedly not found article at %s" % message)
                self.assertIn(self.article1.guid, guids, msg="Unexpectedly not found article1 at %s" % message)
                self.assertIn(self.article2.guid, guids, msg="Unexpectedly not found article2 at %s" % message)
                self.assertIn(self.article3.guid, guids, msg="Unexpectedly not found article3 at %s" % message)

        def test_search_entity_by_category(self):
            self.local_setup()
            self.graphql_client.force_login(self.owner)

            for query, data_key, message in self.iterate_query_search():
                variables = {
                    'categories': [{'name': 'fruit', 'values': ['apple', 'grape']}]
                }
                response = self.graphql_client.post(query, variables)
                edges = [e['guid'] for e in get_edges(response['data'][data_key])]
                self.assertEqual(2, response['data'][data_key]['total'], msg="Unexpectedly not found exactly two matches at %s" % message)
                self.assertIn(self.article1.guid, edges, msg="Unexpectedly not found article1 at %s" % message)
                self.assertIn(self.article2.guid, edges, msg="Unexpectedly not found article2 at %s" % message)

                variables['matchStrategy'] = 'any'
                response = self.graphql_client.post(query, variables)
                edges = [e['guid'] for e in get_edges(response['data'][data_key])]
                self.assertEqual(2, response['data'][data_key]['total'], msg="Unexpectedly not found exactly two matches at %s" % message)
                self.assertIn(self.article1.guid, edges, msg="Unexpectedly not found article1 at %s" % message)
                self.assertIn(self.article2.guid, edges, msg="Unexpectedly not found article2 at %s" % message)

                variables['matchStrategy'] = 'all'
                response = self.graphql_client.post(query, variables)
                edges = get_edges(response['data'][data_key])
                self.assertEqual(1, response['data'][data_key]['total'], msg="Unexpectedly not found exactly one match at %s" % message)
                self.assertEqual(self.article1.guid, edges[0]['guid'], msg="Unexpectedly not found article1 at %s" % message)

        def test_search_tags_overflow(self):
            self.local_setup()
            self.graphql_client.force_login(self.owner)

            for query, data_key, message in self.iterate_query_search():
                # testing that 'tags' uses match-all
                variables = {
                    'tags': ['Foo',
                             'Acme'],
                    'matchStrategy': 'all'
                }
                response = self.graphql_client.post(query, variables)
                edges = get_edges(response['data'][data_key])
                self.assertEqual(0, response['data'][data_key]['total'], msg="Unexpectedly found articles at %s" % message)
                self.assertEqual(0, len(edges), msg="Unexpectedly found articles at %s" % message)

                variables['matchStrategy'] = 'any'
                response = self.graphql_client.post(query, variables)
                edges = get_edges(response['data'][data_key])
                self.assertEqual(1, response['data'][data_key]['total'], msg="Unexpectedly not found exactly one match at %s" % message)
                self.assertEqual(self.article1.guid, edges[0]['guid'], msg="Unexpectedly not found article1 at %s" % message)

        def test_search_categories_overflow(self):
            self.local_setup()
            self.graphql_client.force_login(self.owner)

            # testing that 'tagsList' uses match-any
            for query, data_key, message in self.iterate_query_search():
                variables = {
                    'categories': [
                        {'name': 'fruit', 'values': ['apple', 'not a fruit']},
                    ],
                    'matchStrategy': 'all'
                }
                response = self.graphql_client.post(query, variables)
                edges = get_edges(response['data'][data_key])
                self.assertEqual(0, response['data'][data_key]['total'], msg="Unexpectedly found articles at %s" % message)
                self.assertEqual(0, len(edges), msg="Unexpectedly found articles at %s" % message)

                variables['matchStrategy'] = 'any'
                response = self.graphql_client.post(query, variables)
                edges = get_edges(response['data'][data_key])
                self.assertEqual(1, response['data'][data_key]['total'], msg="Unexpectedly not found exactly one match at %s" % message)
                self.assertEqual(self.article1.guid, edges[0]['guid'], msg="Unexpectedly not found article1 at %s" % message)

        def test_tag_properties(self):
            self.local_setup()

            # pylint: disable=protected-access
            tag_with_synonyms = Tag.objects.get(label=self.article1._tag_summary[0])
            tag_with_synonyms.synonyms.create(label="foobar")

            self.assertEqual(["Foo", "Bar"], self.article1.tags)
            self.assertEqual(["apple", 'bar', 'foo', 'foobar', 'grape', 'mediocre'], sorted(self.article1.tags_matches))
            self.assertEqual(["apple (fruit)", "grape (fruit)", "mediocre (verdict)"], [t for t in self.article1.category_tags_index])
