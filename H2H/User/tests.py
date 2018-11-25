"""
from django.contrib.auth import get_user_model

from graphql_jwt.testcases import JSONWebTokenTestCase

from User.models import Skill, HasSkill, Profile


class UsersTests(JSONWebTokenTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create(username='tOor', password='testtest')

    def setUp(self):
        self.client.authenticate(self.user)

    def test_profile_is_created(self):
        self.assertIsInstance(self.user.profile, Profile)

    def test_edit_birthday(self):
        self.client.execute(
            """"""
            mutation {
              updateUser(birthday:"1986-11-20"){
                user {
                  profile {
                    birthday
                  }
                }
              }
            }
            """"""
        )

        resp = self.client.execute("query{user{profile{birthday}}}")
        self.assertEqual(resp.data['user']['profile']['birthday'], '1986-11-20')

    def test_invalid_birthday(self):
        resp = self.client.execute(
            """"""
            mutation {
              updateUser(birthday:1){
                user {
                  profile {
                    birthday
                  }
                }
              }
            }
            """"""
        )
        self.assertTrue(resp.errors)

    def test_credit_points_are_zero(self):
        resp = self.client.execute(
            """"""
            query {
              user {
                profile {
                  creditPoints
                }
              }
            }
            """"""
        )
        self.assertEqual(resp.data['user']['profile']['creditPoints'], 0)

    def test_increase_credit_points(self):
        resp = self.client.execute(
            """"""
            mutation {
              updateUser(creditPoints:10){
                user {
                  profile {
                    creditPoints
                  }
                }
              }
            }
            """"""
        )

        self.assertEqual(resp.data['updateUser']['user']['profile']['creditPoints'], 10)

    def test_negative_credit_points(self):
        pass
        # TODO: SQLite does not validate PositiveIntegerField.
        # with self.assertRaises(AssertionError):
        #     self.user.profile.credit_points -= 10
        #     self.user.profile.save()

    def test_create_skill(self):
        resp = self.client.execute(
            """"""
            mutation {
              createSkill(name:"Flechten") {
                    skill {
                  name
                }
              }
            }
            """"""
        )

        self.assertTrue(resp.data['createSkill']['skill']['name'] == 'Flechten')

        # HasSkill should also be created and user.skills should have an entry
        resp = self.client.execute(
            """"""
            query {
              user {
                skills {
                  name
                }
              }
            }
            """""""
        )
        self.assertTrue('Flechten' in [s['name'] for s in resp.data['user']['skills']])

    def test_delete_skill(self):

        # create Skill and HasSkill first
        skill = Skill.objects.create(name="Hobeln")
        hasskill = HasSkill.objects.create(user=self.user, skill=skill)

        resp = self.client.execute(
            """"""
            mutation {
              deleteSkill(skillId:1) {
                skill {
                  name
                }
              }
            }
            """"""
        )

        self.assertTrue(resp.data['deleteSkill']['skill']['name'] == 'Hobeln')

        # Skill should not have been deleted. Only the HasSkill
        self.assertTrue(Skill.objects.filter(name="Hobeln").exists())
        self.assertFalse(HasSkill.objects.filter(user=self.user).exists())
"""