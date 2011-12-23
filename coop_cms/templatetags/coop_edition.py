# -*- coding: utf-8 -*-

from django import template
register = template.Library()
from djaloha.templatetags.djaloha_utils import DjalohaEditNode
from coop_cms.models import PieceOfHtml, Article
from django.utils.translation import ugettext_lazy as _

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

class CoopFieldNode(template.Node):
    
    def __init__(self, field_name):
        super(CoopFieldNode, self).__init__()
        self._field_name = field_name
    
    def render(self, context):
        coop_cms_article_form = context.get('coop_cms_article_form', None)
        if coop_cms_article_form:
            t = template.Template("""
                {%% with form.%s.errors as errs %%}{%% include "coop_cms/_form_error.html" %%}{%% endwith %%}{{form.%s}}
            """ % (self._field_name, self._field_name))
            return t.render(template.Context({'form': coop_cms_article_form}))
        else:
            article = context.get('article')
            return getattr(article, self._field_name)

@register.tag
def coop_cms_field(parser, token):
    field_name = token.split_contents()[1]
    return CoopFieldNode(field_name)

################################################################################
class ArticleTitleNode(template.Node):
    
    def render(self, context):
        is_edition_mode = context.get('coop_cms_article_form', None)!=None
        article = context.get('article')
        return u"{0}".format(
            article.title,
            _(u" [EDITION]") if is_edition_mode else u"",
            _(u" [DRAFT]") if article.publication == Article.PUBLISHED else u"",
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
    <form id="article_form" method="POST" action="{{ post_url }}">{% csrf_token %}
    {% include "coop_cms/_form_error.html" with errs=form.non_field_errors %}
    {{inner}}
    <input type="submit">
    </form>
"""

class ArticleNode(template.Node):
    
    def __init__(self, nodelist_article):
        self.nodelist_article = nodelist_article
        
    def __iter__(self):
        for node in self.nodelist_article:
            yield node

    def render(self, context):
        coop_cms_article_form = context.get('coop_cms_article_form', None)
        inner_context = {}
        if coop_cms_article_form:
            t = template.Template(article_form_template)
            inner_context['article'] = coop_cms_article_form
        else:
            t = template.Template("{{inner}}")
            inner_context['article'] = context.get('article')
        inner = self.nodelist_article.render(template.Context(inner_context))
        return t.render(template.Context({'inner': inner}))

@register.tag
def article(parser, token):
    nodelist_article = parser.parse(('endarticle',))
    token = parser.next_token()
    return ArticleNode(nodelist_article)
