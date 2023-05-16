from mixer.backend.django import mixer

from blog.models import Blog
from core.constances import ACCESS_TYPE
from core.models import Group, Subgroup
from core.tests.helpers import PleioTenantTestCase
from user.models import User


class SubgroupsTestCase(PleioTenantTestCase):

    def setUp(self):
        super().setUp()
        self.admin = mixer.blend(User, roles=['ADMIN'])
        self.user1 = mixer.blend(User)
        self.user2 = mixer.blend(User, name='test_na')
        self.user3 = mixer.blend(User)
        self.user4 = mixer.blend(User)
        self.user5 = mixer.blend(User)
        self.user6 = mixer.blend(User)

        self.group = mixer.blend(Group, owner=self.user1)
        self.group.join(self.user1, 'owner')
        self.group.join(self.user2, 'member')
        self.group.join(self.user3, 'member')
        self.group.join(self.user4, 'member')
        self.group.join(self.user5, 'member')
        self.group.join(self.user6, 'member')

        self.subgroup1 = Subgroup.objects.create(
            name='testSubgroup1',
            group=self.group,
            id=1
        )
        self.subgroup1.members.add(self.user2)
        self.subgroup1.members.add(self.user3)
        self.subgroup1.members.add(self.user6)

        self.group.leave(self.user6)

        self.blog = Blog.objects.create(
            title="Test subgroup blog",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.user1.id), ACCESS_TYPE.subgroup.format(self.subgroup1.access_id)],
            write_access=[ACCESS_TYPE.user.format(self.user1.id)],
            owner=self.user1,
            group=self.group,
            is_recommended=False
        )

        self.blog2 = Blog.objects.create(
            title="Test subgroup blog",
            rich_description="JSON to string",
            read_access=[ACCESS_TYPE.user.format(self.user1.id), ACCESS_TYPE.subgroup.format(self.subgroup1.access_id)],
            write_access=[ACCESS_TYPE.user.format(self.user1.id), ACCESS_TYPE.subgroup.format(self.subgroup1.access_id)],
            owner=self.user1,
            group=self.group,
            is_recommended=False
        )

    def tearDown(self):
        super().tearDown()

    def test_query_subgroups_by_group_owner(self):
        query = """
            query SubgroupsList($guid: String!) {
                entity(guid: $guid) {
                    ... on Group {
                        guid
                        subgroups {
                            total
                            edges {
                            id
                            name
                            members {
                                guid
                                __typename
                            }
                            __typename
                            }
                            __typename
                        }
                        __typename
                        }
                    __typename
                }
            }
        """
        variables = {"guid": self.group.guid}

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["subgroups"]["total"], 1)
        self.assertEqual(data["entity"]["subgroups"]["edges"][0]["id"], self.subgroup1.id)
        self.assertEqual(data["entity"]["subgroups"]["edges"][0]["name"], self.subgroup1.name)

    def test_query_subgroups_memberlist_by_group_owner(self):
        query = """
            query SubgroupMembersList($guid: String!, $subgroupId: Int, $q: String, $offsetInSubgroup: Int, $offsetNotInSubgroup: Int) {
                inSubgroup: entity(guid: $guid) {
                    ... on Group {
                        guid
                        canEdit
                        canChangeOwnership
                        members(q: $q, offset: $offsetInSubgroup, limit: 20, inSubgroupId: $subgroupId) {
                            total
                            edges {
                                role
                                email
                                user {
                                    guid
                                    username
                                    url
                                    name
                                    icon
                                    __typename
                                }
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
                notInSubgroup: entity(guid: $guid) {
                    ... on Group {
                        guid
                        canEdit
                        canChangeOwnership
                        members(q: $q, offset: $offsetNotInSubgroup, limit: 20, notInSubgroupId: $subgroupId) {
                            total
                            edges {
                                role
                                email
                                user {
                                    guid
                                    username
                                    url
                                    name
                                    icon
                                    __typename
                                }
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "guid": self.group.guid,
            "subgroupId": self.subgroup1.id,
            "q": ""
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["inSubgroup"]["guid"], self.group.guid)
        self.assertEqual(data["inSubgroup"]["members"]["total"], 2)
        self.assertEqual(data["notInSubgroup"]["guid"], self.group.guid)
        self.assertEqual(data["notInSubgroup"]["members"]["total"], 3)

    def test_query_subgroup_access_fields(self):
        query = """
            query AccessField($guid: String) {
                entity(guid: $guid) {
                    guid
                    status
                    ... on Group {
                        defaultAccessId
                        accessIds {
                            id
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {"guid": self.group.guid}

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.group.guid)
        self.assertEqual(data["entity"]["defaultAccessId"], 1)
        self.assertEqual(data["entity"]["accessIds"][2]["id"], 10001)

    def test_blog_in_subgroup_by_subgroup_member(self):
        query = """
            fragment BlogParts on Blog {
                title
                accessId
                writeAccessId
                owner {
                    guid
                }
                group {
                    guid
                }
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """
        variables = {
            "guid": self.blog.guid
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.blog.guid)
        self.assertEqual(data["entity"]["accessId"], 10001)
        self.assertEqual(data["entity"]["writeAccessId"], 0)

    def test_blog2_in_subgroup_by_subgroup_member(self):
        query = """
            fragment BlogParts on Blog {
                title
                accessId
                writeAccessId
                owner {
                    guid
                }
                group {
                    guid
                }
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """
        variables = {
            "guid": self.blog2.guid
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"]["guid"], self.blog2.guid)
        self.assertEqual(data["entity"]["accessId"], 10001)
        self.assertEqual(data["entity"]["writeAccessId"], 10001)

    def test_edit_blog_in_subgroup_by_subgroup_member(self):
        mutation = """
            fragment BlogParts on Blog {
                title
                richDescription
                timeCreated
                timeUpdated
                accessId
                writeAccessId
                canEdit
                tags
                url
                inGroup
                group {
                    guid
                }
                isRecommended
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...BlogParts
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog2.guid,
                "title": "Update blog title",
            }
        }

        self.graphql_client.force_login(self.user2)
        result = self.graphql_client.post(mutation, variables)

        data = result["data"]
        self.assertEqual(data["editEntity"]["entity"]["guid"], self.blog2.guid)
        self.assertEqual(data["editEntity"]["entity"]["title"], "Update blog title")
        self.assertEqual(data["editEntity"]["entity"]["accessId"], 10001)
        self.assertEqual(data["editEntity"]["entity"]["writeAccessId"], 10001)

    def test_edit_blog_in_subgroup_by_non_subgroup_member(self):
        mutation = """
            fragment BlogParts on Blog {
                title
                richDescription
                timeCreated
                timeUpdated
                accessId
                writeAccessId
                canEdit
                tags
                url
                inGroup
                group {
                    guid
                }
                isRecommended
            }
            mutation ($input: editEntityInput!) {
                editEntity(input: $input) {
                    entity {
                    guid
                    status
                    ...BlogParts
                    }
                }
            }
        """
        variables = {
            "input": {
                "guid": self.blog2.guid,
                "title": "Update blog title",
            }
        }

        with self.assertGraphQlError("could_not_save"):
            self.graphql_client.force_login(self.user5)
            self.graphql_client.post(mutation, variables)

        self.assertEqual(self.graphql_client.result['data']["editEntity"], None)

    def test_blog_in_subgroup_by_non_subgroup_member(self):
        query = """
            fragment BlogParts on Blog {
                title
                accessId
                writeAccessId
                owner {
                    guid
                }
                group {
                    guid
                }
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """
        variables = {
            "guid": self.blog2.guid
        }

        self.graphql_client.force_login(self.user5)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"], None)

    def test_blog_in_subgroup_by_subgroup_member_which_left_group(self):
        query = """
            fragment BlogParts on Blog {
                title
                accessId
                owner {
                    guid
                }
                group {
                    guid
                }
            }
            query GetBlog($guid: String!) {
                entity(guid: $guid) {
                    guid
                    status
                    ...BlogParts
                }
            }
        """
        variables = {
            "guid": self.blog.guid
        }

        self.graphql_client.force_login(self.user6)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["entity"], None)

    def test_query_subgroups_memberlist_with_filter(self):
        query = """
            query SubgroupMembersList($guid: String!, $subgroupId: Int, $q: String, $offsetInSubgroup: Int, $offsetNotInSubgroup: Int) {
                inSubgroup: entity(guid: $guid) {
                    ... on Group {
                        guid
                        canEdit
                        canChangeOwnership
                        members(q: $q, offset: $offsetInSubgroup, limit: 20, inSubgroupId: $subgroupId) {
                            total
                            edges {
                                role
                                email
                                user {
                                    guid
                                    username
                                    url
                                    name
                                    icon
                                    __typename
                                }
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
                notInSubgroup: entity(guid: $guid) {
                    ... on Group {
                        guid
                        canEdit
                        canChangeOwnership
                        members(q: $q, offset: $offsetNotInSubgroup, limit: 20, notInSubgroupId: $subgroupId) {
                            total
                            edges {
                                role
                                email
                                user {
                                    guid
                                    username
                                    url
                                    name
                                    icon
                                    __typename
                                }
                                __typename
                            }
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }
        """
        variables = {
            "guid": self.group.guid,
            "subgroupId": self.subgroup1.id,
            "q": "test_na"
        }

        self.graphql_client.force_login(self.user1)
        result = self.graphql_client.post(query, variables)

        data = result["data"]
        self.assertEqual(data["inSubgroup"]["guid"], self.group.guid)
        self.assertEqual(data["inSubgroup"]["members"]["total"], 1)
        self.assertEqual(data["notInSubgroup"]["guid"], self.group.guid)
        self.assertEqual(data["notInSubgroup"]["members"]["total"], 0)
