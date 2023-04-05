from core.tests.helpers import PleioTenantTestCase
from user.factories import QuestionManagerFactory, AdminFactory, UserFactory
from user.models import User
from question.models import Question
from mixer.backend.django import mixer
from core.constances import ACCESS_TYPE, USER_ROLES


class ToggleIsClosedTestCase(PleioTenantTestCase):

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
        self.query = """
            mutation ($input: toggleIsClosedInput!) {
                toggleIsClosed(input: $input) {
                    entity {
                        guid
                        isClosed
                    }
                }
            }
        """

    def tearDown(self):
        self.question.delete()
        self.authenticatedUser.delete()
        self.admin.delete()
        self.question_manager.delete()
        super().tearDown()

    def test_toggle_is_closed_owner(self):
        variables = {
            "input": {
                "guid": self.question.guid,
            }
        }

        self.graphql_client.force_login(self.authenticatedUser)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["toggleIsClosed"]["entity"]["guid"], self.question.guid)
        self.assertTrue(data["toggleIsClosed"]["entity"]["isClosed"])

        self.question.refresh_from_db()

        self.assertTrue(self.question.is_closed)

        variables = {
            "input": {
                "guid": self.question.guid,
            }
        }

        result = self.graphql_client.post(self.query, variables)

        data = result["data"]
        self.assertEqual(data["toggleIsClosed"]["entity"]["guid"], self.question.guid)
        self.assertFalse(data["toggleIsClosed"]["entity"]["isClosed"])

        self.question.refresh_from_db()

        self.assertFalse(self.question.is_closed)

    def test_toggle_is_closed_admin(self):
        variables = {
            "input": {
                "guid": self.question.guid,
            }
        }

        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(self.query, variables)
        self.question.refresh_from_db()

        data = result["data"]
        self.assertEqual(data["toggleIsClosed"]["entity"]["guid"], self.question.guid)
        self.assertTrue(data["toggleIsClosed"]["entity"]["isClosed"])
        self.assertTrue(self.question.is_closed)

        variables = {
            "input": {
                "guid": self.question.guid,
            }
        }

        result = self.graphql_client.post(self.query, variables)
        self.question.refresh_from_db()

        data = result["data"]
        self.assertEqual(data["toggleIsClosed"]["entity"]["guid"], self.question.guid)
        self.assertFalse(data["toggleIsClosed"]["entity"]["isClosed"])
        self.assertFalse(self.question.is_closed)

    def test_toggle_is_closed_question_manager(self):
        variables = {
            "input": {
                "guid": self.question.guid,
            }
        }

        self.graphql_client.force_login(self.question_manager)
        result = self.graphql_client.post(self.query, variables)
        self.question.refresh_from_db()

        data = result["data"]
        self.assertEqual(data["toggleIsClosed"]["entity"]["guid"], self.question.guid)
        self.assertTrue(data["toggleIsClosed"]["entity"]["isClosed"])
        self.assertTrue(self.question.is_closed)

        variables = {
            "input": {
                "guid": self.question.guid,
            }
        }

        result = self.graphql_client.post(self.query, variables)
        self.question.refresh_from_db()

        data = result["data"]
        self.assertEqual(data["toggleIsClosed"]["entity"]["guid"], self.question.guid)
        self.assertFalse(data["toggleIsClosed"]["entity"]["isClosed"])
        self.assertFalse(self.question.is_closed)
