import graphene
import graphene_django
from django.contrib.auth.backends import UserModel
from .models import Book, HasRead

class UserType(graphene_django.DjangoObjectType):
    is_admin = graphene.Boolean()

    def resolve_is_admin(self, info):
        return self.is_staff

    class Meta:
        model = UserModel
        only_fields = ('id', 'username', 'books_read')

class BookType(graphene_django.DjangoObjectType):
    average_rating = graphene.Float()

    def resolve_average_rating(self, info):
        all_book_reads = HasRead.objects.all()
        this_book_reads = all_book_reads.filter(book=self.id)
        book_ratings = list(map(lambda read: read.rating, this_book_reads))

        # print(f"${self.title}: ${book_ratings}") # control

        if book_ratings:
            return sum(book_ratings) / len(book_ratings)
        else: return None

    class Meta:
        model = Book

class HasReadType(graphene_django.DjangoObjectType):
    class Meta:
        model = HasRead

class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    books = graphene.List(BookType, fiction=graphene.Boolean())

    def resolve_users(self, info):
        return UserModel.objects.all()

    def resolve_books(self, info, **kwargs):
        q = Book.objects.all()

        fiction = kwargs.get('fiction')
        if fiction is not None:
            q = q.filter(fiction=fiction)

        return q

schema = graphene.Schema(query=Query)
