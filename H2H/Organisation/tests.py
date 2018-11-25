"""
from django.contrib.auth import get_user_model
from django.test import TestCase

# Create your tests here.
from graphql_jwt.testcases import JSONWebTokenTestCase


class OrganisationTests(JSONWebTokenTestCase):

    def setUp(self):
        query = """"""mutation{createUser(username:"tOor" password:"testtest" email:"toor@gmail.com"){user{username}}}""""""
        result = self.client.execute(query)
        self.user = get_user_model().objects.get(username="tOor")
        self.client.authenticate(self.user)

    def test_create_organisation(self):
        query = """"""mutation{createOrganisation(name: "Test Orga" description: "this is a test"){organisation{name}}}""""""
        result = self.client.execute(query)

        self.assertTrue(result.data['createOrganisation']['organisation']['name'] == 'Test Orga')
"""