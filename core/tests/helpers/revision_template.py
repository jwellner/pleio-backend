from django.utils.timezone import localtime, timedelta

from blog.factories import BlogFactory
from core.factories import GroupFactory
from core.tests.helpers import PleioTenantTestCase
from news.factories import NewsFactory
from user.factories import UserFactory, AdminFactory, EditorFactory


class RevisionTemplate:
    class BaseTestCase(PleioTenantTestCase):
        editMutation = 'editEntity'
        editMutationInput = 'editEntityInput'

        useCommonTests = True
        useAbstract = False
        useIsRecommended = False
        useIsFeatured = False
        useFeatured = False
        useWriteAccess = False
        useTimeCreated = False
        useArchiveDeletePublish = False
        useGroupGuid = False
        useOwnerGuid = False
        useSuggestedItems = False
        useSource = False
        useParent = False

        reference_data = {}

        def assertReferenceUnchanged(self, content, *is_not_reference):
            for key, value in self.reference_data.items():
                if key in is_not_reference:
                    continue
                self.assertEqual(content[key], value)

        def build_entity(self, owner):
            raise NotImplementedError()

        def default_variables(self):
            raise NotImplementedError()

        def build_owner(self):
            raise NotImplementedError()

        def localSetUp(self):
            self.admin = AdminFactory()
            self.owner = self.build_owner()
            self.entity = self.build_entity(self.owner)

            self.mutation = """
            mutation UpdateEntity($input: %s!) {
                %s(input: $input) {
                    entity {
                        guid
                    }
                }
            }
            """ % (self.editMutationInput, self.editMutation)

            self.variables = {
                "input": {
                    "guid": self.entity.guid,
                }
            }

            self.query = """
            query GetRevisions ($guid: String!) {
                revisions(containerGuid: $guid) {
                    edges {
                        container {
                            guid
                        }
                        author {
                            guid
                        }
                        type
                        statusPublishedChanged
                        changedFields
                        content {
                            title
                            featured {
                                video
                                videoTitle
                                image
                                imageGuid
                                positionY
                                alt
                            }
                            abstract
                            richDescription
                            tags
                            tagCategories {
                                name
                                values
                            }
                            suggestedItems {
                                guid
                            }
                            source
                            isRecommended
                            isFeatured
                            group {
                                guid
                            }
                            parent {
                                guid
                            }
                            owner {
                                guid
                            }
                            accessId
                            writeAccessId
                            timeCreated
                            timePublished
                            scheduleArchiveEntity
                            scheduleDeleteEntity
                        }
                    }
                }
            }
            """

        def applyChanges(self, **kwargs):
            assert self.reference_data, "Add two or more fields to test if they are not changed in the process."
            for key, value in self.reference_data.items():
                self.variables['input'][key] = value
            for key, value in kwargs.items():
                self.variables['input'][key] = value
            self.graphql_client.force_login(self.admin)
            self.graphql_client.post(self.mutation, self.variables)

            response = self.graphql_client.post(self.query, {"guid": self.entity.guid})
            return response['data']['revisions']['edges']

        def test_mutate_title(self):
            if not self.useCommonTests:
                return
            self.localSetUp()

            revisions = self.applyChanges(title="new title")
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['title'])
            self.assertEqual(revision['content']['title'], self.variables['input']['title'])
            self.assertEqual(revision['content']['richDescription'], self.variables['input']['richDescription'])
            self.assertEqual(revision['type'], 'update')
            self.assertReferenceUnchanged(revision['content'], 'title')

        def test_mutate_rich_description(self):
            if not self.useCommonTests:
                return
            self.localSetUp()

            revisions = self.applyChanges(richDescription=self.tiptap_paragraph("new rich description"))
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['richDescription'])
            self.assertEqual(revision['content']['richDescription'], self.variables['input']['richDescription'])
            self.assertReferenceUnchanged(revision['content'], 'richDescription')

        def test_mutate_access_id(self):
            if not self.useCommonTests:
                return
            self.localSetUp()

            revisions = self.applyChanges(accessId=0)
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['accessId'])
            self.assertEqual(revision['content']['accessId'], self.variables['input']['accessId'])
            self.assertReferenceUnchanged(revision['content'], 'accessId')

        def test_mutate_write_access_id(self):
            if not self.useWriteAccess:
                return
            self.localSetUp()

            revisions = self.applyChanges(writeAccessId=1)
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['writeAccessId'])
            self.assertEqual(revision['content']['writeAccessId'], self.variables['input']['writeAccessId'])
            self.assertReferenceUnchanged(revision['content'], 'writeAccessId')

        def test_mutate_tags(self):
            if not self.useCommonTests:
                return
            self.localSetUp()

            revisions = self.applyChanges(tags=['Foo', 'Bar', 'Baz'])
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['tags'])
            self.assertEqual(revision['content']['tags'], sorted(self.variables['input']['tags']))
            self.assertReferenceUnchanged(revision['content'], 'tags')

        def test_mutate_tag_categories(self):
            if not self.useCommonTests:
                return
            self.localSetUp()

            revisions = self.applyChanges(tagCategories=[{'name': 'Demo', 'values': ['One', 'Two', 'Three']}])
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['tagCategories'])
            self.assertEqual(revision['content']['tagCategories'], self.variables['input']['tagCategories'])
            self.assertReferenceUnchanged(revision['content'], 'tagCategories')

        def test_mutate_time_created(self):
            if not self.useTimeCreated:
                return
            self.localSetUp()

            new_create_time = localtime() - timedelta(days=2)

            revisions = self.applyChanges(timeCreated=str(new_create_time))
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['timeCreated'])
            self.assertDateEqual(revision['content']['timeCreated'], self.variables['input']['timeCreated'])
            self.assertReferenceUnchanged(revision['content'], 'timeCreated')

        def test_mutate_time_published(self):
            if not self.useArchiveDeletePublish:
                return
            self.localSetUp()
            self.entity.published = None
            self.entity.save()

            revisions = self.applyChanges(timePublished=str(localtime()))
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['timePublished'])
            self.assertDateEqual(revision['content']['timePublished'], self.variables['input']['timePublished'])
            self.assertEqual(revision['statusPublishedChanged'], "published")
            self.assertReferenceUnchanged(revision['content'], 'timePublished')

        def test_mutate_schedule_archive_entity(self):
            if not self.useArchiveDeletePublish:
                return
            self.localSetUp()

            revisions = self.applyChanges(scheduleArchiveEntity=str(localtime()))
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['scheduleArchiveEntity'])
            self.assertEqual(revision['statusPublishedChanged'], "archived")
            self.assertDateEqual(revision['content']['scheduleArchiveEntity'], self.variables['input']['scheduleArchiveEntity'])
            self.assertReferenceUnchanged(revision['content'], 'scheduleArchiveEntity')

        def test_mutate_schedule_delete_entity(self):
            if not self.useArchiveDeletePublish:
                return
            self.localSetUp()

            revisions = self.applyChanges(scheduleDeleteEntity=str(localtime()))
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['scheduleDeleteEntity'])
            self.assertDateEqual(revision['content']['scheduleDeleteEntity'], self.variables['input']['scheduleDeleteEntity'])
            self.assertReferenceUnchanged(revision['content'], 'scheduleDeleteEntity')

        def test_mutate_abstract(self):
            if not self.useAbstract:
                return
            self.localSetUp()

            revisions = self.applyChanges(abstract=self.tiptap_paragraph("new abstract text"))
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['abstract'])
            self.assertEqual(revision['content']['abstract'], self.variables['input']['abstract'])
            self.assertReferenceUnchanged(revision['content'], 'abstract')

        def test_mutate_is_recommended(self):
            if not self.useIsRecommended:
                return
            self.localSetUp()

            revisions = self.applyChanges(isRecommended=True)
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['isRecommended'])
            self.assertEqual(revision['content']['isRecommended'], self.variables['input']['isRecommended'])
            self.assertReferenceUnchanged(revision['content'], 'isRecommended')

        def test_mutate_is_featured(self):
            if not self.useIsFeatured:
                return
            self.localSetUp()

            revisions = self.applyChanges(isFeatured=True)
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['isFeatured'])
            self.assertEqual(revision['content']['isFeatured'], self.variables['input']['isFeatured'])
            self.assertReferenceUnchanged(revision['content'], 'isFeatured')

        def test_mutate_featured_video(self):
            if not self.useFeatured:
                return
            self.localSetUp()

            revisions = self.applyChanges(featured={
                'video': 'https://www.youtube.com/watch?v=FN2RM-CHkuI',
                'videoTitle': "How to write instructions for making a peanutbutter-jelly sandwich"
            })
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['featured'])
            self.assertDictEqual({k: v for k, v in revision['content']['featured'].items() if v}, self.variables['input']['featured'])
            self.assertReferenceUnchanged(revision['content'], 'featured')

        def test_mutate_featured_image(self):
            if not self.useFeatured:
                return

            self.localSetUp()
            file = self.file_factory(self.relative_path(__file__, ['..', 'assets', 'landscape.jpeg']))

            revisions = self.applyChanges(featured={
                'imageGuid': file.guid,
                'alt': "Landscape",
                'positionY': 10,
            })
            self.entity.refresh_from_db()
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['featured'])
            self.assertDictEqual({k: v for k, v in revision['content']['featured'].items() if v}, {
                "alt": "Landscape",
                "imageGuid": file.guid,
                "image": self.entity.featured_image.download_url,
                "positionY": 10,
            })
            self.assertReferenceUnchanged(revision['content'], 'featured')

        def test_mutate_featured_image_twice(self):
            if not self.useFeatured:
                return
            self.localSetUp()
            file1 = self.file_factory(self.relative_path(__file__, ['..', 'assets', 'landscape.jpeg']))
            file2 = self.file_factory(self.relative_path(__file__, ['..', 'assets', 'landscape.jpeg']))

            self.applyChanges(title="First mutation",
                              featured={
                                  'imageGuid': file1.guid,
                                  'alt': "Landscape 1",
                              })
            revisions = self.applyChanges(title="Second mutation",
                                          featured={
                                              'imageGuid': file2.guid,
                                              'alt': "Landscape 2",
                                          })
            self.assertNotEqual(revisions[0]['content']['featured']['imageGuid'], revisions[1]['content']['featured']['imageGuid'])
            self.assertNotEqual(revisions[0]['content']['featured']['image'], revisions[1]['content']['featured']['image'])

        def test_mutate_group_guid(self):
            if not self.useGroupGuid:
                return
            self.localSetUp()
            group = GroupFactory(owner=self.admin)

            revisions = self.applyChanges(groupGuid=group.guid)
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['groupGuid'])
            left = revision['content']['group']['guid'] if revision['content'].get('group') else None
            right = self.variables['input']['groupGuid']
            self.assertEqual(left, right)
            self.assertReferenceUnchanged(revision['content'], 'groupGuid')

        def test_mutate_owner_guid(self):
            if not self.useOwnerGuid:
                return
            self.localSetUp()
            new_owner = UserFactory()

            revisions = self.applyChanges(ownerGuid=new_owner.guid)
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['ownerGuid'])
            left = revision['content']['owner']['guid'] if revision['content'].get('owner') else None
            right = self.variables['input']['ownerGuid']
            self.assertEqual(left, right)
            self.assertReferenceUnchanged(revision['content'], 'ownerGuid')

        def test_mutate_suggested_items(self):
            if not self.useSuggestedItems:
                return
            self.localSetUp()

            related_blog = BlogFactory(owner=self.owner)
            related_news = NewsFactory(owner=EditorFactory())

            revisions = self.applyChanges(suggestedItems=[
                related_blog.guid,
                related_news.guid,
            ])
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['suggestedItems'])
            self.assertListEqual([item['guid'] for item in revision['content']['suggestedItems']], self.variables['input']['suggestedItems'])
            self.assertReferenceUnchanged(revision['content'], 'suggestedItems')

        def test_mutate_source(self):
            if not self.useSource:
                return
            self.localSetUp()

            revisions = self.applyChanges(source="New source description")
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['source'])
            self.assertEqual(revision['content']['source'], self.variables['input']['source'])
            self.assertReferenceUnchanged(revision['content'], 'source')

        def test_mutate_parent(self):
            if not self.useParent:
                return
            self.localSetUp()

            container = self.build_entity(self.owner)

            self.localSetUp()
            revisions = self.applyChanges(containerGuid=container.guid)
            self.assertEqual(len(revisions), 1)

            revision = revisions[0]
            self.assertEqual(revision['author']['guid'], self.admin.guid)
            self.assertEqual(revision['changedFields'], ['containerGuid'])
            self.assertEqual(revision['content']['parent']['guid'], self.variables['input']['containerGuid'])
            self.assertReferenceUnchanged(revision['content'], 'containerGuid')
