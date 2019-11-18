from rest_framework import filters
from user.models import User


class AdminOrOwnerFilter(filters.BaseFilterBackend):
    """
    Filter that hides others people alerts from
    non staff users.
    """

    def filter_queryset(self, request, queryset, view):
        if "user" in view.kwargs:
            target_user = User.objects.get(id=view.kwargs["user"])
            queryset = queryset.filter(user=target_user)
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user)
        return queryset
