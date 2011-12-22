# -*- coding: utf-8 -*-
import inspect

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, AnonymousUser
from django.utils.importlib import import_module


class ArticlePermissionBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def authenticate(self, username, password):
        return None

    def has_perm(self, user_obj, perm, obj=None):
        if obj:
            field = getattr(obj, perm, None)
            if field:
                if not callable(field):
                    is_authorized = field
                else:
                    is_authorized = field(user_obj)
                return is_authorized
        return False
