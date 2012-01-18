# -*- coding:utf-8 -*-

from django.core.cache import cache
from django import template

register = template.Library()

from coop_cms.settings import get_article_class


@register.tag
def last_articles(parser, token):
    try:
        tag_name, number, template = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('%s tag requires 2 arguments' % token.split_contents()[0])
    return ArticleListNode(number, template)

def resolve(var_or_value, ctx):
    if var_or_value[0] == '"':
        return var_or_value[1:-1]
    return ctx.resolve_variable(var_or_value)

class ArticleListNode(template.Node):
    def __init__(self, number, templ):
        self.number = number
        self.templ = templ

    def last_articles(self,number):
        article_list = []
        all_articles = get_article_class().objects.all()[:number]
        for a in all_articles:
            if a.navigation_parent == None :
                article_list.append(a)
        return article_list

    def render(self, context):
        #nb = resolve(self.number, context)
        tmpl = resolve(self.templ, context)
        t = template.loader.get_template(tmpl)
        return ''.join([t.render(template.Context({ 'item': item })) for item in self.last_articles(self.number)])
    