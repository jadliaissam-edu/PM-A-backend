from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils import timezone

from .models import ActivityLog


def _get_request_meta(request):
    if not request:
        return {}
    meta = request.META
    ip = meta.get('HTTP_X_FORWARDED_FOR') or meta.get('REMOTE_ADDR')
    ua = meta.get('HTTP_USER_AGENT')
    return {'ip': ip, 'user_agent': ua}


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ct = ContentType.objects.get_for_model(user.__class__)
    meta = _get_request_meta(request)
    ActivityLog.objects.create(
        actor=user,
        content_type=ct,
        object_id=user.id,
        action='user.login',
        description=f'User logged in. meta={meta}',
        created_at=timezone.now(),
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user is None:
        return
    ct = ContentType.objects.get_for_model(user.__class__)
    meta = _get_request_meta(request)
    ActivityLog.objects.create(
        actor=user,
        content_type=ct,
        object_id=user.id,
        action='user.logout',
        description=f'User logged out. meta={meta}',
        created_at=timezone.now(),
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    # actor unknown; store as system actor if available
    user = None
    meta = _get_request_meta(request)
    # Use a dummy actor: attempt to find by email
    actor = None
    email = credentials.get('username') or credentials.get('email')
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        actor = User.objects.filter(email=email).first()
    except Exception:
        actor = None

    if actor is None:
        # skip creating if no actor available; log with system user if configured
        return

    ct = ContentType.objects.get_for_model(actor.__class__)
    ActivityLog.objects.create(
        actor=actor,
        content_type=ct,
        object_id=actor.id,
        action='user.login_failed',
        description=f'User login failed. meta={meta}',
        created_at=timezone.now(),
    )


# Profile change logging
from accounts.models import UserProfile


@receiver(pre_save, sender=UserProfile)
def capture_old_profile(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_profile = None
        return
    try:
        instance._old_profile = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._old_profile = None


@receiver(post_save, sender=UserProfile)
def log_profile_change(sender, instance, created, **kwargs):
    user = instance.user
    ct = ContentType.objects.get_for_model(user.__class__)
    if created:
        ActivityLog.objects.create(
            actor=user,
            content_type=ct,
            object_id=user.id,
            action='profile.created',
            description=f'Profile created for user {user.email}',
            new_value={
                'bio': instance.bio,
                'avatar_url': getattr(instance.avatar, 'url', None) or instance.avatar_url,
                'preferences': instance.preferences_json,
            },
            created_at=timezone.now(),
        )
    else:
        old = getattr(instance, '_old_profile', None)
        old_value = None
        if old:
            old_value = {
                'bio': old.bio,
                'avatar_url': getattr(old.avatar, 'url', None) or old.avatar_url,
                'preferences': old.preferences_json,
            }
        new_value = {
            'bio': instance.bio,
            'avatar_url': getattr(instance.avatar, 'url', None) or instance.avatar_url,
            'preferences': instance.preferences_json,
        }
        ActivityLog.objects.create(
            actor=user,
            content_type=ct,
            object_id=user.id,
            action='profile.updated',
            description=f'Profile updated for user {user.email}',
            old_value=old_value,
            new_value=new_value,
            created_at=timezone.now(),
        )
