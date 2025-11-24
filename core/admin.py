from django.contrib import admin
from .models import Collection, Card, User

admin.site.register(Collection)
admin.site.register(Card)
admin.site.register(User)