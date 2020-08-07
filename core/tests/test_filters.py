from django.db import connection
from django_tenants.test.cases import FastTenantTestCase
from backend2.schema import schema
from ariadne import graphql_sync
import json
from core.lib import is_valid_json
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from core.models import Group, ProfileField
from user.models import User
from mixer.backend.django import mixer
from graphql import GraphQLError

class FiltersTestCase(FastTenantTestCase):

    def setUp(self):
        self.anonymousUser = AnonymousUser()
        self.user = mixer.blend(User)
        self.other = mixer.blend(User)
        self.admin = mixer.blend(User)
        self.admin.is_admin = True
        self.admin.save()
        ProfileField.objects.create(key='text_key', name='text_name', field_type='text_field')
        ProfileField.objects.create(key='html_key', name='html_name', field_type='html_field')
        ProfileField.objects.create(key='select_key', name='select_name', field_type='select_field', field_options=['select_value', 'select_value_2'])
        ProfileField.objects.create(key='date_key', name='date_name', field_type='date_field')
        ProfileField.objects.create(key='multi_key', is_filter=True, name='multi_name', field_type='multi_select_field',
                                    field_options=['select_value_1', 'select_value_2', 'select_value_3'])

    def tearDown(self):
        self.admin.delete()
        self.other.delete()
        self.user.delete()

    def test_query_filters_by_user(self):
        query = """
            query UsersQuery {
                filters {
                    users {
                        name
                        label
                        fieldType
                        keys
                    }
                }
            }
        """
        variables = {
            "input": {
                "offset": 0,
                "limit": "40"
            }
        }

        request = HttpRequest()
        request.user = self.user

        result = graphql_sync(schema, { "query": query, "variables": variables }, context_value={ 'request': request })

        data = result[1]["data"]

        self.assertEqual(data["filters"]["users"][0]["name"], "multi_key")
        self.assertEqual(data["filters"]["users"][0]["fieldType"], "multi_select_field")        
        self.assertEqual(data["filters"]["users"][0]["label"], "multi_name")        
        self.assertEqual(data["filters"]["users"][0]["keys"], ['select_value_1', 'select_value_2', 'select_value_3'])  
