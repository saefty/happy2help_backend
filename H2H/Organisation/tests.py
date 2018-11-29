
from django.contrib.auth import get_user_model


# Create your tests here.
from graphql_jwt.testcases import JSONWebTokenTestCase


class OrganisationTests(JSONWebTokenTestCase):

    def setUpTestData(cls):
        cls.user_0 = get_user_model().objects.create(username='test_user', password='test_password')

    def setUp(self):
        self.client.authenticate(self.user_0)

    def test_create_organisation(self):
        query = """mutation{createOrganisation(name: "Test Orga" description: "this is a test"){organisation{name}}}"""
        result = self.client.execute(query)

        self.assertTrue(result.data['createOrganisation']['organisation']['name'] == 'Test Orga')
