# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.template.loader import get_template
from django.template import Context
from coop_cms.settings import get_article_class
from django.conf import settings
from coop_bar.utils import make_link
from django.contrib.contenttypes.models import ContentType

def can_do(perm, object_names):
    def inner_decorator(func):
        def wrapper(request, context):
            editable = context.get('editable')
            if not editable:
                return
            for object_name in object_names:
                object = context.get(object_name)
                if object and request.user.has_perm(perm+"_"+object_name, object):
                    yes_we_can = func(request, context)
                    if yes_we_can:
                        return yes_we_can
            return
        return wrapper
    return inner_decorator


can_edit_article = can_do('can_edit', ['article'])
can_publish_article = can_do('can_publish', ['article'])
can_edit_newsletter = can_do('can_edit', ['newsletter'])
can_edit = can_do('can_edit', ['article', 'newsletter'])

def can_add_article(func):
    def wrapper(request, context):
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        perm = '{0}.add_{1}'.format(ct.app_label, ct.model)
        if request.user.has_perm(perm):
            return func(request, context)
        return None
    return wrapper

def django_admin(request, context):
    if request.user.is_staff:
        return make_link(reverse("admin:index"), _(u'Administration'), 'fugue/tables.png',
            classes=['icon', 'alert_on_click'])

#def django_admin_add_article(request, context):
#    if request.user.is_staff:
#        article_class = get_article_class()
#        view_name = 'admin:%s_%s_add' % (article_class._meta.app_label,  article_class._meta.module_name)
#        return make_link(reverse(view_name), _(u'Add article'), 'fugue/document--plus.png',
#            classes=['icon', 'alert_on_click'])
        
def django_admin_edit_article(request, context):
    if request.user.is_staff and 'article' in context:
        article_class = get_article_class()
        article = context['article']
        view_name = 'admin:%s_%s_change' % (article_class._meta.app_label,  article_class._meta.module_name)
        return make_link(reverse(view_name, args=[article.id]), _(u'Article admin'), 'fugue/table.png',
            classes=['icon', 'alert_on_click'])

@can_edit
def cms_media_library(request, context):
    if context.get('edit_mode'):
        return make_link(reverse('coop_cms_media_images'), _(u'Media library'), 'fugue/images-stack.png',
            'coopbar_medialibrary', ['icon', 'slide'])

@can_edit
def cms_upload_image(request, context):
    if context.get('edit_mode'):
        return make_link(reverse('coop_cms_upload_image'), _(u'Add image'), 'fugue/image--plus.png',
            classes=['coopbar_addfile', 'colorbox-form', 'icon'])

@can_edit
def cms_upload_doc(request, context):
    if context.get('edit_mode'):
        return make_link(reverse('coop_cms_upload_doc'), _(u'Add document'), 'fugue/document-import.png',
            classes=['coopbar_addfile', 'colorbox-form', 'icon'])

@can_add_article
def cms_new_article(request, context):
        url = reverse('coop_cms_new_article')
        return make_link(url, _(u'Add article'), 'fugue/document--plus.png',
            classes=['alert_on_click', 'colorbox-form', 'icon'])

@can_edit_article    
def cms_article_settings(request, context):
    if context.get('edit_mode'):
        article = context['article']
        url = reverse('coop_cms_article_settings', args=[article.id])
        return make_link(url, _(u'Article settings'), 'fugue/gear.png',
            classes=['alert_on_click', 'colorbox-form', 'icon'])

@can_edit_article
def cms_save(request, context):
    if context.get('edit_mode'):
        #No link, will be managed by catching the js click event
        return make_link('', _(u'Save'), 'fugue/disk-black.png', id="coopbar_save",
            classes=['show-dirty', 'icon'])

@can_edit_article
def cms_view(request, context):
    if context.get('edit_mode'):
        article = context['article']
        return make_link(article.get_cancel_url(), _(u'View'), 'fugue/eye--arrow.png',
            classes=['alert_on_click', 'icon', 'show-clean'])

