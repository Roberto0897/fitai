from django.contrib import admin
from .models import Workout, WorkoutSession

admin.site.register(Workout)
admin.site.register(WorkoutSession)