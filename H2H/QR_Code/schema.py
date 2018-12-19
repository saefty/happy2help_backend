import graphene
from django.contrib.auth.models import User
from graphql_jwt.decorators import login_required
from django.core.signing import TimestampSigner


def make_token(user):
    return TimestampSigner().sign(user.username)



class Query(graphene.ObjectType):
    qr_get_token = graphene.String()
    qr_check_token = graphene.Field("User.schema.UserType", token=graphene.String())

    @login_required
    def resolve_qr_get_token(self, info, **kwargs):
        token = make_token(info.context.user)
        return token

    @login_required
    def resolve_qr_check_token(self, info, token, **kwargs):
        username = TimestampSigner().unsign(token, max_age=60 * 5)
        user = User.objects.get(username=username)
        return user



class Mutation(graphene.AbstractType):
    pass