@can_edit_article
def cms_cancel(request, context):
    if context.get('edit_mode'):
        article = context['article']
        return make_link(article.get_cancel_url(), _(u'Cancel'), 'fugue/cross.png',
            classes=['alert_on_click', 'icon', 'show-dirty'])

@can_edit_article
def cms_edit(request, context):
    if not context.get('edit_mode'):
        article = context['article']
        return make_link(article.get_edit_url(), _(u'Edit'), 'fugue/document--pencil.png',
            classes=['icon'])

@can_publish_article
def cms_publish(request, context):
    article = context.get('article')
    if article:
        if context['draft']:
            
            return make_link(article.get_publish_url(), _(u'Draft'), 'fugue/lock.png',
                classes=['colorbox-form', 'icon'])
        else:
            return make_link(article.get_publish_url(), _(u'Published'), 'fugue/globe.png',
                classes=['colorbox-form', 'icon'])
        

def cms_extra_js(request, context):
    try:
        editable = context['editable']
        t = get_template("coop_cms/_coop_bar_js.html")
        return t.render(context)
    except KeyError:
        return None

def log_out(request, context):
    if request.user.is_authenticated():
        return make_link(reverse("django.contrib.auth.views.logout"), _(u'Log out'), 'fugue/control-power.png',
            classes=['alert_on_click', 'icon'])

@can_edit_newsletter
def edit_newsletter(request, context):
    if not context.get('edit_mode'):
        newsletter = context.get('newsletter')
        return make_link(newsletter.get_edit_url(), _(u'Edit'), 'fugue/document--pencil.png', classes=['icon'])

@can_edit_newsletter
def cancel_edit_newsletter(request, context):
    if context.get('edit_mode'):
        newsletter = context.get('newsletter')
        return make_link(newsletter.get_absolute_url(), _(u'Cancel'), 'fugue/cross.png', classes=['icon'])

@can_edit_newsletter
def save_newsletter(request, context):
    newsletter = context.get('newsletter')
    post_url = context.get('post_url')
    if context.get('edit_mode') and post_url:
        return make_link(post_url, _(u'Save'), 'fugue/disk-black.png',
            classes=['icon', 'post-form'])

@can_edit_newsletter
def change_newsletter_settings(request, context):
    if context.get('edit_mode'):
        newsletter = context.get('newsletter')
        view_name = 'admin:coop_cms_newsletter_change'
        return make_link(reverse(view_name, args=[newsletter.id]), _(u'Newsletter settings'), 'fugue/gear.png',
            classes=['icon', 'alert_on_click'])

@can_edit_newsletter
def change_newsletter_template(request, context):
    if context.get('edit_mode'):
        newsletter = context.get('newsletter')
        url = reverse('coop_cms_change_newsletter_template', args=[newsletter.id])
        return make_link(url, _(u'Newsletter template'), 'fugue/application-blog.png',
            classes=['alert_on_click', 'colorbox-form', 'icon'])

@can_edit_newsletter
def test_newsletter(request, context):
    newsletter = context.get('newsletter')
    url = reverse('coop_cms_test_newsletter', args=[newsletter.id])
    return make_link(url, _(u'Send test'), 'fugue/mail-at-sign.png',
        classes=['alert_on_click', 'colorbox-form', 'icon'])

@can_edit_newsletter
def schedule_newsletter(request, context):
    if not context.get('edit_mode'):
        newsletter = context.get('newsletter')
        url = reverse('coop_cms_schedule_newsletter_sending', args=[newsletter.id])
        return make_link(url, _(u'Schedule sending'), 'fugue/alarm-clock--arrow.png',
            classes=['alert_on_click', 'colorbox-form', 'icon'])

def load_commands(coop_bar):
    
    coop_bar.register([
        [django_admin, django_admin_edit_article],
        [edit_newsletter, cancel_edit_newsletter, save_newsletter,
            change_newsletter_settings, change_newsletter_template,
            test_newsletter, schedule_newsletter],
        [cms_edit, cms_view, cms_save, cms_cancel],
        [cms_new_article, cms_article_settings],
        [cms_publish],
        [cms_media_library, cms_upload_image, cms_upload_doc],
        [log_out]
    ])
    
    coop_bar.register_header(cms_extra_js)
