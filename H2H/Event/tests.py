from django.contrib.auth import get_user_model

from graphql_jwt.testcases import JSONWebTokenTestCase

from Location.models import Location


class TestEvent(JSONWebTokenTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create(username='tOor', password='testtest')
        cls.location = Location.objects.create(latitude=52.564668, longitude=13.360665, name="Schäfersee")

    def setUp(self):
        self.client.authenticate(self.user)

    def test_create_event(self):
        # create location first
        # TODO: maybe create an empty location at event creation

        resp = self.client.execute(
            """
            mutation {
                createEvent(locationId:1 name:"Helfen" description:"Hilf schnell!") {
                event {
                  id
                }
              }
            }
            """
        )

        self.assertTrue(resp.data["createEvent"]["event"]["id"])

    def test_delete_event(self):
        pass

    def test_delete_event_with_participations(self):
        pass
