# -*- coding: utf-8 -*-
from django.contrib import admin
from django.core.urlresolvers import reverse
import models
from forms import NavTypeForm, ArticleAdminForm, NewsletterItemAdminForm, NewsletterAdminForm
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from coop_cms.settings import get_article_class, get_navTree_class


class NavNodeAdmin(admin.ModelAdmin):
    list_display = ["label", 'parent', 'ordering', 'in_navigation', 'content_type', 'object_id']

admin.site.register(models.NavNode, NavNodeAdmin)


class NavTypeAdmin(admin.ModelAdmin):
    form = NavTypeForm

admin.site.register(models.NavType, NavTypeAdmin)


class NavTreeAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'name', 'navtypes_list']
    list_editable = ['name']
    list_filters = ['id']

    def nodes_li(self, tree):
        root_nodes = tree.get_root_nodes()
        nodes_li = u''.join([node.as_jstree() for node in root_nodes])
        return nodes_li

    def navtypes_list(self, tree):
        if tree.types.count() == 0:
            return _(u'All')
        else:
            return u' - '.join([unicode(x) for x in tree.types.all()])
    navtypes_list.short_description = _(u'navigable types')

    def change_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        tree = models.get_navTree_class().objects.get(id=object_id)
        extra_context['navtree'] = tree
        extra_context['navtree_nodes'] = self.nodes_li(tree)
        return super(NavTreeAdmin, self).change_view(request, object_id,
            extra_context=extra_context)

admin.site.register(get_navTree_class(), NavTreeAdmin)


class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ['slug', 'title', 'publication', 'is_homepage', 'in_newsletter', 'category', 'modified']
    list_editable = ['publication', 'is_homepage', 'in_newsletter', 'category']
    readonly_fields = ['slug', 'created', 'modified']
    fieldsets = (
        #(_('Navigation'), {'fields': ('navigation_parent',)}),
        (_('General'), {'fields': ('slug', 'title', 'content')}),
        (_('Advanced'), {'fields': ('template', 'category', 'logo', 'is_homepage', 'in_newsletter')}),
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
admin.site.register(models.NewsletterSending)


class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'ordering']
    list_editable = ['ordering']
admin.site.register(models.ArticleCategory, ArticleCategoryAdmin)

#class NewsletterItemAdmin(admin.ModelAdmin):
#    form = NewsletterItemAdminForm
#    list_display = ['content_object']
#    fieldsets = (
#        (_('Article'), {'fields': ('object_id', 'content_type')}),
#    )
#
#admin.site.register(models.NewsletterItem, NewsletterItemAdmin)


class NewsletterAdmin(admin.ModelAdmin):
    form = NewsletterAdminForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(NewsletterAdmin, self).get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

admin.site.register(models.Newsletter, NewsletterAdmin)
