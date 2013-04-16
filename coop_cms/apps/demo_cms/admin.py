# -*- coding: utf-8 -*-
from django.contrib import admin
from coop_cms.admin import ArticleAdmin as CmsArticleAdmin

class ArticleAdmin(CmsArticleAdmin):
    fieldsets = CmsArticleAdmin.fieldsets + (
        ('Misc', {'fields': ('author',)}),
    )

from coop_cms.settings import get_article_class
admin.site.unregister(get_article_class())
admin.site.register(get_article_class(), ArticleAdmin)
