from django.contrib import admin
from .models import UserProfile, UserProgress, DailyTip

admin.site.register(UserProfile)
admin.site.register(UserProgress)
admin.site.register(DailyTip)