from django.contrib import admin
from .models import Recommendation

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'workout_recomendado', 'algoritmo_utilizado', 'score_confianca', 'aceita_pelo_usuario', 'data_geracao']
    list_filter = ['algoritmo_utilizado', 'aceita_pelo_usuario', 'data_geracao']
    search_fields = ['usuario__username', 'workout_recomendado__nome']
    readonly_fields = ['data_geracao', 'data_aceite']
    
    fieldsets = (
        ('Recomendação', {
            'fields': ('usuario', 'workout_recomendado')
        }),
        ('Algoritmo', {
            'fields': ('algoritmo_utilizado', 'score_confianca', 'motivo_recomendacao')
        }),
        ('Status', {
            'fields': ('aceita_pelo_usuario', 'data_geracao', 'data_aceite')
        }),
    )