from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Question)
admin.site.register(Client)
admin.site.register(Reponse)
admin.site.register(Requete)
admin.site.register(Organisation)
admin.site.register(Tag)
admin.site.register(TagType)
