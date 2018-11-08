# graphql_jwt style
from django.contrib.auth import get_user_model
from graphql_jwt.testcases import JSONWebTokenTestCase


class UsersTests(JSONWebTokenTestCase):

    def setUp(self):
        # self.user = get_user_model().objects.create(username='tOor', password='testtest')
        query = """mutation{createUser(username:"tOor" password:"testtest" email:"toor@gmail.com"){user{username}}}"""
        result = self.client.execute(query)
        self.user = get_user_model().objects.get(username="tOor")
        self.client.authenticate(self.user)

    def test_get_user(self):
        query = """query{user{username}}"""
        result = self.client.execute(query)

        self.assertTrue(result.data["user"]["username"] == 'tOor')

    def test_edit_birthday(self):
        query = """mutation{updateUser(birthday:"1986-11-20"){user{profile{birthday}}}}"""
        result = self.client.execute(query)

        self.assertTrue(result.data["updateUser"]["user"]["profile"]["birthday"] == '1986-11-20')


class OrganisationTests(JSONWebTokenTestCase):

    def setUp(self):
        query = """mutation{createUser(username:"tOor" password:"testtest" email:"toor@gmail.com"){user{username}}}"""
        result = self.client.execute(query)
        self.user = get_user_model().objects.get(username="tOor")
        self.client.authenticate(self.user)

    def test_create_organisation(self):
        query = """mutation{createOrganisation(name: "Test Orga" description: "this is a test"){organisation{name}}}"""
        result = self.client.execute(query)

        self.assertTrue(result.data['createOrganisation']['organisation']['name'] == 'Test Orga')