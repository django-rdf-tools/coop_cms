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
        if context.get('form', None):
            context.dicts[0]['djaloha_edit'] = True
        #context.dicts[0]['can_edit_template'] = True
        return super(PieceOfHtmlEditNode, self).render(context)

@register.tag
def coop_piece_of_html(parser, token):
    div_id = token.split_contents()[1]
    return PieceOfHtmlEditNode(PieceOfHtml, {'div_id': div_id}, 'content')

################################################################################
class ArticleTitleNode(template.Node):

    def render(self, context):
        is_edition_mode = context.get('form', None)!=None
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


class CmsFormMediaNode(template.Node):

    def render(self, context):
        form = context.get('form', None)
        if form:
            t = template.Template("{{form.media}}")
            return t.render(template.Context({'form': form}))
        else:
            return ""


@register.tag
def cms_form_media(parser, token):
    return CmsFormMediaNode()


################################################################################


class IfCmsEditionNode(template.Node):
    def __init__(self, nodelist_true, nodelist_false):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def __iter__(self):
        for node in self.nodelist_true:
            yield node
        for node in self.nodelist_false:
            yield node

    def render(self, context):
        form = context.get('form', None)
        if form:
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)


@register.tag
def if_cms_edition(parser, token):
    nodelist_true = parser.parse(('else', 'endif'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endif',))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfCmsEditionNode(nodelist_true, nodelist_false)


################################################################################


CMS_FORM_TEMPLATE = """
    <form id="cms_form" enctype="multipart/form-data"  method="POST" action="{{post_url}}">{% csrf_token %}
    {% include "coop_cms/_form_error.html" with errs=form.non_field_errors %}
    {{inner}} <input type="submit" style="display: none"> </form>
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
                value = u'<img class="logo" src="{0}">'.format(src.url)
            else:
                value = u''
        elif callable(value):
            return value()
        return mark_safe(value)

class FormWrapper:

    def __init__(self, form, the_object, logo_size=None):
        self._form = form
        self._obj = the_object
        if logo_size:
            self._form.set_logo_size(logo_size)

    def __getitem__(self, field, logo_size=None):
        if field in self._form.fields.keys():
            t = template.Template("""
                    {%% with form.%s.errors as errs %%}{%% include "coop_cms/_form_error.html" %%}{%% endwith %%}{{form.%s}}
                """ % (field, field))
            return t.render(template.Context({'form': self._form}))
        else:
            return getattr(self._obj, field)

class CmsEditNode(template.Node):
    def __init__(self, nodelist_content, var_name, logo_size=None):
        self.var_name = var_name
        self.nodelist_content = nodelist_content
        self._logo_size = logo_size
        from logging import getLogger
        self.log = getLogger('tartiflette')

    def __iter__(self):
        for node in self.nodelist_content:
            yield node

    def render(self, context):
        form = context.get('form', None)
        request = context.get('request')
        the_object = context.get(self.var_name)

        #the context used for rendering the templatetag content
        inner_context = {}
        for x in context.dicts:
            inner_context.update(x)

        #the context used for rendering the whole page
        self.post_url = the_object.get_edit_url()
        outer_context = {'post_url': self.post_url}

        inner_context[self.var_name] = the_object  # ???

        safe_context = inner_context.copy()
        inner_context[self.var_name] = the_object  # ????????
        inner_value = u""

        if form:
            t = template.Template(CMS_FORM_TEMPLATE)
            safe_context[self.var_name] = FormWrapper(form, the_object, logo_size=self._logo_size)
            outer_context.update(csrf(request))
            #outer_context['inner'] = self.nodelist_content.render(template.Context(inner_context))
        else:
            t = template.Template("{{inner|safe}}")
            safe_context[self.var_name] = SafeWrapper(the_object, logo_size=self._logo_size)
        for node in self.nodelist_content:
            if isinstance(node, template.VariableNode) or isinstance(node, template.TextNode):
                c = node.render(template.Context(safe_context))
            else:
                self.log.debug(str(type(node)))
                c = node.render(template.Context(inner_context))
                self.log.debug('render = ' + str(c))
            inner_value += c
        outer_context['inner'] = mark_safe(inner_value) if form else inner_value
        return t.render(template.Context(outer_context))


@register.tag
def cms_edit(parser, token):
    args = token.split_contents()[1:]
    data = {}
    var_name = args[0]
    for arg in args[1:]:
        k, v = arg.split('=')
        data[k] = v
    nodelist = parser.parse(('end_cms_edit',))
    token = parser.next_token()
    return CmsEditNode(nodelist, var_name, **data)

################################################################################

class CmsNoSpace(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        html = self.nodelist.render(context).strip()
        return ' '.join(html.split())

@register.tag
def cms_nospace(parser, token):
    nodelist = parser.parse(('end_cms_nospace',))
    parser.delete_first_token()
    return CmsNoSpace(nodelist)
