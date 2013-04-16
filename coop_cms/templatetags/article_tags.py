# -*- coding:utf-8 -*-

from django.core.cache import cache
from django import template

register = template.Library()

from coop_cms.settings import get_article_class


@register.tag
def last_articles(parser, token):
    try:
        args = token.split_contents()
        if len(args) == 4:
            tag_name, number, template, category = token.split_contents()
            return ArticleListNode(number, template, category)
        elif len(args) == 3:
            tag_name, number, template = token.split_contents()
            return ArticleListNode(number, template, None)
    except ValueError:
        raise template.TemplateSyntaxError('%s tag requires at least 2 arguments' % token.split_contents()[0])

def resolve(var_or_value, ctx):
    if var_or_value[0] == '"':
        return var_or_value[1:-1]
    return ctx.resolve_variable(var_or_value)

class ArticleListNode(template.Node):
    """
    This templatetag takes as arguments :
    - A number limit of articles #TODO pagination
    - A template to render each articles
    - An optional ArticleCategory object
    """
    def __init__(self, number, templ, category):
        self.number = number
        self.templ = templ
        if category:
            self.category = template.Variable(category)

    def last_articles(self, context):
        article_list = []
        all_articles = get_article_class().objects.all().order_by('-created')
        if hasattr(self, 'category'):
            category = self.category.resolve(context)
            all_articles = all_articles.filter(category=category)
        all_articles = all_articles[:self.number]
        for a in all_articles:
            if a.navigation_parent == None:
                article_list.append(a)
        return article_list

    def render(self, context):
        tmpl = resolve(self.templ, context)
        t = template.loader.get_template(tmpl)
        return ''.join([t.render(template.Context({ 'item': item })) for item in self.last_articles(context)])
