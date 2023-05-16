from django.db import connection
from django.core.cache import cache
from core.models import Comment
from core.tests.helpers import PleioTenantTestCase, override_config
from user.models import User
from question.models import Question
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE
from django.utils.text import slugify


class QuestionTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = mixer.blend(User)

        self.questionPublic = Question.objects.create(
            title="Test public question",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_closed=False
        )


        self.questionPrivate = Question.objects.create(
            title="Test private question",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_closed=False,
            is_featured=True
        )

        self.comment1 = mixer.blend(Comment, container=self.questionPrivate)
        self.comment2 = mixer.blend(Comment, container=self.questionPrivate)
        self.comment3 = mixer.blend(Comment, container=self.questionPrivate)

        self.questionPrivate.best_answer = self.comment2
        self.questionPrivate.save()

        self.query = """
            fragment QuestionParts on Question {
                title
                richDescription
                accessId
                timeCreated
                timePublished
                scheduleArchiveEntity
                scheduleDeleteEntity
                featured {
                    image
                    video
                    videoTitle
                    positionY
                }
                canEdit
                tags
                url
                views
                votes
                hasVoted
                isBookmarked
                isFollowing
                isFeatured
                isClosed
                canBookmark
                canComment
                canChooseBestAnswer
                comments {
                    guid
                    richDescription
                    isBestAnswer
                    canEdit
                    timeCreated
                    hasVoted
                    votes
                }
                owner {
                    guid
                }
                group {
                    guid
                }
                isLocked
            }
            query GetQuestion($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...QuestionParts
                }
            }
        """

    def tearDown(self):
        cache.clear()
        super().tearDown()

    @override_config(QUESTIONER_CAN_CHOOSE_BEST_ANSWER=True)
    def test_question_anonymous(self):
        variables = {
            "guid": self.questionPublic.guid
        }

        result = self.graphql_client.post(self.query, variables)

        entity = result['data']['entity']
        self.assertEqual(entity["guid"], self.questionPublic.guid)
        self.assertEqual(entity["title"], self.questionPublic.title)
        self.assertEqual(entity["richDescription"], self.questionPublic.rich_description)
        self.assertEqual(entity["accessId"], 2)
        self.assertEqual(entity["timeCreated"], self.questionPublic.created_at.isoformat())
        self.assertEqual(entity["isClosed"], self.questionPublic.is_closed)
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["views"], 0)
        self.assertEqual(entity["votes"], 0)
        self.assertEqual(entity["hasVoted"], False)
        self.assertEqual(entity["isBookmarked"], False)
        self.assertEqual(entity["isFollowing"], False)
        self.assertEqual(entity["isFeatured"], False)
        self.assertEqual(entity["canBookmark"], False)
        self.assertEqual(entity["canEdit"], False)
        self.assertEqual(entity["canComment"], False)
        self.assertEqual(entity["isLocked"], False)
        self.assertEqual(entity["canChooseBestAnswer"], False)
        self.assertEqual(entity["owner"]["guid"], self.questionPublic.owner.guid)
        self.assertEqual(entity["url"], "/questions/view/{}/{}".format(self.questionPublic.guid, slugify(self.questionPublic.title)))
        self.assertIsNotNone(entity["timePublished"])
        self.assertIsNone(entity["scheduleArchiveEntity"])
        self.assertIsNone(entity["scheduleDeleteEntity"])

        variables = {
            "guid": self.questionPrivate.guid
        }

        result = self.graphql_client.post(self.query, variables)
        entity = result['data']['entity']

        self.assertEqual(entity, None)

    @override_config(
        QUESTIONER_CAN_CHOOSE_BEST_ANSWER=True,
        QUESTION_LOCK_AFTER_ACTIVITY=False
    )
    def test_question_owner(self):
        variables = {
            "guid": self.questionPrivate.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        entity = result['data']['entity']
        self.assertEqual(entity["guid"], self.questionPrivate.guid)
        self.assertEqual(entity["title"], self.questionPrivate.title)
        self.assertEqual(entity["richDescription"], self.questionPrivate.rich_description)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.questionPrivate.created_at.isoformat())
        self.assertEqual(entity["isClosed"], self.questionPrivate.is_closed)
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["views"], 0)
        self.assertEqual(entity["votes"], 0)
        self.assertEqual(entity["hasVoted"], False)
        self.assertEqual(entity["isBookmarked"], False)
        self.assertEqual(entity["isFollowing"], False)
        self.assertEqual(entity["isFeatured"], True)
        self.assertEqual(entity["canBookmark"], True)
        self.assertEqual(entity["canEdit"], True)
        self.assertEqual(entity["canComment"], True)
        self.assertEqual(entity["canChooseBestAnswer"], True)
        self.assertEqual(entity["isLocked"], False)
        self.assertEqual(entity["owner"]["guid"], self.questionPrivate.owner.guid)
        self.assertEqual(entity["url"], "/questions/view/{}/{}".format(self.questionPrivate.guid, slugify(self.questionPrivate.title)))
        self.assertEqual(entity["comments"][0]['guid'], self.comment2.guid)

    @override_config(
        QUESTIONER_CAN_CHOOSE_BEST_ANSWER=True,
        QUESTION_LOCK_AFTER_ACTIVITY=True
    )
    def test_question_owner_locked(self):
        variables = {
            "guid": self.questionPrivate.guid
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        entity = result['data']['entity']
        self.assertEqual(entity["guid"], self.questionPrivate.guid)
        self.assertEqual(entity["title"], self.questionPrivate.title)
        self.assertEqual(entity["richDescription"], self.questionPrivate.rich_description)
        self.assertEqual(entity["accessId"], 0)
        self.assertEqual(entity["timeCreated"], self.questionPrivate.created_at.isoformat())
        self.assertEqual(entity["isClosed"], self.questionPrivate.is_closed)
        self.assertEqual(entity["tags"], [])
        self.assertEqual(entity["views"], 0)
        self.assertEqual(entity["votes"], 0)
        self.assertEqual(entity["hasVoted"], False)
        self.assertEqual(entity["isBookmarked"], False)
        self.assertEqual(entity["isFollowing"], False)
        self.assertEqual(entity["isFeatured"], True)
        self.assertEqual(entity["canBookmark"], True)
        self.assertEqual(entity["canEdit"], False)
        self.assertEqual(entity["canComment"], True)
        self.assertEqual(entity["canChooseBestAnswer"], True)
        self.assertEqual(entity["isLocked"], True)
        self.assertEqual(entity["owner"]["guid"], self.questionPrivate.owner.guid)
        self.assertEqual(entity["url"], "/questions/view/{}/{}".format(self.questionPrivate.guid, slugify(self.questionPrivate.title)))
        self.assertEqual(entity["comments"][0]['guid'], self.comment2.guid)
