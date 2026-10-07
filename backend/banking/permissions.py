from rest_framework.exceptions import PermissionDenied

from banking.models import Profile


def is_admin(user):
    profile = getattr(user, 'profile', None)
    return bool(user.is_staff or (profile and profile.role == Profile.Role.ADMIN))


def owned_account_id(user):
    profile = getattr(user, 'profile', None)
    return profile.account_id if profile and profile.account_id else None


def require_admin(request):
    if not is_admin(request.user):
        raise PermissionDenied('Admin access required.')
