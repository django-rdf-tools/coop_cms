# -*- coding: utf-8 -*-
from django.contrib import admin
from django.core.urlresolvers import reverse
import models
from forms import NavTypeForm, ArticleAdminForm
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from coop_cms.settings import get_article_class

class NavNodeAdmin(admin.ModelAdmin):
    list_display = ["label", 'parent', 'ordering', 'in_navigation', 'content_type', 'object_id']

admin.site.register(models.NavNode, NavNodeAdmin)


class NavTypeAdmin(admin.ModelAdmin):
    form = NavTypeForm
    
admin.site.register(models.NavType, NavTypeAdmin)

class NavTreeAdmin(admin.ModelAdmin):

    def nodes_li(self):
        root_nodes = models.NavNode.objects.filter(parent__isnull=True).order_by("ordering")
        nodes_li = u''.join([node.as_jstree() for node in root_nodes])
        return nodes_li
    
    def suggest_list_url(self):
        return reverse('object_suggest_list')
        
    def get_absolute_url(self):
        return reverse('navigation_tree')

admin.site.register(models.NavTree, NavTreeAdmin)

class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ['slug', 'title', 'publication', 'created', 'modified']
    list_editable = ['publication']
    readonly_fields = ['slug', 'created', 'modified']
    fieldsets = (
        (_('Navigation'), {'fields': ('navigation_parent',)}),
        (_('General'), {'fields': ('slug', 'title', 'content',)}),
        (_('Advanced'), {'fields': ('template', 'section', 'logo')}),
        (_('Publication'), {'fields': ('publication', 'created', 'modified')}),
        (_('Summary'), {'fields': ('summary',)}),
        (_('Debug'), {'fields': ('temp_logo',)}),
    )
    def get_form(self, request, obj=None, **kwargs):
        form = super(ArticleAdmin, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form
admin.site.register(get_article_class(), ArticleAdmin)

admin.site.register(models.Link)
admin.site.register(models.Document)
admin.site.register(models.Image)
admin.site.register(models.PieceOfHtml)