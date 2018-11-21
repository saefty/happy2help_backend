import graphene
from graphene_django import DjangoObjectType

from .models import Rating, Report


class RatingType(DjangoObjectType):
    class Meta:
        model = Rating


class ReportType(DjangoObjectType):
    class Meta:
        model = Report


# Queries
class Query(graphene.ObjectType):
    ratings = graphene.List(RatingType)
    reports = graphene.List(ReportType)

    def resolve_ratings(self, info, id):
        return Rating.objects.all()

    def resolve_reports(self, info, id):
        return Report.objects.all()


# Mutations
class Mutation(graphene.AbstractType):
    pass
