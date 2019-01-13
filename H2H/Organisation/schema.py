import graphene
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from .models import Organisation


class OrganisationType(DjangoObjectType):
    class Meta:
        model = Organisation


class CreateOrganisation(graphene.Mutation):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    admin = graphene.Field("User.schema.UserType")
    members = graphene.List("User.schema.UserType")

    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String(required=True)

    @login_required
    def mutate(self, info, **kwargs):
        organisation = Organisation(
            admin=info.context.user,
            name=kwargs.get('name'),
            description=kwargs.get('description')
        )
        organisation.save()
        organisation.members.add(info.context.user)

        return CreateOrganisation(
            id=organisation.id,
            name=organisation.name,
            description=organisation.description,
            admin=organisation.admin,
            members=organisation.members
        )


class UpdateOrganisation(graphene.Mutation):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    admin = graphene.Field("User.schema.UserType")
    members = graphene.List("User.schema.UserType")

    class Arguments:
        organisation_id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        organisation = Organisation.objects.get(pk=kwargs.get('organisation_id'))

        if user != organisation.admin:
            raise Exception('You have to be the admin of this organisation to update it')

        if kwargs.get('name', None):
            organisation.name = kwargs.get('name', None)
        if kwargs.get('description', None):
            organisation.description = kwargs.get('description', None)

        organisation.save()

        return UpdateOrganisation(
            id=organisation.id,
            name=organisation.name,
            description=organisation.description,
            admin=organisation.admin,
            members=organisation.members
        )


class AddMember(graphene.Mutation):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    admin = graphene.Field("User.schema.UserType")
    members = graphene.List("User.schema.UserType")

    class Arguments:
        organisation_id = graphene.ID(required=True)
        username = graphene.String(required=True)

    @login_required
    def mutate(self, info, organisation_id, username):
        user = info.context.user
        organisation = Organisation.objects.get(pk=organisation_id)

        if user != organisation.admin:
            raise Exception('You have to be the admin of this organisation to add members to it')

        organisation.members.add(User.objects.get(username=username))
        organisation.save()

        return AddMember(
            id=organisation.id,
            name=organisation.name,
            description=organisation.description,
            admin=organisation.admin,
            members=organisation.members
        )

    
class RemoveMembers(graphene.Mutation):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    admin = graphene.Field("User.schema.UserType")
    members = graphene.List("User.schema.UserType")

    class Arguments:
        organisation_id = graphene.ID(required=True)
        user_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)

    @login_required
    def mutate(self, info, organisation_id, user_ids):
        user = info.context.user
        organisation = Organisation.objects.get(pk=organisation_id)

        if user != organisation.admin:
            raise Exception('You have to be the admin of this organisation to delete its members')

        for id in user_ids:
            to_be_deleted = User.objects.get(pk=id)
            if to_be_deleted != organisation.admin:
                organisation.members.remove(to_be_deleted)
            else:
                raise Exception('You cannot remove the admin of an organisation')
        
        organisation.save()

        return RemoveMembers(
            id=organisation.id,
            name=organisation.name,
            description=organisation.description,
            admin=organisation.admin,
            members=organisation.members
        )


class DeleteOrganisation(graphene.Mutation):
    id = graphene.ID()

    class Arguments:
        organisation_id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, organisation_id):
        user = info.context.user
        organisation = Organisation.objects.get(id=organisation_id)

        if user != organisation.admin:
            raise Exception('You have to be the admin of this organisation to delete it')

        organisation.delete()
        return DeleteOrganisation(id=organisation_id)


# Queries
class Query(graphene.ObjectType):
    organisations = graphene.List(OrganisationType)
    organisation = graphene.Field(OrganisationType, id=graphene.ID())

    def resolve_organisations(self, info):
        return Organisation.objects.all()

    def resolve_organisation(self, info, id):
        return Organisation.objects.get(id=id)

# Mutations
class Mutation(graphene.AbstractType):
    create_organisation = CreateOrganisation.Field()
    update_organisation = UpdateOrganisation.Field()
    add_member = AddMember.Field()
    remove_members = RemoveMembers.Field()
    delete_organisation = DeleteOrganisation.Field()
