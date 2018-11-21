from django.contrib.auth import get_user_model

from graphql_jwt.testcases import JSONWebTokenTestCase

from Event.models import Event
from Location.models import Location


class TestEvent(JSONWebTokenTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create(username='tOor', password='testtest')

    def setUp(self):
        self.client.authenticate(self.user)

    def test_create_event(self):
        # create location first
        # TODO: maybe create an empty location at event creation
        location = Location.objects.create(latitude=52.564668, longitude=13.360665, name="Schäfersee")
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

    def test_create_job(self):
        location = Location.objects.create(latitude=52.544937, longitude=13.351855, name="Beuth")
        event = Event.objects.create(
            name="Mega Event",
            description="Da muss man hin!",
            creator=self.user,
            location=location
        )
        resp = self.client.execute(
            """
            mutation {
                createJob(eventId:1 name:"ein job" description:"toller job" totalPositions:2) {
                job {
                  id
                }
              }
            }
            """
        )
        self.assertTrue(resp.data["createJob"]["job"]["id"])