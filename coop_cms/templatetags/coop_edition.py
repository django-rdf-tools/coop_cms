# -*- coding: utf-8 -*-

from django import template
register = template.Library()
from djaloha.templatetags.djaloha_utils import DjalohaEditNode
from coop_cms.models import PieceOfHtml, BaseArticle
from django.utils.translation import ugettext_lazy as _
from django.core.context_processors import csrf
from django.utils.safestring import mark_safe
from coop_cms.widgets import ImageEdit

################################################################################
class PieceOfHtmlEditNode(DjalohaEditNode):
    def render(self, context):
        if context.get('coop_cms_article_form', None):
            context.dicts[0]['djaloah_edit'] = True
        #context.dicts[0]['can_edit_template'] = True
        return super(PieceOfHtmlEditNode, self).render(context)

@register.tag
def coop_piece_of_html(parser, token):
    div_id = token.split_contents()[1]
    return PieceOfHtmlEditNode(PieceOfHtml, {'div_id': div_id}, 'content')

################################################################################
class ArticleTitleNode(template.Node):
    
    def render(self, context):
        is_edition_mode = context.get('coop_cms_article_form', None)!=None
        article = context.get('article')
        return u"{0}".format(
            article.title,
            _(u" [EDITION]") if is_edition_mode else u"",
            _(u" [DRAFT]") if article.publication == BaseArticle.PUBLISHED else u"",
        )

@register.tag
def article_title(parser, token):
    return ArticleTitleNode()
    
################################################################################

class ArticleFormMediaNode(template.Node):
    
    def render(self, context):
        coop_cms_article_form = context.get('coop_cms_article_form', None)
        if coop_cms_article_form:
            t = template.Template("{{form.media}}")
            return t.render(template.Context({'form': coop_cms_article_form}))
        else:
            return ""

@register.tag
def article_form_media(parser, token):
    return ArticleFormMediaNode()

################################################################################

class IfArticleEditionNode(template.Node):
    
    def __init__(self, nodelist_true, nodelist_false):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        
    def __iter__(self):
        for node in self.nodelist_true:
            yield node
        for node in self.nodelist_false:
            yield node    

    def render(self, context):
        coop_cms_article_form = context.get('coop_cms_article_form', None)
        if coop_cms_article_form:
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)

@register.tag
def if_article_edition(parser, token):
    nodelist_true = parser.parse(('else', 'endif'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endif',))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfArticleEditionNode(nodelist_true, nodelist_false)

################################################################################
article_form_template = """
    <form id="article_form" enctype="multipart/form-data"  method="POST" action="{{post_url}}">{% csrf_token %}
    {% include "coop_cms/_form_error.html" with errs=form.non_field_errors %}
    {{inner}} <input type="submit"> </form>
"""

class SafeWrapper:
    
    def __init__(self, wrapped, logo_size=None):
        self._wrapped = wrapped
        self._logo_size = logo_size
    
    def __getattr__(self, field):
        value = getattr(self._wrapped, field)
        if field=='logo':
            src = getattr(self._wrapped, 'logo_thumbnail')(False, self._logo_size)
            if src:
                value = u'<img class="article-logo" src="{0}">'.format(src.url)
            else:
                value = u'' #TODO : default icon
        return mark_safe(value)

class FormWrapper:
    
    def __init__(self, form, logo_size=None):
        self._form = form
        if logo_size:
            self._form.set_logo_size(logo_size)
    
    def __getitem__(self, field, logo_size=None):
        if field in self._form.fields.keys():
            t = template.Template("""
                    {%% with form.%s.errors as errs %%}{%% include "coop_cms/_form_error.html" %%}{%% endwith %%}{{form.%s}}
                """ % (field, field))
            return t.render(template.Context({'form': self._form}))

class ArticleNode(template.Node):
    
    def __init__(self, nodelist_article, logo_size=None):
        self.nodelist_article = nodelist_article
        self._logo_size = logo_size
        
    def __iter__(self):
        for node in self.nodelist_article:
            yield node

    def render(self, context):
        coop_cms_article_form = context.get('coop_cms_article_form', None)
        request = context.get('request')
        article = context.get('article')
        inner_context = {}
        for x in context.dicts:
            inner_context.update(x)
        outer_context = {'post_url': article.get_edit_url()}
        
        if coop_cms_article_form:
            t = template.Template(article_form_template)
            inner_context['article'] = FormWrapper(coop_cms_article_form, logo_size=self._logo_size)
            outer_context.update(csrf(request))
        else:
            t = template.Template("{{inner|safe}}")
            inner_context['article'] = SafeWrapper(article, logo_size=self._logo_size)
        outer_context['inner'] = self.nodelist_article.render(template.Context(inner_context))
        return t.render(template.Context(outer_context))

@register.tag
def article(parser, token):
    args = token.split_contents()[1:]
    data = {}
    for arg in args:
        k, v = arg.split('=')
        data[k] = v
    nodelist_article = parser.parse(('endarticle',))
    token = parser.next_token()
    return ArticleNode(nodelist_article, **data)
