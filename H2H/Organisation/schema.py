import graphene
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from .models import Organisation


class OrganisationType(DjangoObjectType):
    class Meta:
        model = Organisation


class CreateOrganisation(graphene.Mutation):
    organisation = graphene.Field(OrganisationType)

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

        return CreateOrganisation(organisation=organisation)


class UpdateOrganisation(graphene.Mutation):
    organisation = graphene.Field(OrganisationType)

    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String()
        description = graphene.String()
        add_member = graphene.ID()
        delete_member = graphene.ID()

    @login_required
    def mutate(self, info, **kwargs):
        user = info.context.user
        organisation = Organisation.objects.get(pk=kwargs.get('id'))

        if user != organisation.admin:
            raise Exception('You have to be the admin of this organisation to update it')

        if kwargs.get('name', None):
            organisation.name = kwargs.get('name', None)
        if kwargs.get('description', None):
            organisation.description = kwargs.get('description', None)
        if kwargs.get('add_member', None):
            organisation.members.add(User.objects.get(pk=kwargs.get('add_member')))
        if kwargs.get('delete_member', None):
            to_be_deleted = User.objects.get(pk=kwargs.get('delete_member'))
            if to_be_deleted != organisation.admin:
                organisation.members.remove(to_be_deleted)
            else:
                raise Exception('You cannot remove the admin of an organisation')

        organisation.save()

        return UpdateOrganisation(organisation=organisation)


class DeleteOrganisation(graphene.Mutation):
    organisation = graphene.Field(OrganisationType)

    class Arguments:
        id = graphene.ID(required=True)

    @login_required
    def mutate(self, info, id):
        user = info.context.user
        organisation = Organisation.objects.get(pk=id)

        if user != organisation.admin:
            raise Exception('You have to be the admin of this organisation to delete it')

        organisation.delete()
        return DeleteOrganisation(organisation)


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
    delete_organisation = DeleteOrganisation.Field()
