import graphene
import graphql_jwt
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from Event.models import Event
from Event.schema import EventType
from .models import Skill, HasSkill, Profile, Favourite


# Types
class FavouriteType(DjangoObjectType):
    class Meta:
        model = Favourite


class SkillType(DjangoObjectType):
    approved = graphene.Boolean()

    class Meta:
        model = Skill
        exclude_fields = ('hasskill_set',)

    def resolve_approved(self, info):
        return HasSkill.objects.get(user=info.context.user, skill=self).approved


class HasSkillType(DjangoObjectType):
    class Meta:
        model = HasSkill


class UserType(DjangoObjectType):
    skills = graphene.List(SkillType)

    class Meta:
        model = User

    def resolve_skills(self, info):
        return [s.skill for s in HasSkill.objects.filter(user=self)]


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile
        exclude_fields = ('user',)


# create user and profile
class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        birthday = graphene.types.datetime.Date()

    def mutate(self, info, username, password, email, **kwargs):
        # save user
        user = User(username=username, email=email)
        user.set_password(password)
        user.save()

        # save profile
        user.profile.birthday = kwargs.get('birthday', None)
        user.profile.save()

        return CreateUser(user=user)


# update user and profile
class UpdateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        email = graphene.String()
        birthday = graphene.types.datetime.Date()
        credit_points = graphene.Int()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        # users old email if email=""
        user.email = user.email if not kwargs.get('email', None) else kwargs["email"]
        user.profile.birthday = kwargs.get('birthday', user.profile.birthday)
        user.profile.credit_points = kwargs.get('credit_points', user.profile.credit_points)
        user.save()
        user.profile.save()
        return UpdateUser(user=user)


# delete user and profile
class DeleteUser(graphene.Mutation):
    """Profile will be deleted automatically (CASCADE)"""
    user = graphene.Field(UserType)

    @login_required
    def mutate(self, info):
        user = info.context.user
        user.delete()
        return DeleteUser(user=user)


# create skill
class CreateSkill(graphene.Mutation):
    # TODO: make it impossible to create multiple hasskills
    skill = graphene.Field(SkillType)

    class Arguments:
        name = graphene.String()

    @login_required
    def mutate(self, info, name):
        skill, created = Skill.objects.get_or_create(name=name)
        HasSkill.objects.create(user=info.context.user, skill=skill)
        return CreateSkill(skill=skill)


# delete has_skill
class DeleteSkill(graphene.Mutation):
    """Deletes only the HasSkill"""
    skill = graphene.Field(SkillType)

    class Arguments:
        skill_id = graphene.ID()

    @login_required
    def mutate(self, info, skill_id):
        skill = Skill.objects.get(id=skill_id)
        has_skill = HasSkill.objects.get(user=info.context.user, skill=skill)
        has_skill.delete()
        return DeleteSkill(skill=skill)


class CreateFavourite(graphene.Mutation):
    user = graphene.Field(UserType)
    event = graphene.Field(EventType)

    class Arguments:
        event_id = graphene.ID()

    @login_required
    def mutate(self, info, event_id):
        event = Event.objects.get(id=event_id)
        Favourite.objects.create(user=info.context.user, event=event)
        return CreateFavourite(user=info.context.user, event=event)


class Query(graphene.ObjectType):
    user = graphene.Field(UserType)

    def resolve_user(self, info):
        return User.objects.get(id=info.context.user.id)


class Mutation(graphene.AbstractType):
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()

    create_skill = CreateSkill.Field()
    delete_skill = DeleteSkill.Field()

    create_favourite = CreateFavourite.Field()

    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
