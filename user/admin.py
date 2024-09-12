from django.contrib import admin
from .models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'kakao_email')
    search_fields = ('user__username', 'kakao_email')

admin.site.register(UserProfile, UserProfileAdmin)