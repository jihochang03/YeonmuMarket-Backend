from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.socialaccount.signals import social_account_added
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)

@receiver(social_account_added)
def social_login_callback(request, sociallogin, **kwargs):
    user = sociallogin.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    if created or not profile.kakao_email:
        kakao_account = sociallogin.account.extra_data.get('kakao_account', {})
        profile.kakao_email = kakao_account.get('email', '')
        profile.save()
