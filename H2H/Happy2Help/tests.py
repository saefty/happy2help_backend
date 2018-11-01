from django.test import TestCase
from graphene.test import Client
from H2H.H2H.schema import schema


# Create your tests here.
class UserModelTests(TestCase):
    client = Client(schema)

    def test_user_creation(self):
        result = self.client.execute("""mutation {createUser(username:"tOor" email:"toor@gmail.com" password:"testtest") {user {username}}}""")