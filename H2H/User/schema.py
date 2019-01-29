import graphene
import graphql_jwt
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.postgres.search import TrigramSimilarity
from django.core.validators import validate_email
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from Event.models import Event
from Event.schema import EventType
from Location.models import Location
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
    event_set = graphene.List(EventType)

    class Meta:
        model = User

    def resolve_skills(self, info):
        return [s.skill for s in HasSkill.objects.filter(user=self)]

    def resolve_event_set(self, info):
        return [event for event in Event.objects.filter(creator=self, organisation=None)]


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile
        exclude_fields = ('user',)


# create user and profile
class CreateUser(graphene.Mutation):
    id = graphene.ID()
    username = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    email = graphene.String()
    profile = graphene.Field(ProfileType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        birthday = graphene.types.datetime.Date()
        location_id = graphene.ID()

    def mutate(self, info, username, password, email, **kwargs):
        # save user
        validate_email(email)
        user = User(username=username, email=email)
        validate_password(password=password, user=user)
        user.set_password(password)

        first_name = kwargs.get("first_name", None)
        if first_name:
            user.first_name = first_name
        last_name = kwargs.get("last_name", None)
        if last_name:
            user.last_name = last_name

        user.save()

        # save profile
        user.profile.birthday = kwargs.get('birthday', None)
        location_id = kwargs.get('location_id', None)
        if location_id:
            user.profile.location = Location.objects.get(id=location_id)
        user.profile.save()

        return CreateUser(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            profile=user.profile
        )


# update user and profile
class UpdateUser(graphene.Mutation):
    id = graphene.ID()
    username = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    email = graphene.String()
    profile = graphene.Field(ProfileType)

    class Arguments:
        email = graphene.String()
        birthday = graphene.types.datetime.Date()
        credit_points = graphene.Int()
        location_id = graphene.ID()
        first_name = graphene.String()
        last_name = graphene.String()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        # users old email if email=""
        email = kwargs.get("email", None)
        if email:
            validate_email(email)
            user.email = email
        user.profile.birthday = kwargs.get('birthday', user.profile.birthday)
        user.profile.credit_points = kwargs.get('credit_points', user.profile.credit_points)
        location_id = kwargs.get('location_id', None)
        if location_id:
            location = Location.objects.get(id=location_id)
            user.profile.location = location
        first_name = kwargs.get("first_name", None)
        if first_name:
            user.first_name = first_name
        last_name = kwargs.get("last_name", None)
        if last_name:
            user.last_name = last_name
        user.save()
        user.profile.save()
        return UpdateUser(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            profile=user.profile
        )


# delete user and profile
class DeleteUser(graphene.Mutation):
    """Profile will be deleted automatically (CASCADE)"""
    id = graphene.ID()

    @login_required
    def mutate(self, info):
        user = info.context.user
        user_id = user.id
        user.delete()
        return DeleteUser(id=user_id)


# create skill
class CreateSkill(graphene.Mutation):
    # TODO: make it impossible to create multiple hasskills
    id = graphene.ID()
    name = graphene.String()
    created = graphene.Boolean()

    class Arguments:
        name = graphene.String()

    @login_required
    def mutate(self, info, name):
        skill, created = Skill.objects.get_or_create(name=name)
        HasSkill.objects.create(user=info.context.user, skill=skill)
        return CreateSkill(
            id=skill.id,
            name=skill.name,
            created=created
        )


# delete has_skill
class DeleteSkill(graphene.Mutation):
    """Deletes only the HasSkill"""
    has_skill_id = graphene.ID()

    class Arguments:
        skill_id = graphene.ID()

    @login_required
    def mutate(self, info, skill_id):
        skill = Skill.objects.get(id=skill_id)
        has_skill = HasSkill.objects.get(user=info.context.user, skill=skill)
        has_skill_id = has_skill.id
        has_skill.delete()
        return DeleteSkill(has_skill_id=has_skill_id)


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
    find_participant = graphene.Field(UserType, user_id=graphene.ID())
    skill_search = graphene.List(SkillType, query=graphene.String())

    def resolve_user(self, info):
        return User.objects.get(id=info.context.user.id)

    def resolve_skill_search(self, info, query):
        skills = Skill.objects.annotate(similarity=TrigramSimilarity('name', query)) \
            .filter(similarity__gt=0.1) \
            .order_by('-similarity')[:5]
        return skills

    @login_required
    def resolve_find_participant(self, info, user_id):
        return User.objects.get(id=user_id)


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
