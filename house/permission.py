from rest_framework import permissions


class IsPremiumUser(permissions.BasePermission):
    """Faqat premium foydalanuvchilarga Create ruxsati beradi"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'is_premium', False))


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Faqat uy egasiga tahrirlash/o'chirish ruxsati beradi"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class CanChatPermission(permissions.BasePermission):
    """
    Faqat Premium foydalanuvchilar xabar yubora oladi.
    Uy egalari esa (premium bo'lmasa ham) kelgan xabarlarga javob qaytara olishi uchun
    mantiqni biroz kengaytiramiz.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.method == 'POST':
            return getattr(request.user, 'is_premium', False)

        return True