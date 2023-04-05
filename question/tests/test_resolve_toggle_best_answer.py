from django.core.cache import cache
from core.models import Comment
from core.tests.helpers import PleioTenantTestCase
from user.factories import QuestionManagerFactory, AdminFactory, UserFactory
from user.models import User
from question.models import Question
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE, USER_ROLES


class ToggleBestAnswerTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.authenticatedUser = UserFactory()
        self.admin = AdminFactory()
        self.question_manager = QuestionManagerFactory()

        self.question = Question.objects.create(
            title="Test1",
            rich_description="",
            read_access=[ACCESS_TYPE.public],
            write_access=[ACCESS_TYPE.user.format(self.authenticatedUser.id)],
            owner=self.authenticatedUser,
            is_closed=False
        )

        self.answer = Comment.objects.create(
            rich_description="",
            owner=self.authenticatedUser,
            container=self.question
        )

        self.query = """
            mutation ($input: toggleBestAnswerInput!) {
                toggleBestAnswer(input: $input) {
                    entity {
                        guid
                        comments {
                            isBestAnswer
                        }
                    }
                }
            }
        """

        cache.set("%s%s" % (self.tenant.schema_name, 'QUESTIONER_CAN_CHOOSE_BEST_ANSWER'), True)

    def tearDown(self):
        self.question.delete()
        self.authenticatedUser.delete()
        cache.clear()
        super().tearDown()

    def test_toggle_best_answer_owner(self):
        variables = {
            "input": {
                "guid": self.answer.guid,
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["toggleBestAnswer"]["entity"]["guid"], self.question.guid)
        self.assertTrue(data["toggleBestAnswer"]["entity"]["comments"][0]["isBestAnswer"])

        self.question.refresh_from_db()

        self.assertEqual(self.question.best_answer, self.answer)

        variables = {
            "input": {
                "guid": self.answer.guid,
            }
        }

        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["toggleBestAnswer"]["entity"]["guid"], self.question.guid)
        self.assertFalse(data["toggleBestAnswer"]["entity"]["comments"][0]["isBestAnswer"])

        self.question.refresh_from_db()

        self.assertIsNone(self.question.best_answer)

    def test_toggle_best_answer_admin(self):
        variables = {
            "input": {
                "guid": self.answer.guid,
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["toggleBestAnswer"]["entity"]["guid"], self.question.guid)
        self.assertTrue(data["toggleBestAnswer"]["entity"]["comments"][0]["isBestAnswer"])

        self.question.refresh_from_db()

        self.assertEqual(self.question.best_answer, self.answer)

        variables = {
            "input": {
                "guid": self.answer.guid,
            }
        }

        result  =self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["toggleBestAnswer"]["entity"]["guid"], self.question.guid)
        self.assertFalse(data["toggleBestAnswer"]["entity"]["comments"][0]["isBestAnswer"])

        self.question.refresh_from_db()

        self.assertIsNone(self.question.best_answer)

    def test_toggle_best_answer_question_manager(self):
        variables = {
            "input": {
                "guid": self.answer.guid,
            }
        }

        self.graphql_client.force_login(self.question_manager)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["toggleBestAnswer"]["entity"]["guid"], self.question.guid)
        self.assertTrue(data["toggleBestAnswer"]["entity"]["comments"][0]["isBestAnswer"])

        self.question.refresh_from_db()

        self.assertEqual(self.question.best_answer, self.answer)

        variables = {
            "input": {
                "guid": self.answer.guid,
            }
        }

        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["toggleBestAnswer"]["entity"]["guid"], self.question.guid)
        self.assertFalse(data["toggleBestAnswer"]["entity"]["comments"][0]["isBestAnswer"])

        self.question.refresh_from_db()

        self.assertIsNone(self.question.best_answer)
