import graphene
import graphene_django
from django.contrib.auth.backends import UserModel

class UserType(graphene_django.DjangoObjectType):
    class Meta:
        model = UserModel

class Query(graphene.ObjectType):
    users = graphene.List(UserType)

    def resolve_users(self, info):
        return UserModel.objects.all()

schema = graphene.Schema(query=Query)
