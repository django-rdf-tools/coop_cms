# -*- coding: utf-8 -*-

from django import template
from django.template.loader import get_template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from coop_cms.models import NavNode
from coop_cms.settings import get_navTree_class
from django.contrib.contenttypes.models import ContentType
register = template.Library()
from django.template import VariableDoesNotExist


def extract_kwargs(args):
    kwargs = {}
    for arg in args:
        try:
            key, value = arg.split('=')
            kwargs[key] = value
        except ValueError:  # No = in the arg
            pass
    return kwargs


class NavigationTemplateNode(template.Node):
    def __init__(self, *args, **kwargs):
        super(NavigationTemplateNode, self).__init__()
        self._kwargs = {}
        for (k, v) in kwargs.items():
            self._kwargs[k] = template.Variable(v)

    def format_css_class(self, class_name):
        return u' class="{0}"'.format(class_name) if class_name else u""

    def resolve_kwargs(self, context):
        kwargs = {}
        for (k, v) in self._kwargs.items():
            try:
                kwargs[k] = v.resolve(context)
            except VariableDoesNotExist:
                kwargs[k] = v.var  # if the variable can not be resolved, thake the value as is

            if k == 'css_class':
                kwargs[k] = self.format_css_class(v)

        if not 'tree' in kwargs:
            kwargs['tree'] = 'default'

        tree, _is_new = get_navTree_class().objects.get_or_create(name=kwargs['tree'])
        if 'coop_cms_navtrees' in context.dicts[0]:
            context.dicts[0]['coop_cms_navtrees'].append(tree)
        else:
            context.dicts[0]['coop_cms_navtrees'] = [tree]

        return kwargs

#----------------------------------------------------------


class NavigationAsNestedUlNode(NavigationTemplateNode):

    def __init__(self, **kwargs):
        super(NavigationAsNestedUlNode, self).__init__(**kwargs)

    def render(self, context):
        kwargs = self.resolve_kwargs(context)
        tree_name = kwargs.pop('tree', 'default')
        root_nodes = NavNode.objects.filter(tree__name=tree_name, parent__isnull=True).order_by("ordering")
        return u''.join([node.as_navigation(**kwargs) for node in root_nodes])


@register.tag
def navigation_as_nested_ul(parser, token):
    args = token.contents.split()
    kwargs = extract_kwargs(args)
    return NavigationAsNestedUlNode(**kwargs)

#----------------------------------------------------------


class NavigationBreadcrumbNode(NavigationTemplateNode):
    def __init__(self, object, **kwargs):
        super(NavigationBreadcrumbNode, self).__init__(**kwargs)
        self.object_var = template.Variable(object)

    def render(self, context):
        object = self.object_var.resolve(context)
        ct = ContentType.objects.get_for_model(object.__class__)
        kwargs = self.resolve_kwargs(context)
        tree_name = kwargs.pop('tree', 'default')
        nav_nodes = NavNode.objects.filter(tree__name=tree_name, content_type=ct, object_id=object.id)
        if nav_nodes.count() > 0:
            return nav_nodes[0].as_breadcrumb(**kwargs)
        return u''


@register.tag
def navigation_breadcrumb(parser, token):
    args = token.contents.split()
    kwargs = extract_kwargs(args)
    if len(args) < 2:
        raise template.TemplateSyntaxError(_("navigation_breadcrumb requires object as argument"))
    return NavigationBreadcrumbNode(args[1], **kwargs)


class NavigationChildrenNode(NavigationTemplateNode):

    def __init__(self, object, **kwargs):
        super(NavigationChildrenNode, self).__init__(**kwargs)
        self.object_var = template.Variable(object)

    def render(self, context):
        object = self.object_var.resolve(context)
        ct = ContentType.objects.get_for_model(object.__class__)
        kwargs = self.resolve_kwargs(context)
        tree_name = kwargs.pop('tree', 'default')
        nav_nodes = NavNode.objects.filter(tree__name=tree_name, content_type=ct, object_id=object.id)
        if nav_nodes.exists():
            return nav_nodes[0].children_as_navigation(**kwargs)
        return u''


@register.tag
def navigation_children(parser, token):
    args = token.contents.split()
    kwargs = extract_kwargs(args)
    if len(args) < 2:
        raise template.TemplateSyntaxError(_("navigation_children requires object as argument and optionally tree={{tree_name}}"))
    return NavigationChildrenNode(args[1], **kwargs)


class NavigationSiblingsNode(NavigationTemplateNode):

    def __init__(self, object, **kwargs):
        super(NavigationSiblingsNode, self).__init__(**kwargs)
        self.object_var = template.Variable(object)

    def render(self, context):
        object = self.object_var.resolve(context)
        ct = ContentType.objects.get_for_model(object.__class__)
        kwargs = self.resolve_kwargs(context)
        tree_name = kwargs.pop('tree', 'default')
        nav_nodes = NavNode.objects.filter(tree__name=tree_name, content_type=ct, object_id=object.id)
        if nav_nodes.count() > 0:
            return nav_nodes[0].siblings_as_navigation(**kwargs)
        return u''


@register.tag
def navigation_siblings(parser, token):
    args = token.contents.split()
    kwargs = extract_kwargs(args)
    if len(args) < 2:
        raise template.TemplateSyntaxError(_("navigation_siblings requires object as argument"))
    return NavigationSiblingsNode(args[1], **kwargs)
