import graphene
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from .models import Skill, HasSkill, Profile, Favourite


class SkillType(DjangoObjectType):
    class Meta:
        model = Skill


class HasSkillType(DjangoObjectType):
    class Meta:
        model = HasSkill


class UserType(DjangoObjectType):

    skills = graphene.List(SkillType)

    class Meta:
        model = User
        exclude_fields = ('hasskill_set',)

    # restricted Fields:
    def resolve_organisation_set(self, info):
        return field_restrictor(self, info, self.organisation_set)

    def resolve_profile(self, info):
        return field_restrictor(self, info, self.profile)

    def resolve_event_set(self, info):
        return field_restrictor(self, info, self.event_set)

    def resolve_participation_set(self, info):
        return field_restrictor(self, info, self.participation_set)

    def resolve_favourite_set(self, info):
        return field_restrictor(self, info, self.favourite_set)

    def resolve_skills(self, info):
        skills = [s.skill for s in HasSkill.objects.filter(user=self)]
        return field_restrictor(self, info, skills)


@login_required
def field_restrictor(self, info, field):
    """ allows only the user himself access on the given field"""
    if info.context.user != self:
        raise Exception("You tried to request a restricted Field")
    return field


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile


class FavouriteType(DjangoObjectType):
    class Meta:
        model = Favourite


class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)
    profile = graphene.Field(ProfileType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        birthday = graphene.types.datetime.Date()
        location = graphene.String()

    def mutate(info, username, password, email, **kwargs):
        user = User(username=username, email=email)
        user.set_password(password)
        user.save()

        profile = Profile(
            user=user,
            birthday=kwargs.get('birthday', None),
        )
        profile.save()

        return CreateUser(user=user, profile=profile)


class UpdateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        birthday = graphene.types.datetime.Date()
        email = graphene.String()
        # gps_coordinates

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        if kwargs.get('birthday', None):
            user.profile.birthday = kwargs.get('birthday', None)
        if kwargs.get('email', None):
            user.email = kwargs.get('email', None)
        user.profile.save()
        user.save()

        return UpdateUser(user=user)


class DeleteUser(graphene.Mutation):
    user = graphene.Field(UserType)

    @login_required
    def mutate(self, info):
        user = info.context.user
        user.delete()
        return DeleteUser(user)


# Queries
class Query(graphene.ObjectType):
    user = graphene.Field(UserType)
    all_users = graphene.List(UserType)
    profiles = graphene.List(ProfileType)
    favourites = graphene.List(FavouriteType)
    skills = graphene.List(SkillType)
    has_skill = graphene.List(HasSkillType)

    def resolve_user(self, info):
        if info.context.user.is_anonymous:
            raise Exception('Not logged!')
        return info.context.user

    def resolve_all_users(self, info):
        return User.objects.all()

    def resolve_profiles(self, info):
        return Profile.objects.all()

    def resolve_favourites(self, info):
        return Favourite.objects.all()

    def resolve_skills(self, info):
        return Skill.objects.all()

    def resolve_has_skill(self, info):
        return HasSkill.objects.all()


# Mutations
class Mutation(graphene.AbstractType):
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()
