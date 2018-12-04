
from django.contrib.auth import get_user_model


# Create your tests here.
from graphql_jwt.testcases import JSONWebTokenTestCase

from Organisation.models import Organisation


class OrganisationTest(JSONWebTokenTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_0 = get_user_model().objects.create(username="user_0", password="sajadjkd22a")
        cls.user_1 = get_user_model().objects.create(username="user_1", password="sajadjkd22a")

        cls.orga_0 = Organisation.objects.create(name="orga1", description="orga1 desc", admin=cls.user_0)


class CreateTests(OrganisationTest):
    def setUp(self):
        pass

    def test_create_organisation_with_auth(self):
        self.client.authenticate(self.user_0)
        query = """mutation{createOrganisation(name: "Test Orga" description: "this is a test"){organisation{name}}}"""
        result = self.client.execute(query)
        self.assertTrue(result.data['createOrganisation']['organisation']['name'] == 'Test Orga')

    def test_create_organisation_without_auth(self):
        query = """mutation{createOrganisation(name: "Test Orga" description: "this is a test"){organisation{name}}}"""
        result = self.client.execute(query)
        self.assertIsNone(result.data['createOrganisation'])

    def test_admin(self):
        self.client.authenticate(self.user_0)
        query = """
            mutation {
              createOrganisation(name:"Hansssen" description:"asasas") {
                organisation {
                  id
                  admin {
                    username
                  }
                }
              }
            }
        """
        result = self.client.execute(query)
        self.assertEqual(result.data['createOrganisation']['organisation']['admin']['username'], self.user_0.username)


class UpdateTests(OrganisationTest):
    def setUp(self):
        self.client.authenticate(self.user_0)

    def test_edit_name(self):
        query = """
            mutation {
                updateOrganisation(id:1 name: "edit") {
                organisation {
                  name
                }
              }
            }
        """
        result = self.client.execute(query)
        self.assertEqual(result.data['updateOrganisation']['organisation']['name'], "edit")

    def test_edit_description(self):
        query = """
            mutation {
                updateOrganisation(id:1 description: "edit") {
                organisation {
                  description
                }
              }
            }
        """
        result = self.client.execute(query)
        self.assertEqual(result.data['updateOrganisation']['organisation']['description'], "edit")

    def test_add_existing_member(self):
        query = """
            mutation {
                updateOrganisation(id:1 addMember:2) {
                organisation {
                  members {
                    username
                  }
                }
              }
            }
        """
        result = self.client.execute(query)
        self.assertTrue("user_1" in result.data['updateOrganisation']['organisation']['members'][0].values())