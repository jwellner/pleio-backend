from ariadne import graphql_sync
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django_tenants.test.cases import FastTenantTestCase
from mixer.backend.django import mixer
from time import sleep

from backend2.schema import schema
from core.constances import USER_ROLES
from core.models import Entity
from core.models.tags import Tag, TagSynonym, EntityTag
from user.models import User


class TestTagsTestCase(FastTenantTestCase):

    def setUp(self):
        super(TestTagsTestCase, self).setUp()

        self.owner = mixer.blend(User)
        self.entity = Entity.objects.create(owner=self.owner, is_archived=False)
        self.entity.tags = ["Tag1", "Tag2"]
        self.entity.save()

        self.tag2 = Tag.objects.get(label='tag2')
        TagSynonym.objects.create(tag=self.tag2, label='tag2.1')
        TagSynonym.objects.create(tag=self.tag2, label='tag2.2')
        TagSynonym.objects.create(tag=self.tag2, label='tag2.3')

    def test_all_matches(self):
        matches = [label for label in self.tag2.all_matches]
        self.assertEqual(4, len(matches))
        self.assertIn('tag2', matches)
        self.assertIn('tag2.1', matches)
        self.assertIn('tag2.2', matches)
        self.assertIn('tag2.3', matches)

    def test_tags_matches(self):
        matches = self.entity.tags_matches
        self.assertEqual(5, len(matches))
        self.assertIn('tag1', matches)
        self.assertIn('tag2', matches)
        self.assertIn('tag2.1', matches)
        self.assertIn('tag2.2', matches)
        self.assertIn('tag2.3', matches)

    def test_set_links_existing_tags(self):
        self.entity.tags = ["Tag1"]
        self.assertEqual(self.entity.tags, ['Tag1'])

    def test_set_synonym_links_existing_tag(self):
        self.entity.tags = ["Tag2.3"]
        self.assertEqual(self.entity.tags, ['Tag2.3'])
        self.assertEqual([t.tag.label for t in EntityTag.objects.filter(entity_id=self.entity.id)], ['tag2'])

    def test_add_links_new_tags(self):
        with self.assertRaises(Tag.DoesNotExist):
            Tag.objects.get(label="new")
        self.entity.tags = ["New"]
        self.entity.save()
        self.assertEqual(self.entity.tags, ['New'])

        tag = Tag.objects.get(label="new")
        self.assertEqual(tag.label, "new")

    def test_ommit_removes_links_to_tags(self):
        self.entity.tags = ["New", "Tag1", "Tag2"]
        self.entity.save()
        self.assertEqual(self.entity.tags, ['New', "Tag1", "Tag2"])
        self.entity.tags = ["New", "Tag1"]
        self.entity.save()
        self.assertEqual(self.entity.tags, ['New', "Tag1"])

    def test_overwrite_tag(self):
        self.entity.tags = ['Tag2']
        self.entity.save()
        self.assertEqual(self.entity.tags, ['Tag2'])

        self.entity.tags = ['Tag2.1']
        self.entity.save()
        self.assertEqual(self.entity.tags, ['Tag2.1'])

        self.entity.tags = ['Tag2', 'Tag2.1']
        self.entity.save()
        self.assertEqual(self.entity.tags, ['Tag2'])

        self.entity.tags = ['Tag2.1', 'Tag2']
        self.entity.save()
        self.assertEqual(self.entity.tags, ['Tag2.1'])


