# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.template.loader import get_template
from django.template import Context
from coop_cms.settings import get_article_class
from django.conf import settings

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

def make_link(url, label, icon, id=None, classes=None):
    icon_url = settings.STATIC_URL+icon
    
    extra_args = [u'id="{0}"'.format(id)] if id else []
    if classes:
        extra_args += [u'class="{0}"'.format(u' '.join(classes))]
        
    return u'<a href="{url}" style="background-image:url({icon_url})"{args}>{label}</a>'.format(
        url=url, icon_url=icon_url, args=u' '.join(extra_args), label=label
    )

def django_admin(request, context):
    if request.user.is_staff:
        return make_link(reverse("admin:index"), _('Administration'), 'fugue/lock.png',
            classes=['icon', 'alert_on_click'])

def django_admin_add_article(request, context):
    if request.user.is_staff:
        article_class = get_article_class()
        view_name = 'admin:%s_%s_add' % (article_class._meta.app_label,  article_class._meta.module_name)
        return make_link(reverse(view_name), _('Add article'), 'fugue/document--plus.png',
            classes=['icon', 'alert_on_click'])
        
def django_admin_edit_article(request, context):
    if request.user.is_staff and 'article' in context:
        article_class = get_article_class()
        article = context['article']
        view_name = 'admin:%s_%s_change' % (article_class._meta.app_label,  article_class._meta.module_name)
        return make_link(reverse(view_name, args=[article.id]), _('Article settings'), 'fugue/gear.png',
            classes=['icon', 'alert_on_click'])

@can_edit
def cms_media_library(request, context):
    if context['edit_mode']:
        return make_link(reverse('coop_cms_media_images'), _(u'Media library'), 'fugue/images-stack.png',
            'coopbar_medialibrary', ['icon', 'slide'])

@can_edit    
def cms_upload_image(request, context):
    if context['edit_mode']:
        return make_link(reverse('coop_cms_upload_image'), _(u'Add image'), 'fugue/images-stack.png',
            classes=['coopbar_addfile', 'colorbox-form', 'icon'])

@can_edit    
def cms_upload_doc(request, context):
    if context['edit_mode']:
        return make_link(reverse('coop_cms_upload_doc'), _(u'Add document'), 'fugue/document-pdf.png',
            classes=['coopbar_addfile', 'colorbox-form', 'icon'])

@can_edit    
def cms_change_template(request, context):
    if context['edit_mode']:
        article = context['article']
        url = reverse('coop_cms_change_template', args=[article.id])
        return make_link(url, _(u'Template'), 'fugue/application-blog.png',
            classes=['alert_on_click', 'colorbox-form', 'icon'])

@can_edit
def cms_save(request, context):
    if context['edit_mode']:
        #No link, will be managed by catching the js click event
        return make_link('', _(u'Save'), 'fugue/disk-black.png', id="coopbar_save",
            classes=['edited', 'icon'])

@can_edit
def cms_cancel(request, context):
    if context['edit_mode']:
        article = context['article']
        return make_link(article.get_cancel_url(), _(u'Cancel'), 'fugue/cross.png',
            classes=['alert_on_click', 'icon'])

@can_edit
def cms_edit(request, context):
    if not context['edit_mode']:
        article = context['article']
        return make_link(article.get_edit_url(), _(u'Edit'), 'fugue/document--pencil.png',
            classes=['icon'])

@can_publish
def cms_publish(request, context):
    if context['draft']:
        article = context['article']
        return make_link(article.get_publish_url(), _(u'Publish'), 'fugue/newspaper--arrow.png',
            classes=['publish', 'colorbox-form', 'icon'])

@can_edit
def cms_extra_js(request, context):
    t = get_template("coop_cms/_coop_bar_js.html")
    return t.render(context)

def log_out(request, context):
    if request.user.is_authenticated():
        return make_link(reverse("django.contrib.auth.views.logout"), _(u'Log out'), 'fugue/control-power.png',
            classes=['alert_on_click', 'icon'])

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
