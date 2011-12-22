# -*- coding: utf-8 -*-

from django import template
register = template.Library()
from djaloha.templatetags.djaloha_utils import DjalohaEditNode
from coop_cms.models import PieceOfHtml

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
