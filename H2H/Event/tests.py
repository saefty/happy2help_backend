from django.contrib.auth import get_user_model

from graphql_jwt.testcases import JSONWebTokenTestCase
from unittest import skip

from Event.models import Event, Job, Participation
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
                                           start='2050-11-01T11:00:00+00:00', end='2050-11-02T11:00:00+00:00',
                                           organisation=cls.organisation_0, creator=cls.user_0)
        cls.event_1 = Event.objects.create(name='test_event_1', description='test', location=cls.location_1,
                                           start='2050-11-01T11:00:00+00:00', end='2050-11-02T11:00:00+00:00',
                                           organisation=cls.organisation_1, creator=cls.user_1)

        cls.job_0 = Job.objects.create(name="test_job_0", description="test", event=cls.event_0, total_positions=2)
        cls.job_1 = Job.objects.create(name="test_job_1", description="test", event=cls.event_1, total_positions=4)
        cls.participation_job_0 = Job.objects.create(name="participation_job_0", description="test", event=cls.event_0, total_positions=4)
        cls.participation_job_1 = Job.objects.create(name="participation_job_1", description="test", event=cls.event_0, total_positions=1)

        cls.participation_0 = Participation.objects.create(job=cls.participation_job_0, user=cls.user_0, state=4)
        cls.participation_1 = Participation.objects.create(job=cls.participation_job_0, user=cls.user_1, state=4)

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
                            start: "2050-11-01T11:00:00+00:00", end: "2050-11-02T11:00:00+00:00") {
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
                            start: "2050-11-01T11:00:00+00:00", end: "2050-11-02T11:00:00+00:00") {
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
                            start: "2050-11-02T11:00:00+00:00", end: "2050-11-01T11:00:00+00:00") {
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
                            start: "2050-11-01T11:00:00+00:00", end: "2050-11-02T11:00:00+00:00") {
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
                            start: "2050-11-01T11:00:00+00:00", end: "2050-11-02T11:00:00+00:00") {
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

        #self.assertIsNone(resp_3.data["createEvent"]["event"])                                         -> NOT WORKING WITH SQLITE

    def test_update_event(self):
        self.client.execute(
            """
            mutation {
                updateEvent(eventId: 1, name: "updated", description: "updated",
                            start: "2050-12-01T11:00:00+00:00", end: "2050-12-02T11:00:00+00:00") {
                    event {
                        id
                    }
                }
            }
            """
        )

        resp_0 = self.client.execute(
            """
            query {
              event(id: 1) {
                  id
                  name
                  description
                  start
                  end
                }
            }
            """
        )

        self.assertEqual(resp_0.data["event"]["name"], "updated")
        self.assertEqual(resp_0.data["event"]["description"], "updated")
        self.assertEqual(resp_0.data["event"]["start"], "2050-12-01T11:00:00+00:00")
        self.assertEqual(resp_0.data["event"]["end"], "2050-12-02T11:00:00+00:00")

    def test_update_event_invalid_organisation(self):
        """ Test for updating an event the user is not a member of """
        resp_0 = self.client.execute(
            """
            mutation {
                updateEvent(eventId: 2, name: "updated", description: "updated",
                            start: "2050-12-01T11:00:00+00:00", end: "2050-12-02T11:00:00+00:00") {
                    event {
                        id
                    }
                }
            }
            """
        )

        self.assertIsNone(resp_0.data["updateEvent"])

    def test_delete_event(self):
        resp_0 = self.client.execute(
            """
            mutation {
                deleteEvent(eventId: 1) {
                    event {
                        name
                    }
                }
            }
            """
        )

        resp_1 = self.client.execute(
            """
            query {
              event(id: 1) {
                  id
                }
            }
            """
        )

        resp_2 = self.client.execute(
            """
            query {
              events {
                  id
                }
            }
            """
        )

        self.assertEqual(resp_0.data["deleteEvent"]["event"]["name"], "test_event_0")
        self.assertIsNone(resp_1.data["event"])
        self.assertEqual(len(resp_2.data["events"]), 1)

    def test_delete_event_invalid_organisation(self):
        """ Test for deleting an event the user is not a member of """
        resp_0 = self.client.execute(
           """
            mutation {
                deleteEvent(eventId: 2) {
                    event {
                        name
                    }
                }
            }
            """
        )

        self.assertIsNone(resp_0.data["deleteEvent"])

    def test_query_jobs(self):
        """ Test for querying jobSet of user """
        resp_0 = self.client.execute(
            """
            query {
                jobs {
                    id
                    name
                }
            }
            """
         )

        self.assertTrue(resp_0.data["jobs"][0])
        self.assertEqual(len(resp_0.data["jobs"]), 1)

    def test_create_job(self):
        resp_0 = self.client.execute(
            """
            mutation {
                createJob(eventId:1, name:"test_job", description:"test_job") {
                job {
                  id
                  name
                  description
                  totalPositions
                }
              }
            }
            """
        )

        resp_1 = self.client.execute(
            """
            mutation {
                createJob(eventId:1, name:"test_job", description:"test_job") {
                job {
                  id
                }
              }
            }
            """
        )

        self.assertTrue(resp_0.data["createJob"]["job"]["id"])
        self.assertEqual(resp_0.data["createJob"]["job"]["name"], "test_job")
        self.assertEqual(resp_0.data["createJob"]["job"]["description"], "test_job")
        self.assertEqual(resp_0.data["createJob"]["job"]["totalPositions"], None)
        self.assertIsNone(resp_1.data["createJob"])    # job already exists


    def test_create_job_invalid_creator(self):
        resp = self.client.execute(
            """
            mutation {
                createJob(eventId:2, name:"test_job", description:"test_job", totalPositions: 2) {
                job {
                  id
                }
              }
            }
            """
        )

        self.assertIsNone(resp.data["createJob"])

    def test_update_job(self):
        self.client.execute(
            """
            mutation {
                createJob(eventId:1, name:"test_job", description:"test_job", totalPositions: 2) {
                job {
                  id
                  name
                  description
                  totalPositions
                }
              }
            }
            """
        )

        resp_0 = self.client.execute(
            """
            mutation {
                updateJob(jobId:3, name:"updated", description:"updated", totalPositions: 3) {
                job {
                  id
                  name
                  description
                  totalPositions
                }
              }
            }
            """
        )

        self.assertTrue(resp_0.data["updateJob"]["job"]["id"])
        self.assertEqual(resp_0.data["updateJob"]["job"]["name"], "updated")
        self.assertEqual(resp_0.data["updateJob"]["job"]["description"], "updated")
        self.assertEqual(resp_0.data["updateJob"]["job"]["totalPositions"], 3)

    def test_update_job_invalid_creator(self):
        resp_0 = self.client.execute(
            """
            mutation {
                updateJob(jobId:2, name:"updated", description:"updated", totalPositions: 3) {
                job {
                  id
                  name
                  description
                  totalPositions
                }
              }
            }
            """
        )

        self.assertIsNone(resp_0.data["updateJob"])

    def test_update_job_invalid_total_positions(self):
        """ Test for updating a job to have less totalPositions than already applied participations. """        
        """ jobId = 5 participation_job_0 """
        resp_0 = self.client.execute(
            """
            mutation {
                updateJob(jobId:5, totalPositions: 1) {     
                job {
                  id
                  name
                  description
                  totalPositions
                  participationSet {
                      id
                      user { username }
                      state
                  }
                }
              }
            }
            """
        )

        self.assertIsNone(resp_0.data["updateJob"])

    @skip
    def test_delete_job(self):
        """ Test deleting jobs """
        """ test_event_0 has jobs with id 1, 3 and 5 """
        
        resp_0 = self.client.execute(
            """
            mutation {
                deleteJob(jobId: 5) {
                    job {
                        name
                    }
                }
            }
            """
        )

        resp_1 = self.client.execute(
            """
            query {
                event(id: 1) {
                    jobSet {
                        id
                    }
                }
            }
            """
        )

        resp_2 = self.client.execute(
            """
            query {
                participations {
                    id
                    job {
                        name
                    }
                    state
                }
            }
            """
        )

        self.assertEqual(resp_0.data["deleteJob"]["job"]["name"], "participation_job_0")
        self.assertEqual(len(resp_1.data["event"]["jobSet"]), 2)
        self.assertIsNone(resp_2.data["participations"][0]["job"])
        self.assertEqual(resp_2.data["participations"][0]["state"],  5)

    def test_create_participation(self):
        resp_0 = self.client.execute(
            """
            mutation {
                createParticipation(jobId: 6) {
                    participation {
                        id
                        user { username }
                        state
                    }
                }
            }
            """
        )

        resp_1 = self.client.execute(
            """
            mutation {
                createParticipation(jobId: 6) {
                    participation {
                        id
                    }
                }
            }
            """
        )

        self.assertTrue(resp_0.data["createParticipation"]["participation"]["id"])
        self.assertEqual(resp_0.data["createParticipation"]["participation"]["user"]["username"], "test_user")
        self.assertEqual(resp_0.data["createParticipation"]["participation"]["state"], 2)
        self.assertIsNone(resp_1.data["createParticipation"])   # usser already applied

    def test_update_participation(self):
        
        """ authenticated user is event creator AND participator in this case """
        r = self.client.execute(
            """
            mutation {
                createParticipation(jobId: 3) {
                    participation {
                        id
                        user { username }
                        state
                    }
                }
            }
            """
        )
        
        resp_0 = self.client.execute(
            """
            mutation {
                updateParticipation(participationId: 3, state: 4) {
                    participation {
                        id
                        state
                    }
                }
            }
            """
        )

        resp_1 = self.client.execute(
            """
            mutation {
                updateParticipation(participationId: 3, state: 3) {
                    participation {
                        id
                        state
                    }
                }
            }
            """
        )

        resp_2 = self.client.execute(
            """
            mutation {
                updateParticipation(participationId: 3, state: 5) {
                    participation {
                        id
                        state
                    }
                }
            }
            """
        )

        """ participator is not the event creator in this case """
        self.client.execute(
            """
            mutation {
                createParticipation(jobId: 4) {
                    participation {
                        id
                        user { username }
                        state
                    }
                }
            }
            """
        )

        resp_3 = self.client.execute(
            """
            mutation {
                updateParticipation(participationId: 4, state: 3) {
                    participation {
                        id
                        state
                    }
                }
            }
            """
        )

        resp_4 = self.client.execute(
            """
            mutation {
                updateParticipation(participationId: 4, state: 4) {
                    participation {
                        id
                        state
                    }
                }
            }
            """
        )

        """ user is not the participator """
        resp_5 = self.client.execute(
            """
            mutation {
                updateParticipation(participationId: 2, state: 5) {
                    participation {
                        id
                        state
                    }
                }
            }
            """
        )

        self.assertTrue(resp_0.data["updateParticipation"]["participation"]["id"])
        self.assertEqual(resp_0.data["updateParticipation"]["participation"]["state"], 4)
        self.assertEqual(resp_1.data["updateParticipation"]["participation"]["state"], 3)
        self.assertEqual(resp_2.data["updateParticipation"]["participation"]["state"], 5)
        self.assertIsNone(resp_3.data["updateParticipation"])   # need to be event creator
        self.assertIsNone(resp_4.data["updateParticipation"])   # need to be event creator
        self.assertIsNone(resp_5.data["updateParticipation"])   # need to be participator
