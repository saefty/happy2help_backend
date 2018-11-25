from django.contrib.auth import get_user_model

from graphql_jwt.testcases import JSONWebTokenTestCase

from Event.models import Event
from Location.models import Location
from Organisation.models import Organisation
from User.models import Profile


class TestEvent(JSONWebTokenTestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user_0 = get_user_model().objects.create(username='test_user', password='test_password')
        cls.user_1 = get_user_model().objects.create(username='test_user_1', password='test_password')

        cls.organisation_0 = Organisation.objects.create(name='test_organisation_0', description='test', admin=cls.user_0)
        cls.organisation_1 = Organisation.objects.create(name='test_organisation_1', description='test', admin=cls.user_1)
        cls.organisation_0.members.add(cls.user_0)
        cls.organisation_1.members.add(cls.user_1)

        cls.location_0 = Location.objects.create(latitude=10, longitude=10, name="test_location_0")
        cls.location_1 = Location.objects.create(latitude=15, longitude=15, name="test_location_1")

        cls.event_0 = Event.objects.create(name='test_event_0', description='test', location=cls.location_0,
                                           start='2050-11-01T11:00:00', end='2050-11-02T11:00:00',
                                           organisation=cls.organisation_0, creator=cls.user_0)
        cls.event_1 = Event.objects.create(name='test_event_1', description='test', location=cls.location_1,
                                           start='2050-11-01T11:00:00', end='2050-11-02T11:00:00',
                                           organisation=cls.organisation_1, creator=cls.user_1)

    def setUp(self):
        self.client.authenticate(self.user_0)

    def test_query_events(self):
        resp_0 = self.client.execute(
            """
            query {
              events {
                  id
                }
            }
            """
        )

        self.assertEqual(len(resp_0.data["events"]), 2)

    def test_query_event_by_id(self):
        resp_0 = self.client.execute(
            """
            query {
              event(id: 2) {
                  id
                }
            }
            """
        )

        self.assertEqual(len(resp_0.data["event"]), 1)
        self.assertEqual(resp_0.data["event"]["id"], str(self.event_1.id))

    def test_query_events_by_coordinates(self):
        resp_0 = self.client.execute(
            """
            query {
              eventsByCoordinates(ulLongitude: 10, ulLatitude: 10, lrLongitude: 20, lrLatitude: 20) {
  	                id
                }
            }
            """
        )

        resp_1 = self.client.execute(
            """
            query {
              eventsByCoordinates(ulLongitude: 10, ulLatitude: 10, lrLongitude: 20, lrLatitude: 14) {
  	                id
                }
            }
            """
        )

        resp_2 = self.client.execute(
            """
            query {
              eventsByCoordinates(ulLongitude: 10, ulLatitude: 10, lrLongitude: 14, lrLatitude: 20) {
  	                id
                }
            }
            """
        )

        self.assertEqual(len(resp_0.data["eventsByCoordinates"]), 2)    # both events pass
        
        self.assertEqual(len(resp_1.data["eventsByCoordinates"]), 1)    # only one event passes
        self.assertEqual(len(resp_2.data["eventsByCoordinates"]), 1)

        self.assertEqual(resp_1.data["eventsByCoordinates"][0]["id"], str(self.event_0.id))
        self.assertEqual(resp_2.data["eventsByCoordinates"][0]["id"], str(self.event_0.id))

    def test_create_event(self):
        """ Test for normal event creation """
        resp = self.client.execute(
            """
            mutation {
                createEvent(organisationId: "1", name: "test_event_1", description: "test",
                            locationName: "test_location_0", locationLat: 52.564668, locationLon: 13.360665,
                            start: "2050-11-01T11:00:00", end: "2050-11-02T11:00:00") {
                    event {
                        id
                        creator {
                            id
                        }
                         organisation {
                            name
                        }
                        location {
                            id
                        }
                        jobSet {
                            id
                        }
                    }
                }
            }
            """
        )

        self.assertTrue(resp.data["createEvent"]["event"]["id"])
        self.assertTrue(resp.data["createEvent"]["event"]["location"]["id"])
        self.assertTrue(resp.data["createEvent"]["event"]["jobSet"][0]["id"])
        self.assertEqual(resp.data["createEvent"]["event"]["creator"]["id"], str(self.user_0.id))
        self.assertEqual(resp.data["createEvent"]["event"]["organisation"]["name"], self.organisation_0.name)
    
    def test_create_event_invalid_organisation(self):
        """ Test for event creation with an organisation the user is not a member of """
        resp = self.client.execute(
            """
            mutation {
                createEvent(organisationId: "2", name: "test_event_1", description: "test",
                            locationName: "test_location_0", locationLat: 52.564668, locationLon: 13.360665,
                            start: "2050-11-01T11:00:00", end: "2050-11-02T11:00:00") {
                    event {
                        id
                    }
                }
            }
            """
        )

        self.assertIsNone(resp.data["createEvent"])

    def test_create_event_invalid_time(self):
        """ Test for event creation with invalid times (end- before start time) """
        resp = self.client.execute(
            """
            mutation {
                createEvent(organisationId: "1", name: "test_event_1", description: "test",
                            locationName: "test_location_0", locationLat: 52.564668, locationLon: 13.360665,
                            start: "2050-11-02T11:00:00", end: "2050-11-01T11:00:00") {
                    event {
                        id
                    }
                }
            }
            """
        )

        self.assertIsNone(resp.data["createEvent"])

    def test_create_event_credits(self):
        """ Test for non-organisation event creation and subtraction of user credits """
        resp_0 = self.client.execute(
            """
            query {
              user {
                profile {
                  creditPoints
                }
              }
            }
            """
        )

        resp_1 = self.client.execute( 
            """
            mutation {
              updateUser(creditPoints:10){
                user {
                  profile {
                    creditPoints
                  }
                }
              }
            }
            """
        )
        
        resp_2 = self.client.execute(
           """
            mutation {
                createEvent(name: "test_event_1", description: "test",
                            locationName: "test_location_0", locationLat: 52.564668, locationLon: 13.360665,
                            start: "2050-11-01T11:00:00", end: "2050-11-02T11:00:00") {
                    event {
                        id
                        creator {
                            id
                            profile {
                                id
                                creditPoints
                            }
                            username
                        }
                        organisation {
                            id
                        }
                    }
                }
            }
            """
        )

        resp_3 = self.client.execute(
           """
            mutation {
                createEvent(name: "test_event_2", description: "test",
                            locationName: "test_location_2", locationLat: 52.564668, locationLon: 13.360665,
                            start: "2050-11-01T11:00:00", end: "2050-11-02T11:00:00") {
                    event {
                        id
                    }
                }
            }
            """
        )

        self.assertEqual(resp_0.data["user"]["profile"]["creditPoints"], 0)                             # start out with 0 credits

        self.assertEqual(resp_1.data["updateUser"]["user"]["profile"]["creditPoints"], 10)              # succesfully added 10 credits

        self.assertTrue(resp_2.data["createEvent"]["event"]["id"])                                      # successfully created event
        self.assertTrue(resp_2.data["createEvent"]["event"]["creator"]["id"], str(self.user_0.id))
        self.assertEqual(resp_2.data["createEvent"]["event"]["creator"]["profile"]["id"], str(self.user_0.profile.id))
        self.assertIsNone(resp_2.data["createEvent"]["event"]["organisation"])                          # no organisation
        self.assertEqual(resp_2.data["createEvent"]["event"]["creator"]["profile"]["creditPoints"], 0)  # subtracted 10 credits

        #self.assertIsNone(resp_3.data["createEvent"]["event"]) -> NOT WORKING WITH SQLITE

"""
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
            """"""
            mutation {
                createJob(eventId:1 name:"ein job" description:"toller job" totalPositions:2) {
                job {
                  id
                }
              }
            }
            """"""
        )
        self.assertTrue(resp.data["createJob"]["job"]["id"])
"""