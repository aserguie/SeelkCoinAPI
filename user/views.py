from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from user.serializers import UserSerializer
from .models import User


@api_view(["POST"])
@permission_classes([AllowAny])
def registration_view(request):
    serializer = UserSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.create(request.data)
        request.data["token"] = Token.objects.get(user=user).key
        request.data["id"] = user.id
        return Response(request.data)
    else:
        return Response(serializer.errors)


@api_view(["POST"])
def logout_view(request):
    request.user.auth_token.delete()
    return Response(status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    This serializer corresponds to the /users route.
    It is reserved for staff users, they can list all users or get
    details on a specific user and his alerts on this route. All
    basic CRUD actions are allowed
    """

    model = User
    queryset = User.objects
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)


class SelfUserViewSet(viewsets.ModelViewSet):
    """
    This serializer corresponds to the /me route and returns the
    authenticated user's credentials. Basic CRUD actions are allowed
    """

    model = User
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
