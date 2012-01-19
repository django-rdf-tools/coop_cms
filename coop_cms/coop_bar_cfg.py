# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.template.loader import get_template
from django.template import Context
from coop_cms.settings import get_article_class

def django_admin(request, context):
    if request.user.is_staff:
        return u'<a class="alert_on_click icon"\
                    style="background-image:url(/static/fugue/lock.png)"\
                    href="{0}">{1}</a>'.format(reverse("admin:index"), _('Administration'))

def django_admin_add_article(request, context):
    if request.user.is_staff:
        article_class = get_article_class()
        view_name = 'admin:%s_%s_add' % (article_class._meta.app_label,  article_class._meta.module_name)
        return u'<a class="alert_on_click icon"\
                    style="background-image:url(/static/fugue/document--plus.png)"\
                    href="{0}">{1}</a>'.format(reverse(view_name), _('Add article'))
        
def django_admin_edit_article(request, context):
    if request.user.is_staff and 'article' in context:
        article_class = get_article_class()
        article = context['article']
        view_name = 'admin:%s_%s_change' % (article_class._meta.app_label,  article_class._meta.module_name)
        return u'<a class="alert_on_click icon"\
                    style="background-image:url(/static/fugue/gear.png)"\
                    href="{0}">{1}</a>'.format(reverse(view_name, args=[article.id]), _('Article settings'))

def can_do(perm):
    def inner_decorator(func):
        def wrapper(request, context):
            try:
                editable = context['editable']
                article = context['article']
                if editable and request.user.has_perm(perm, article):
                    return func(request, context)
            except KeyError:
                pass
            return None
        return wrapper
    return inner_decorator

can_edit = can_do('can_edit_article')
can_publish = can_do('can_publish_article')


@can_edit
def cms_media_library(request, context):
    if context['edit_mode']:
        return u'<a href="{0}" id="coopbar_medialibrary"\
                    style="background-image:url(/static/fugue/images-stack.png)"\
                    class="icon slide">{1}</a>'.format(reverse('coop_cms_media_images'), _('Media library'))

@can_edit    
def cms_upload_image(request, context):
    if context['edit_mode']:
        return u'<a href="{0}" class="coopbar_addfile colorbox-form icon"\
                    style="background-image:url(/static/fugue/image--plus.png)"\
                    >{1}</a>'.format(reverse('coop_cms_upload_image'), _('Add image'))

@can_edit    
def cms_upload_doc(request, context):
    if context['edit_mode']:
        return u'<a href="{0}" class="coopbar_addfile colorbox-form icon"\
                    style="background-image:url(/static/fugue/document-pdf.png)"\
                    >{1}</a>'.format(reverse('coop_cms_upload_doc'), _('Add document'))

@can_edit    
def cms_change_template(request, context):
    if context['edit_mode']:
        article = context['article']
        url = reverse('coop_cms_change_template', args=[article.id])
        return u'<a class="alert_on_click colorbox-form icon"\
                    style="background-image:url(/static/fugue/application-blog.png)"\
                    href="{0}">{1}</a>'.format(url, _('Template'))

@can_edit
def cms_save(request, context):
    if context['edit_mode']:
        return u'<a class="edited icon" id="coopbar_save"\
                    style="background-image:url(/static/fugue/disk-black.png)"\
                    href="{0}">{1}</a>'.format('', _('Save'))

@can_edit
def cms_cancel(request, context):
    if context['edit_mode']:
        article = context['article']
        return u'<a class="alert_on_click icon"\
                    style="background-image:url(/static/fugue/cross.png)"\
                    href="{0}">{1}</a>'.format(article.get_cancel_url(), _('Cancel'))

@can_edit
def cms_edit(request, context):
    if not context['edit_mode']:
        article = context['article']
        return u'<a href="{0}" class="icon"\
                    style="background-image:url(/static/fugue/document--pencil.png)"\
                    >{1}</a>'.format(article.get_edit_url(), _('Edit'))

@can_publish
def cms_publish(request, context):
    if context['draft']:
        article = context['article']
        return u'<a class="publish colorbox-form icon"\
                    style="background-image:url(/static/fugue/newspaper--arrow.png)"\
                    href="{0}">{1}</a>'.format(article.get_publish_url(), _('Publish'))

@can_edit
def cms_extra_js(request, context):
    t = get_template("coop_cms/_coop_bar_js.html")
    return t.render(context)

def log_out(request, context):
    if request.user.is_authenticated():
        return u'<a class="alert_on_click icon"\
                    style="background-image:url(/static/fugue/control-power.png)"\
                    href="{0}">{1}</a>'.format(reverse("django.contrib.auth.views.logout"), _('Log out'))

def load_commands(coop_bar):
    coop_bar.register_command(django_admin)
    coop_bar.register_command(django_admin_add_article)
    coop_bar.register_command(django_admin_edit_article)
    coop_bar.register_separator()
    coop_bar.register_command(cms_media_library)
    coop_bar.register_command(cms_upload_image)
    coop_bar.register_command(cms_upload_doc)
    coop_bar.register_separator()
    coop_bar.register_command(cms_edit)
    coop_bar.register_separator()
    coop_bar.register_command(cms_change_template)
    coop_bar.register_separator()
    coop_bar.register_command(cms_save)
    coop_bar.register_command(cms_publish)
    coop_bar.register_command(cms_cancel)
    coop_bar.register_separator()
    coop_bar.register_command(log_out)
    
    coop_bar.register_header(cms_extra_js)
