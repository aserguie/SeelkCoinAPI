import requests
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from api.settings import BASE_URL
from .filters import AdminOrOwnerFilter
from .models import Alert
from .serializers import AlertSerializer


class AlertViewSet(viewsets.ModelViewSet):
    """"
    A regular user can CRUD his own alerts on alerts/ route
    A staff user can also CRUD alerts for other users on users/ route
    """

    model = Alert
    serializer_class = AlertSerializer
    queryset = Alert.objects
    filter_backends = (AdminOrOwnerFilter,)

    def get_permissions(self):
        """ Only admin user can access to /users/ route"""
        context = self.get_serializer_context()
        if "user" in context["view"].kwargs:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            response = requests.get(url=BASE_URL + "assets")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return Response(data=str(e), status=status.HTTP_400_BAD_REQUEST)
        alert = serializer.create(request.data, response)
        request.data["id"] = alert.id
        return Response(data=request.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if "base_currency" not in request.data:
            request.data["base_currency"] = instance.base_currency
        if "quote_currency" not in request.data:
            request.data["quote_currency"] = instance.quote_currency
        try:
            response = requests.get(url=BASE_URL + "assets")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return Response(data=str(e), status=status.HTTP_400_BAD_REQUEST)
        serializer.update(instance, request.data, response)
        request.data["id"] = instance.id
        return Response(data=request.data, status=status.HTTP_200_OK)