class TestTagAdministrationTestCase(FastTenantTestCase):

    def assertGraphQlErrorMessage(self, errors, expected_message, msg=None):
        if not errors:
            self.fail("Expected %s error message. Got none." % expected_message)
        messages = [e['message'] for e in errors]
        self.assertIn(expected_message, messages, msg=msg or messages)

    def assertGraphQlNoErrors(self, errors, msg=None):
        if errors:
            self.fail(msg or [e['message'] for e in errors])

    def graphql_sync(self, query, variables, user) -> dict:
        request = HttpRequest()
        request.user = user

        success, result = graphql_sync(schema, {'query': query, 'variables': variables},
                                       context_value={'request': request})

        return result

    def graphql_sync_error(self, query, variables, user):
        result = self.graphql_sync(query, variables, user)
        return result.get('errors')

    def setUp(self) -> None:
        self.owner = mixer.blend(User)
        self.admin = mixer.blend(User, roles=[USER_ROLES.ADMIN])
        self.entity = mixer.blend(Entity, owner=self.owner)
        self.entity.tags = ['Tag one', 'Tag1', 'Tag2', 'Tag3']
        self.entity.save()

        TagSynonym.objects.create(label='tag1.1', tag=Tag.objects.get(label='tag1'))
        TagSynonym.objects.create(label='tag.one', tag=Tag.objects.get(label='tag one'))

    def test_list_of_tags(self):
        query = """
        query ListTags {
            tags {
              label
              synonyms
            }
        }
        """

        result = self.graphql_sync(query, None, self.owner)

        self.assertGraphQlNoErrors(result.get('errors'))

        data = result.get("data")
        labels = [tag['label'] for tag in data['tags']]
        self.assertEqual(len(data.get('tags')), 4)
        self.assertIn('tag1', labels)
        self.assertIn('tag2', labels)
        self.assertIn('tag3', labels)
        self.assertIn('tag one', labels)

        labelSynonym = {record['label']: record['synonyms'] for record in data['tags']}
        self.assertEqual(labelSynonym['tag1'], ['tag1.1'])
        self.assertEqual(labelSynonym['tag one'], ['tag.one'])

    def test_merge_tag_restricted_access(self):
        query = """
        mutation ($input: tagMergeInput!) {
            mergeTags(input: $input) {
              __typename
            }
        }
        """

        # authenticated users are not allowed to alter the tags:
        for message, account in [("Content eigenaar heeft onterecht toegang", self.owner),
                                 ("Anonieme bezoeker heeft onterecht toegang", AnonymousUser())]:
            errors = self.graphql_sync_error(query, {
                'input': {
                    'tag': 'tag1',
                    'synonym': 'tag1.1',
                }
            }, account)
            self.assertIsNotNone(errors, msg=message)
            self.assertGraphQlErrorMessage(errors, "Not allowed")

    def test_merge_tag_results_in_one_less_tag(self):
        query = """
        mutation ($input: tagMergeInput!) {
            mergeTags(input: $input) {
                label
                synonyms
            }
        }
        """
        result = self.graphql_sync(query, {
            'input': {
                'tag': 'tag2',
                'synonym': 'tag3',
            }
        }, self.admin)
        self.assertGraphQlNoErrors(result.get('errors'))

        data = result.get('data')
        labelSynonym = {record['label']: record['synonyms'] for record in data['mergeTags']}
        self.assertEqual(len(data.get('mergeTags')), 3, msg=result)
        self.assertEqual(labelSynonym['tag1'], ['tag1.1'])
        self.assertEqual(labelSynonym['tag2'], ['tag3'])
        self.assertEqual(labelSynonym['tag one'], ['tag.one'])

        self.entity.refresh_from_db()
        self.assertEqual(self.entity.tags, ['Tag one', 'Tag1', 'Tag2'], msg="Gevonden tags kloppen niet.")
        # pylint: disable=protected-access
        self.assertEqual(self.entity._tag_summary, ['tag one', 'tag1', 'tag2'], msg="Tag summary klopt niet.")

    def test_merge_tags_preserves_all_synonyms(self):
        query = """
        mutation ($input: tagMergeInput!) {
            mergeTags(input: $input) {
                label
                synonyms
            }
        }
        """
        result = self.graphql_sync(query, {
            'input': {
                'tag': 'tag one',
                'synonym': 'tag1',
            }
        }, self.admin)
        self.assertGraphQlNoErrors(result.get('errors'))

        data = result.get('data')
        labelSynonym = {record['label']: record['synonyms'] for record in data['mergeTags']}
        self.assertEqual(len(labelSynonym['tag one']), 3)
        self.assertIn('tag1', labelSynonym['tag one'])
        self.assertIn('tag1.1', labelSynonym['tag one'])
        self.assertIn('tag.one', labelSynonym['tag one'])

    def test_extract_synonym_restricted_access(self):
        query = """
        mutation ($input: tagMergeInput!) {
            extractTagSynonym(input: $input) {
              __typename
            }
        }
        """
        errors = self.graphql_sync_error(query, {
            'input': {
                'tag': 'tag1',
                'synonym': 'tag1.1',
            }
        }, self.owner)
        self.assertIsNotNone(errors, msg="Gebruiker heeft onterecht toegang.")
        self.assertGraphQlErrorMessage(errors, "Not allowed")

    def test_extract_synonym_results_in_one_extra_tag(self):
        # Start with 4.
        self.assertEqual(4, Tag.objects.count())

        query = """
        mutation ($input: tagMergeInput!) {
            extractTagSynonym(input: $input) {
                label
                synonyms
                __typename
            }
        }
        """
        result = self.graphql_sync(query, {
            'input': {
                'tag': 'tag1',
                'synonym': 'tag1.1',
            }
        }, self.admin)
        self.assertGraphQlNoErrors(result.get('errors'))

        data = result.get('data')
        self.assertEqual(len(data['extractTagSynonym']), 5)

    def test_extract_synonym_restores_tag_references_on_existing_content(self):
        TagSynonym.objects.create(label='tag one', tag=Tag.objects.get(label='tag1'))
        TagSynonym.objects.create(label='tag two', tag=Tag.objects.get(label='tag2'))
        other_entity = mixer.blend(Entity, owner=self.owner)
        other_entity.tags = ['Tag one', 'Tag two']
        other_entity.save()

        self.assertIn("tag2", other_entity._tag_summary)
        self.assertNotIn("tag two", other_entity._tag_summary)
        self.assertEqual(other_entity.tags, ['Tag one', 'Tag two'])

        query = """
        mutation ($input: tagMergeInput!) {
            extractTagSynonym(input: $input) {
                label
                synonyms
                __typename
            }
        }
        """
        result = self.graphql_sync(query, {
            'input': {
                'tag': 'tag2',
                'synonym': 'tag two',
            }
        }, self.admin)
        self.assertGraphQlNoErrors(result.get('errors'))

        other_entity.refresh_from_db()
        self.assertNotIn("tag2", other_entity._tag_summary)
        self.assertIn("tag two", other_entity._tag_summary)
        self.assertEqual(other_entity.tags, ['Tag one', 'Tag two'])
