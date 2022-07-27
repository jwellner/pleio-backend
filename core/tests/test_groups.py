from core.tests.helpers import PleioTenantTestCase
from core.models import Group
from user.factories import AdminFactory
from user.models import User
from mixer.backend.django import mixer


class GroupsEmptyTestCase(PleioTenantTestCase):

    def setUp(self):
        super(GroupsEmptyTestCase, self).setUp()

    def test_groups_empty(self):
        query = """
            {
                groups {
                    total
                    edges {
                        guid
                        name
                        tags
                    }
                }
            }
        """

        result = self.graphql_client.post(query, {})

        data = result["data"]

        self.assertEqual(data["groups"]["total"], 0)
        self.assertEqual(data["groups"]["edges"], [])


class GroupsNotEmptyTestCase(PleioTenantTestCase):

    def setUp(self):
        super(GroupsNotEmptyTestCase, self).setUp()
        self.user = mixer.blend(User)
        self.group1 = mixer.blend(Group,
                                  name="Group 1",
                                  tags=['tag_one'])
        self.group1.join(self.user, 'member')
        self.groups = mixer.cycle(5).blend(Group, is_closed=False)
        self.group2 = mixer.blend(Group, is_featured=True,
                                  name="Group 2",
                                  tags=['tag_one', 'tag_two'])
        self.query = """
            query GroupsQuery(
                    $filter: GroupFilter
                    $tags: [String]
                    $matchStrategy: MatchStrategy
                    $offset: Int
                    $limit: Int
                    $q: String) {
                groups(
                        filter: $filter
                        tags: $tags
                        matchStrategy: $matchStrategy
                        offset: $offset
                        limit: $limit
                        q: $q) {
                    total
                    edges {
                        guid
                        name
                    }
                }
            }
        """

    def tearDown(self):
        for group in self.groups:
            group.delete()
        self.group1.delete()
        self.group2.delete()
        self.user.delete()

    def test_groups_default(self):
        result = self.graphql_client.post(self.query, {})

        data = result["data"]

        self.assertEqual(data["groups"]["total"], 7)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group2.guid)

    def test_groups_limit(self):
        result = self.graphql_client.post(self.query, {'limit': 1})

        data = result["data"]

        self.assertEqual(data["groups"]["total"], 7)

    def test_groups_mine(self):
        variables = {
            "filter": "mine",
            "offset": 0,
            "limit": 20,
            "q": ""
        }
        self.graphql_client.force_login(self.user)
        result = self.graphql_client.post(self.query, variables)

        data = result["data"]

        self.assertEqual(data["groups"]["total"], 1)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group1.guid)

    def test_tags_match_all(self):
        result = self.graphql_client.post(self.query, {
            'tags': ["tag_one", "tag_two"]
        })
        groups = [e['name'] for e in result['data']['groups']['edges']]
        self.assertEqual(1, len(groups), msg=groups)
        self.assertIn(self.group2.name, groups, msg=groups)

    def test_tags_match_any(self):
        result = self.graphql_client.post(self.query, {
            'tags': ["tag_one", "tag_two"],
            'matchStrategy': 'any',
        })
        groups = [e['name'] for e in result['data']['groups']['edges']]
        self.assertEqual(2, len(groups), msg=groups)
        self.assertIn(self.group2.name, groups, msg=groups)
        self.assertIn(self.group1.name, groups, msg=groups)


class HiddenGroupTestCase(PleioTenantTestCase):

    def setUp(self):
        super(HiddenGroupTestCase, self).setUp()
        self.authenticated_user = mixer.blend(User, name="yy")
        self.group_member_user = mixer.blend(User, name="xx")
        self.non_member_user = mixer.blend(User, name="yyy")
        self.group = mixer.blend(Group, owner=self.authenticated_user,
                                 introduction='introductionMessage',
                                 is_hidden=True)
        self.group.join(self.group_member_user, 'member')
        self.admin = AdminFactory()

    def test_hidden_group_is_hidden_for_non_members(self):
        query = """
            query GroupsQuery {  
                groups {
                    total    
               }
            }
        """

        self.graphql_client.force_login(self.non_member_user)
        result = self.graphql_client.post(query, {})

        data = result["data"]
        self.assertEqual(data["groups"]["total"], 0)

    def test_hidden_group_is_visible_for_members(self):
        query = """
            query GroupsQuery {  
                groups {
                    total    
                    edges {      
                        guid
                    }    
               }
            }
        """

        self.graphql_client.force_login(self.group_member_user)
        result = self.graphql_client.post(query, {})

        data = result["data"]
        self.assertEqual(data["groups"]["total"], 1)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group.guid)

    def test_hidden_group_is_hidden_for_anonymous_users(self):
        query = """
            query GroupsQuery {  
                groups {
                    total    
               }
            }
        """
        result = self.graphql_client.post(query, {})

        data = result["data"]
        self.assertEqual(data["groups"]["total"], 0)

    def test_hidden_group_is_visible_for_admin_users(self):
        query = """
            query GroupsQuery {  
                groups {
                    total    
                    edges {      
                        guid
                    }    
               }
            }
        """
        self.graphql_client.force_login(self.admin)
        result = self.graphql_client.post(query, {})

        data = result["data"]
        self.assertEqual(data["groups"]["total"], 1)
        self.assertEqual(data["groups"]["edges"][0]["guid"], self.group.guid)
