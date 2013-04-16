# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.template import Template, Context
from coop_cms.models import Link, NavNode, NavType, Document, Newsletter, NewsletterItem, PieceOfHtml, NewsletterSending, BaseArticle
import json
from django.core.exceptions import ValidationError
from coop_cms.settings import get_article_class, get_article_templates, get_navTree_class
from model_mommy import mommy
from django.conf import settings
import os.path, shutil
from django.core.files import File
from django.core import mail
from coop_cms.html2text import html2text
from coop_cms.utils import make_links_absolute
from datetime import datetime, timedelta
from django.core import management

class ArticleTest(TestCase):
    
    def _log_as_editor(self):
        self.user = user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
        ct = ContentType.objects.get_for_model(get_article_class())
        
        perm = 'change_{0}'.format(ct.model)
        can_edit_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_edit_article)
        
        perm = 'add_{0}'.format(ct.model)
        can_add_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_add_article)
        
        user.save()
        
        self.client.login(username='toto', password='toto')
        
    def _log_as_editor_no_add(self):
        self.user = user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
        ct = ContentType.objects.get_for_model(get_article_class())
        
        perm = 'change_{0}'.format(ct.model)
        can_edit_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_edit_article)
        
        user.save()
        
        self.client.login(username='toto', password='toto')

    def _check_article(self, response, data):
        for (key, value) in data.items():
            self.assertContains(response, value)
            
    def _check_article_not_changed(self, article, data, initial_data):
        article = get_article_class().objects.get(id=article.id)

        for (key, value) in data.items():
            self.assertNotEquals(getattr(article, key), value)
            
        for (key, value) in initial_data.items():
            self.assertEquals(getattr(article, key), value)

    def test_view_article(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        self.assertEqual(article.slug, 'test')
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_404_ok(self):
        response = self.client.get("/jhjhjkahekhj", follow=True)
        self.assertEqual(404, response.status_code)
        
    def test_is_navigable(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        self.assertEqual('/test/', article.get_absolute_url())

    def test_create_slug(self):
        article = get_article_class().objects.create(title=u"voici l'été", publication=BaseArticle.PUBLISHED)
        self.assertEqual(article.slug, 'voici-lete')
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_edit_article(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        
        data = {"title": 'salut', 'content': 'bonjour!'}
        
        self._log_as_editor()
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article(response, data)
        
        data = {"title": 'bye', 'content': 'au revoir'}
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article(response, data)
        
    def test_article_edition_permission(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        
        data = {"title": 'salut', "content": 'oups'}
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        next_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')+"?next="+article.get_edit_url()
        self.assertTrue(login_url in next_url)
        
        article = get_article_class().objects.get(id=article.id)
        self.assertEquals(article.title, initial_data['title'])
        self.assertEquals(article.content, initial_data['content'])
        
    def test_article_empty_title(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        data = {'content': "un nouveau contenu"}
        
        self._log_as_editor()
        data["title"] = ""
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article_not_changed(article, data, initial_data)
        
        data["title"] = "<br>"
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article_not_changed(article, data, initial_data)
        
        data["title"] = " <br> "
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article_not_changed(article, data, initial_data)
        
    def _is_aloha_found(self, response):
        self.assertEqual(200, response.status_code)
        aloha_js = reverse('aloha_init')
        return (response.content.find(aloha_js)>0)
        
    def test_edit_permission(self):
        initial_data = {'title': "ceci est un test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        response = self.client.get(article.get_absolute_url(), follow=True)
        self.assertEqual(200, response.status_code)
        
        response = self.client.get(article.get_edit_url(), follow=True)
        self.assertEqual(200, response.status_code) #if can_edit returns 404 error
        next_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')+"?next="+article.get_edit_url()
        self.assertTrue(login_url in next_url)
        
        self._log_as_editor()
        response = self.client.get(article.get_edit_url(), follow=True)
        self.assertEqual(200, response.status_code)
        
    def test_aloha_loaded(self):
        initial_data = {'title': "ceci est un test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        response = self.client.get(article.get_absolute_url())
        self.assertFalse(self._is_aloha_found(response))
        
        self._log_as_editor()
        response = self.client.get(article.get_edit_url())
        self.assertTrue(self._is_aloha_found(response))
        
    def test_checks_aloah_links(self):
        slugs = ("un", "deux", "trois", "quatre")
        for slug in slugs:
            get_article_class().objects.create(publication=BaseArticle.PUBLISHED, title=slug)
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(**initial_data)
        
        self._log_as_editor()
        response = self.client.get(reverse('aloha_init'))
        
        context_slugs = [article.slug for article in response.context['links']]
        for slug in slugs:
            self.assertTrue(slug in context_slugs)
        
    def test_view_draft_article(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.DRAFT)
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(404, response.status_code)
        self._log_as_editor()
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_accept_regular_html(self):
        article = get_article_class().objects.create(title="test", publication=BaseArticle.PUBLISHED)
        html = '<h1>paul</h1><a href="/" target="_blank">georges</a><p><b>ringo</b></p>'
        html += '<h6>john</h6><img src="/img.jpg"><br><table><tr><th>A</th><td>B</td></tr>'
        data = {'content': html, 'title': 'ok<br>ok'}
        self._log_as_editor()
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        #checking html content would not work. Check that the article is updated
        for b in ['paul', 'georges', 'ringo', 'john']:
            self.assertContains(response, b)
        
    #def test_no_malicious_when_editing(self):
    #    initial_data = {'title': "test", 'content': "this is my article content"}
    #    article = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
    #    
    #    data1 = {'content': "<script>alert('aahhh');</script>", 'title': 'ok'}
    #    data2 = {'title': '<a href="/">home</a>', 'content': 'ok'}
    #    
    #    self._log_as_editor()
    #    response = self.client.post(article.get_edit_url(), data=data1, follow=True)
    #    self.assertEqual(response.status_code, 200)
    #    self._check_article_not_changed(article, data1, initial_data)
    #    
    #    response = self.client.post(article.get_edit_url(), data=data2, follow=True)
    #    self.assertEqual(response.status_code, 200)
    #    self._check_article_not_changed(article, data2, initial_data)
        
    def test_publish_article(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=BaseArticle.DRAFT, **initial_data)
        
        self._log_as_editor()
        
        data = {
            'publication': BaseArticle.PUBLISHED,
        }
        
        response = self.client.post(article.get_publish_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        article = get_article_class().objects.get(id=article.id)
        self.assertEqual(article.title, initial_data['title'])
        self.assertEqual(article.content, initial_data['content'])
        self.assertEqual(article.publication, BaseArticle.PUBLISHED)

    def test_draft_article(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        
        self._log_as_editor()
        
        data = {
            'publication': BaseArticle.DRAFT,
        }
        
        response = self.client.post(article.get_publish_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        article = get_article_class().objects.get(id=article.id)
        self.assertEqual(article.title, initial_data['title'])
        self.assertEqual(article.content, initial_data['content'])
        self.assertEqual(article.publication, BaseArticle.DRAFT)
        
    def test_new_article(self):
        Article = get_article_class()
        
        self._log_as_editor()
        data = {
            'title': "Un titre",
            'publication': BaseArticle.DRAFT,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': None,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(Article.objects.count(), 1)
        article = Article.objects.all()[0]
        
        self.assertEqual(article.title, data['title'])
        self.assertEqual(article.publication, data['publication'])
        self.assertEqual(article.template, data['template'])
        self.assertEqual(article.navigation_parent, None)
        self.assertEqual(NavNode.objects.count(), 0)
        
    def test_new_article_published(self):
        Article = get_article_class()
        
        self._log_as_editor()
        data = {
            'title': "Un titre",
            'publication': BaseArticle.PUBLISHED,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': None,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(Article.objects.count(), 1)
        article = Article.objects.all()[0]
        
        self.assertEqual(article.title, data['title'])
        self.assertEqual(article.publication, data['publication'])
        self.assertEqual(article.template, data['template'])
        self.assertEqual(article.navigation_parent, None)
        self.assertEqual(NavNode.objects.count(), 0)
        
    def test_new_article_anonymous(self):
        Article = get_article_class()
        
        self._log_as_editor() #create self.user
        self.client.logout()
        data = {
            'title': "Un titre",
            'publication': BaseArticle.DRAFT,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': None,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(200, response.status_code) #if can_edit returns 404 error
        next_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(login_url in next_url)
        
        self.assertEqual(Article.objects.count(), 0)
        
    def test_new_article_no_perm(self):
        Article = get_article_class()
        
        self._log_as_editor_no_add()
        data = {
            'title': "Un titre",
            'publication': BaseArticle.DRAFT,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': None,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(403, response.status_code)
        self.assertEqual(Article.objects.count(), 0)
        
    def test_new_article_navigation(self):
        Article = get_article_class()
        
        tree = get_navTree_class().objects.create()
        
        self._log_as_editor()
        data = {
            'title': "Un titre",
            'publication': BaseArticle.PUBLISHED,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': -tree.id,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(Article.objects.count(), 1)
        article = Article.objects.all()[0]
        
        self.assertEqual(article.title, data['title'])
        self.assertEqual(article.publication, data['publication'])
        self.assertEqual(article.template, data['template'])
        self.assertEqual(article.navigation_parent, 0)
        
        self.assertEqual(NavNode.objects.count(), 1)
        node = NavNode.objects.all()[0]
        self.assertEqual(node.content_object, article)
        self.assertEqual(node.parent, None)
        self.assertEqual(node.tree, tree)
        
    def test_new_article_navigation_leaf(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        Article = get_article_class()
        art1 = get_article_class().objects.create(publication=BaseArticle.PUBLISHED, **initial_data)
        
        tree = get_navTree_class().objects.create()
        ct = ContentType.objects.get_for_model(Article)
        node1 = NavNode.objects.create(content_type=ct, object_id=art1.id, tree=tree)
        
        self._log_as_editor()
        data = {
            'title': "Un titre",
            'publication': BaseArticle.PUBLISHED,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': node1.id,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(Article.objects.exclude(id=art1.id).count(), 1)
        art2 = Article.objects.exclude(id=art1.id)[0]
        
        self.assertEqual(art2.title, data['title'])
        self.assertEqual(art2.publication, data['publication'])
        self.assertEqual(art2.template, data['template'])
        self.assertEqual(art2.navigation_parent, node1.id)
        
        self.assertEqual(NavNode.objects.count(), 2)
        node2 = NavNode.objects.exclude(id=node1.id)[0]
        self.assertEqual(node2.content_object, art2)
        self.assertEqual(node2.parent, node1)

class NavigationTest(TestCase):

    def setUp(self):
        self.url_ct = ContentType.objects.get(app_label='coop_cms', model='link')
        NavType.objects.create(content_type=self.url_ct, search_field='url', label_rule=NavType.LABEL_USE_SEARCH_FIELD)
        self.editor = None
        self.staff = None
        self.tree = get_navTree_class().objects.create()
        self.srv_url = reverse("navigation_tree", args=[self.tree.id])

    def _log_as_editor(self):
        if not self.editor:
            self.editor = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
            self.editor.is_staff = True
            can_edit_tree = Permission.objects.get(content_type__app_label='coop_cms', codename='change_navtree')
            self.editor.user_permissions.add(can_edit_tree)
            self.editor.save()
        
        self.client.login(username='toto', password='toto')
        
    def _log_as_staff(self):
        if not self.staff:
            self.staff = User.objects.create_user('titi', 'titi@titi.fr', 'titi')
            self.staff.is_staff = True
            self.staff.save()
        
        self.client.login(username='titi', password='titi')

    def test_view_in_admin(self):
        self._log_as_editor()
        url = reverse("admin:coop_cms_navtree_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
    def test_add_node(self):
        link = Link.objects.create(url="http://www.google.fr")
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': link.id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['label'], 'http://www.google.fr')
        
        nav_node = NavNode.objects.get(object_id=link.id, content_type=self.url_ct)
        self.assertEqual(nav_node.label, 'http://www.google.fr')
        self.assertEqual(nav_node.content_object, link)
        self.assertEqual(nav_node.parent, None)
        self.assertEqual(nav_node.ordering, 1)
        
        #Add a second node as child
        link2 = Link.objects.create(url="http://www.python.org")
        data['object_id'] = link2.id
        data['parent_id'] = link.id
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['label'], 'http://www.python.org')
        nav_node2 = NavNode.objects.get(object_id=link2.id, content_type=self.url_ct)
        self.assertEqual(nav_node2.label, 'http://www.python.org')
        self.assertEqual(nav_node2.content_object, link2)
        self.assertEqual(nav_node2.parent, nav_node)
        self.assertEqual(nav_node.ordering, 1)
        
    def test_add_node_twice(self):
        link = Link.objects.create(url="http://www.google.fr")
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': link.id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['label'], 'http://www.google.fr')
        
        nav_node = NavNode.objects.get(object_id=link.id, content_type=self.url_ct)
        self.assertEqual(nav_node.label, 'http://www.google.fr')
        self.assertEqual(nav_node.content_object, link)
        self.assertEqual(nav_node.parent, None)
        self.assertEqual(nav_node.ordering, 1)
        
        #Add a the same object a 2nd time
        data['object_id'] = link.id
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
        nav_node = NavNode.objects.get(object_id=link.id, content_type=self.url_ct)
        self.assertEqual(nav_node.label, 'http://www.google.fr')
        self.assertEqual(nav_node.content_object, link)
        self.assertEqual(nav_node.parent, None)
        self.assertEqual(nav_node.ordering, 1)
        
    def test_move_node_to_parent(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[-2].id,
            'parent_id': nodes[0].id,
            'ref_pos': 'after',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        node = NavNode.objects.get(id=nodes[-2].id)
        self.assertEqual(node.parent, nodes[0])
        self.assertEqual(node.ordering, 1)
        
        root_nodes = [node for node in NavNode.objects.filter(parent__isnull=True).order_by("ordering")]
        self.assertEqual(nodes[:-2]+nodes[-1:], root_nodes)
        self.assertEqual([1, 2, 3], [n.ordering for n in root_nodes])
        
    def test_move_node_to_root(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.toto.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        nodes[1].parent = nodes[0]
        nodes[1].ordering = 1
        nodes[1].save()
        nodes[2].parent = nodes[0]
        nodes[2].ordering = 2
        nodes[2].save()
        
        self._log_as_editor()
        
        #Move after
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[1].id,
            'ref_pos': 'after',
            'ref_id': nodes[0].id,            
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        node = NavNode.objects.get(id=nodes[1].id)
        self.assertEqual(node.parent, None)
        self.assertEqual(node.ordering, 2)
        self.assertEqual(NavNode.objects.get(id=nodes[0].id).ordering, 1)
        self.assertEqual(NavNode.objects.get(id=nodes[2].id).ordering, 1)
        
        #Move before
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[2].id,
            'ref_pos': 'before',
            'ref_id': nodes[0].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        #if result['status'] != 'success':
        #    print result['message']
        self.assertEqual(result['status'], 'success')
        
        node = NavNode.objects.get(id=nodes[2].id)
        self.assertEqual(node.parent, None)
        self.assertEqual(node.ordering, 1)
        self.assertEqual(NavNode.objects.get(id=nodes[0].id).ordering, 2)
        self.assertEqual(NavNode.objects.get(id=nodes[1].id).ordering, 3)
        
    def test_move_same_level(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #Move the 4th just after the 1st one
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[-2].id,
            'ref_id': nodes[0].id,
            'ref_pos': 'after',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        nodes = [NavNode.objects.get(id=n.id) for n in nodes]#refresh
        [self.assertEqual(n.parent, None) for n in nodes]
        self.assertEqual([1, 3, 2, 4], [n.ordering for n in nodes])
        
        #Move the 1st before the 4th
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[0].id,
            'ref_id': nodes[-1].id,
            'ref_pos': 'before',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        nodes = [NavNode.objects.get(id=n.id) for n in nodes]#refresh
        [self.assertEqual(n.parent, None) for n in nodes]
        self.assertEqual([3, 2, 1, 4], [n.ordering for n in nodes])
        
    def test_delete_node(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #remove the 2ns one
        data = {
            'msg_id': 'remove_navnode',
            'node_ids': nodes[1].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
    
        nodes_after = NavNode.objects.all().order_by('ordering')
        self.assertEqual(3, len(nodes_after))
        self.assertTrue(nodes[1] not in nodes_after)
        for i, node in enumerate(nodes_after):
            self.assertTrue(node in nodes)
            self.assertTrue(i+1, node.ordering)
            
    def test_delete_node_and_children(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        nodes[-1].parent = nodes[-2]
        nodes[-1].ordering = 1
        nodes[-1].save()
        
        self._log_as_editor()
        
        #remove the 2ns one
        data = {
            'msg_id': 'remove_navnode',
            'node_ids': nodes[-2].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
    
        nodes_after = NavNode.objects.all().order_by('ordering')
        self.assertEqual(2, len(nodes_after))
        self.assertTrue(nodes[-1] not in nodes_after)
        self.assertTrue(nodes[-2] not in nodes_after)
        for i, node in enumerate(nodes_after):
            self.assertTrue(node in nodes)
            self.assertTrue(i+1, node.ordering)
            
    def test_rename_node(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #rename the 1st one
        data = {
            'msg_id': 'rename_navnode',
            'node_id': nodes[0].id,
            'name': 'Google',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
    
        node = NavNode.objects.get(id=nodes[0].id)
        self.assertEqual(data["name"], node.label)
        self.assertEqual(links[0].url, node.content_object.url)#object not renamed
        
        for n in nodes[1:]:
            node = NavNode.objects.get(id=n.id)
            self.assertEqual(n.label, node.label)
        
    def test_view_node(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #remove the 2ns one
        data = {
            'msg_id': 'view_navnode',
            'node_id': nodes[0].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['html'].find(nodes[0].get_absolute_url())>=0)
        self.assertTrue(result['html'].find(nodes[1].get_absolute_url())<0)
        self.assertTemplateUsed(response, 'coop_cms/navtree_content/default.html')
        
    def _do_test_get_suggest_list(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'get_suggest_list',
            'term': '.fr'
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['suggestions']), 3)
        
    def test_get_suggest_list(self):
        self._do_test_get_suggest_list()
        
    def test_get_suggest_list_get_label(self):
        
        nt = NavType.objects.get(content_type=self.url_ct)
        nt.search_field = ''
        nt.label_rule=NavType.LABEL_USE_GET_LABEL
        nt.save()
        self._do_test_get_suggest_list()
        
    def test_get_suggest_list_unicode(self):
        
        nt = NavType.objects.get(content_type=self.url_ct)
        nt.search_field = ''
        nt.label_rule=NavType.LABEL_USE_UNICODE
        nt.save()
        self._do_test_get_suggest_list()
        
    def test_get_suggest_list_only_not_in_navigation(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        link = links[0]
        node = NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=1, parent=None)
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'get_suggest_list',
            'term': '.fr'
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['suggestions']), 2)
        
    def test_get_suggest_tree_type_all(self):
        nt_link = NavType.objects.get(content_type=self.url_ct)
        
        ct = ContentType.objects.get_for_model(get_article_class())
        nt_art = NavType.objects.create(content_type=ct, search_field='title', label_rule=NavType.LABEL_USE_SEARCH_FIELD)
        
        self.assertEqual(self.tree.types.count(), 0)
        
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        article = get_article_class().objects.create(title="python", content='nice snake')
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'get_suggest_list',
            'term': 'python'
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['suggestions']), 2)

    def test_get_suggest_tree_type_filter(self):
        nt_link = NavType.objects.get(content_type=self.url_ct)
        
        ct = ContentType.objects.get_for_model(get_article_class())
        nt_art = NavType.objects.create(content_type=ct, search_field='title', label_rule=NavType.LABEL_USE_SEARCH_FIELD)
        
        self.tree.types.add(nt_art)
        self.tree.save()
        
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        article = get_article_class().objects.create(title="python", content='nice snake')
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'get_suggest_list',
            'term': 'python'
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['suggestions']), 1)
        self.assertEqual(result['suggestions'][0]['label'], 'python')
        
    def test_unknow_message(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'oups',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
    def test_missing_message(self):
        self._log_as_editor()
        
        data = {
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        
    def test_not_ajax(self):
        link = Link.objects.create(url="http://www.google.fr")
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': link.id,
        }
        
        response = self.client.post(self.srv_url, data=data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(0, NavNode.objects.count())
        
    def test_add_unknown_obj(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': 11,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(0, NavNode.objects.count())
        
    def test_remove_unknown_node(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'remove_navnode',
            'node_ids': 11,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
    def test_rename_unknown_node(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'remove_navnode',
            'node_id': 11,
            'label': 'oups'
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
    def test_check_auth(self):
        link = Link.objects.create(url='http://www.google.fr')
        
        for msg_id in ('add_navnode', 'move_navnode', 'rename_navnode', 'get_suggest_list', 'view_navnode', 'remove_navnode'):
            data = {
                'ref_pos': 'after',
                'name': 'oups',
                'term': 'goo',
                'object_type':'coop_cms.link',
                'object_id': link.id,
                'msg_id': msg_id
            }
            if msg_id != 'add_navnode':
                node = NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=1, parent=None)
                data.update({'node_id': node.id, 'node_ids': node.id})
            
            self._log_as_staff()
            response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
            result = json.loads(response.content)
            self.assertEqual(result['status'], 'error')
            
            self._log_as_editor()
            response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
            result = json.loads(response.content)
            self.assertEqual(result['status'], 'success')
            
            NavNode.objects.all().delete()
            
    def test_set_out_of_nav(self):
        self._log_as_editor()
        
        link = Link.objects.create(url='http://www.google.fr')
        node = NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=1, parent=None, in_navigation=True)
        
        data = {
            'msg_id': 'navnode_in_navigation',
            'node_id': node.id,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertNotEqual(result['message'], '')
        self.assertEqual(result['icon'], 'out_nav')
        node = NavNode.objects.get(id=node.id)
        self.assertFalse(node.in_navigation)
        
    def test_set_in_nav(self):
        self._log_as_editor()
        
        link = Link.objects.create(url='http://www.google.fr')
        node = NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=1, parent=None, in_navigation=False)
        
        data = {
            'msg_id': 'navnode_in_navigation',
            'node_id': node.id,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertNotEqual(result['message'], '')
        self.assertEqual(result['icon'], 'in_nav')
        node = NavNode.objects.get(id=node.id)
        self.assertTrue(node.in_navigation)
        
    def test_delete_object(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        parent = None
        for i, link in enumerate(links):
            parent = NavNode.objects.create(tree=self.tree, label=link.url, content_object=link, ordering=i+1, parent=parent)
            
        links[1].delete()
        
        self.assertEqual(0, Link.objects.filter(url=addrs[1]).count())
        for url in addrs[:1]+addrs[2:]:
            self.assertEqual(1, Link.objects.filter(url=url).count())
            
        nodes = NavNode.objects.all()
        self.assertEqual(1, nodes.count())
        node = nodes[0]
        self.assertEqual(addrs[0], node.content_object.url)

#class NavigationParentTest(TestCase):
#    
#    def setUp(self):
#        ct = ContentType.objects.get_for_model(get_article_class())
#        NavType.objects.create(content_type=ct, search_field='title', label_rule=NavType.LABEL_USE_SEARCH_FIELD)
#        self.tree = get_navTree_class().objects.create()
#    
#    def test_set_himself_as_parent_raise_error(self):
#        art = get_article_class().objects.create(title='toto', content='oups')
#        node = NavNode.objects.create(tree=self.tree, label=art.title, content_object=art, ordering=1, parent=None)
#        self.assertRaises(ValidationError, art._set_navigation_parent, node.id)
#        
#    def test_set_child_as_parent_raise_error(self):
#        art1 = get_article_class().objects.create(title='toto', content='oups')
#        node1 = NavNode.objects.create(tree=self.tree, label=art1.title, content_object=art1, ordering=1, parent=None)
#        
#        art2 = get_article_class().objects.create(title='titi', content='oups')
#        node2 = NavNode.objects.create(tree=self.tree, label=art2.title, content_object=art2, ordering=1, parent=node1)
#        
#        self.assertRaises(ValidationError, art1._set_navigation_parent, node2.id)
#    
#    def test_add_to_navigation_as_root(self):
#        art1 = get_article_class().objects.create(title='toto', content='oups')
#        art1.navigation_parent = 0
#        ct = ContentType.objects.get_for_model(get_article_class())
#        node = NavNode.objects.get(content_type=ct, object_id=art1.id)
#        
#    def test_add_to_navigation_as_child(self):
#        art1 = get_article_class().objects.create(title='toto', content='oups')
#        node1 = NavNode.objects.create(tree=self.tree, label=art1.title, content_object=art1, ordering=1, parent=None)
#        art2 = get_article_class().objects.create(title='titi', content='oups')
#        art2.navigation_parent = node1.id
#        ct = ContentType.objects.get_for_model(get_article_class())
#        node = NavNode.objects.get(content_type=ct, object_id=art2.id)
#        self.assertEqual(node.parent.id, node1.id)
#        
#    def test_move_in_navigation_to_root(self):
#        art1 = get_article_class().objects.create(title='toto', content='oups')
#        node1 = NavNode.objects.create(tree=self.tree, label=art1.title, content_object=art1, ordering=1, parent=None)
#        art2 = get_article_class().objects.create(title='titi', content='oups')
#        node2 = NavNode.objects.create(tree=self.tree, label=art2.title, content_object=art2, ordering=1, parent=node1)
#        art2.navigation_parent = 0
#        ct = ContentType.objects.get_for_model(get_article_class())
#        node = NavNode.objects.get(content_type=ct, object_id=art2.id)
#        self.assertEqual(node.parent, None)
#        
#    def test_move_in_navigation_to_child(self):
#        art1 = get_article_class().objects.create(title='toto', content='oups')
#        node1 = NavNode.objects.create(tree=self.tree, label=art1.title, content_object=art1, ordering=1, parent=None)
#        art2 = get_article_class().objects.create(title='titi', content='oups')
#        node2 = NavNode.objects.create(tree=self.tree, label=art2.title, content_object=art2, ordering=1, parent=None)
#        art2.navigation_parent = node1.id
#        ct = ContentType.objects.get_for_model(get_article_class())
#        node = NavNode.objects.get(content_type=ct, object_id=art2.id)
#        self.assertEqual(node.parent.id, node1.id)
#        
#    def test_remove_from_navigation(self):
#        art1 = get_article_class().objects.create(title='toto', content='oups')
#        node1 = NavNode.objects.create(tree=self.tree, label=art1.title, content_object=art1, ordering=1, parent=None)
#        art1.navigation_parent = None
#        ct = ContentType.objects.get_for_model(get_article_class())
#        self.assertRaises(NavNode.DoesNotExist, NavNode.objects.get, content_type=ct, object_id=art1.id)
#        
#    def test_remove_from_navigation_twice(self):
#        art1 = get_article_class().objects.create(title='toto', content='oups')
#        node1 = NavNode.objects.create(tree=self.tree, label=art1.title, content_object=art1, ordering=1, parent=None)
#        art1.navigation_parent = None
#        ct = ContentType.objects.get_for_model(get_article_class())
#        self.assertRaises(NavNode.DoesNotExist, NavNode.objects.get, content_type=ct, object_id=art1.id)
#        art1.navigation_parent = None
#        ct = ContentType.objects.get_for_model(get_article_class())
#        self.assertRaises(NavNode.DoesNotExist, NavNode.objects.get, content_type=ct, object_id=art1.id)
#        
#    def test_get_navigation_parent(self):
#        art1 = get_article_class().objects.create(title='toto', content='oups')
#        node1 = NavNode.objects.create(tree=self.tree, label=art1.title, content_object=art1, ordering=1, parent=None)
#        art2 = get_article_class().objects.create(title='titi', content='oups')
#        node2 = NavNode.objects.create(tree=self.tree, label=art2.title, content_object=art2, ordering=1, parent=node1)
#        art3 = get_article_class().objects.create(title='tutu', content='oups')
#        self.assertEqual(art1.navigation_parent, 0)
#        self.assertEqual(art2.navigation_parent, art1.id)
#        self.assertEqual(art3.navigation_parent, None)

class TemplateTagsTest(TestCase):
    
    def setUp(self):
        link1 = Link.objects.create(url='http://www.google.fr')
        link2 = Link.objects.create(url='http://www.python.org')
        link3 = Link.objects.create(url='http://www.quinode.fr')
        link4 = Link.objects.create(url='http://www.apidev.fr')
        link5 = Link.objects.create(url='http://www.toto.fr')
        link6 = Link.objects.create(url='http://www.titi.fr')
        
        self.nodes = []
        
        self.tree = tree = get_navTree_class().objects.create()
        
        self.nodes.append(NavNode.objects.create(tree=tree, label=link1.url, content_object=link1, ordering=1, parent=None))
        self.nodes.append(NavNode.objects.create(tree=tree, label=link2.url, content_object=link2, ordering=2, parent=None))
        self.nodes.append(NavNode.objects.create(tree=tree, label=link3.url, content_object=link3, ordering=3, parent=None))
        self.nodes.append(NavNode.objects.create(tree=tree, label=link4.url, content_object=link4, ordering=1, parent=self.nodes[2]))
        self.nodes.append(NavNode.objects.create(tree=tree, label=link5.url, content_object=link5, ordering=1, parent=self.nodes[3]))
        self.nodes.append(NavNode.objects.create(tree=tree, label=link6.url, content_object=link6, ordering=2, parent=self.nodes[3]))
        
    def test_view_navigation(self):
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({}))
        
        positions = [html.find('{0}'.format(n.content_object.url)) for n in self.nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
    def _insert_new_node(self):
        link7 = Link.objects.create(url='http://www.tutu.fr')
        self.nodes.insert(-1, NavNode.objects.create(tree=self.tree, label=link7.url, content_object=link7, ordering=2, parent=self.nodes[3]))
        self.nodes[-1].ordering = 3
        self.nodes[-1].save()
        
    def test_view_navigation_order(self):
        self._insert_new_node()
        
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({}))
        
        positions = [html.find('{0}'.format(n.content_object.url)) for n in self.nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
            
    def test_view_out_of_navigation(self):
        self.nodes[2].in_navigation = False
        self.nodes[2].save()
        
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({}))
        
        for n in self.nodes[:2]:
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in self.nodes[2:]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_navigation_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul li_template=cst_tpl%}')
        
        html = tpl.render(Context({'cst_tpl': cst_tpl}))
        
        for n in self.nodes:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_navigation_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul li_template=coop_cms/test_li.html%}')
        
        html = tpl.render(Context({}))
        
        for n in self.nodes:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_navigation_css(self):
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul css_class=toto%}')
        html = tpl.render(Context({}))
        self.assertTrue(html.count('<li class="toto">'), len(self.nodes))
        
    def test_view_navigation_custom_template_and_css(self):
        tpl = Template(
            '{% load coop_navigation %}{%navigation_as_nested_ul li_template=coop_cms/test_li.html css_class=toto%}'
        )
        html = tpl.render(Context({}))
        self.assertTrue(html.count('<li class="toto">'), len(self.nodes))
            
        for n in self.nodes:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_breadcrumb(self):
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj %}')
        html = tpl.render(Context({'obj': self.nodes[5].content_object}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in (self.nodes[0], self.nodes[1], self.nodes[4]) :
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_breadcrumb_out_of_navigation(self):
        for n in self.nodes:
            n.in_navigation = False
            n.save()
        
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj %}')
        html = tpl.render(Context({'obj': self.nodes[5].content_object}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in (self.nodes[0], self.nodes[1], self.nodes[4]) :
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)

    def test_view_breadcrumb_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj li_template=cst_tpl%}')
        
        html = tpl.render(Context({'obj': self.nodes[5].content_object, 'cst_tpl': cst_tpl}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_breadcrumb_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj li_template=coop_cms/test_li.html%}')
        
        html = tpl.render(Context({'obj': self.nodes[5].content_object}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_children(self):
        tpl = Template('{% load coop_navigation %}{%navigation_children obj %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        
        for n in self.nodes[4:]:
            self.assertTrue(html.find(n.content_object.url)>=0)
            
        for n in self.nodes[:4]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_children_out_of_navigation(self):
        self.nodes[1].in_navigation = False
        self.nodes[1].save()
        
        self.nodes[5].in_navigation = False
        self.nodes[5].save()
        
        tpl = Template('{% load coop_navigation %}{%navigation_children obj %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        
        for n in (self.nodes[4], ):
            self.assertTrue(html.find(n.content_object.url)>=0)
            
        for n in self.nodes[:4] + [self.nodes[5]]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_children_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{%navigation_children obj  li_template=cst_tpl %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object, 'cst_tpl': cst_tpl}))
        
        for n in self.nodes[4:]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_children_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{%navigation_children obj li_template=coop_cms/test_li.html %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        
        for n in self.nodes[4:]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_children_order(self):
        self._insert_new_node()
        nodes = self.nodes[3].get_children(in_navigation=True)
        tpl = Template('{% load coop_navigation %}{%navigation_children obj%}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        positions = [html.find(n.content_object.url) for n in nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
            
    def test_view_siblings(self):
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj %}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object}))
        for n in self.nodes[:3]:
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in self.nodes[3:]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
    
    def test_view_siblings_order(self):
        self._insert_new_node()
        all_nodes = [n for n in self.nodes]
        nodes = all_nodes[-1].get_siblings(in_navigation=True)
        tpl = Template('{% load coop_navigation %}{%navigation_siblings obj%}')
        html = tpl.render(Context({'obj': all_nodes[-1].content_object}))
        positions = [html.find(n.content_object.url) for n in nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
            
    def test_view_siblings_out_of_navigation(self):
        self.nodes[2].in_navigation = False
        self.nodes[2].save()
        
        self.nodes[5].in_navigation = False
        self.nodes[5].save()
        
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj %}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object}))
        
        for n in self.nodes[:2]:
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in self.nodes[2:]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
    
    def test_view_siblings_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj li_template=cst_tpl%}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object, 'cst_tpl': cst_tpl}))
        
        for n in self.nodes[:3]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_siblings_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj li_template=coop_cms/test_li.html%}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object}))
        
        for n in self.nodes[:3]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_navigation_no_nodes(self):
        NavNode.objects.all().delete()
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({})).replace(' ', '')
        self.assertEqual(html, '')
            
    def test_breadcrumb_no_nodes(self):
        NavNode.objects.all().delete()
        link = Link.objects.get(url='http://www.python.org')
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj %}')
        html = tpl.render(Context({'obj': link})).replace(' ', '')
        self.assertEqual(html, '')
            
    def test_children_no_nodes(self):
        NavNode.objects.all().delete()
        link = Link.objects.get(url='http://www.python.org')
        tpl = Template('{% load coop_navigation %}{%navigation_children obj %}')
        html = tpl.render(Context({'obj': link })).replace(' ', '')
        self.assertEqual(html, '')
            
    def test_siblings_no_nodes(self):
        NavNode.objects.all().delete()
        link = Link.objects.get(url='http://www.python.org')
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj %}')
        html = tpl.render(Context({'obj': link})).replace(' ', '')
        self.assertEqual(html, '')
               
        
class CmsEditTagTest(TestCase):
    
    def setUp(self):
        

        self.link1 = Link.objects.create(url='http://www.google.fr')
        self.tree = tree = get_navTree_class().objects.create()
        NavNode.objects.create(tree=tree, label=self.link1.url, content_object=self.link1, ordering=1, parent=None)
    
    def _log_as_editor(self):
        self.user = user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
        ct = ContentType.objects.get_for_model(get_article_class())
        
        perm = 'change_{0}'.format(ct.model)
        can_edit_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_edit_article)
        
        perm = 'add_{0}'.format(ct.model)
        can_add_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_add_article)
        
        user.save()
        
        self.client.login(username='toto', password='toto')
        
    def _create_article(self):
        Article = get_article_class()
        article = Article.objects.create(
            title='test', content='<h1>Ceci est un test</h1>', publication=BaseArticle.PUBLISHED,
            template="test/nav_tag_in_edit_tag.html")
        NavNode.objects.create(tree=self.tree, label=article.title, content_object=article, ordering=1, parent=None)
        return article
        
    def test_view_navigation_inside_cms_edit_tag_visu(self):
        article = self._create_article()
        
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
        self.assertContains(response, "Hello") #text in template
        self.assertContains(response, article.content)
        self.assertContains(response, self.link1.url)
 
    def test_view_navigation_inside_cms_edit_tag_edition(self):
        self._log_as_editor()
        article = self._create_article()
        
        response = self.client.get(article.get_edit_url(), follow=True)
        self.assertEqual(200, response.status_code)
        
        self.assertContains(response, "Hello")
        self.assertContains(response, article.content)
        self.assertContains(response, self.link1.url)
        
class DownloadDocTest(TestCase):

    def _clean_files(self):
        dirs = (settings.DOCUMENT_FOLDER, settings.PRIVATE_DOCUMENT_FOLDER)
        for d in dirs:
            try:
                dir_name = '{0}/{1}'.format(settings.MEDIA_ROOT, d)
                shutil.rmtree(dir_name)
            except:
                pass
    
    def setUp(self):
        settings.DOCUMENT_FOLDER = '_unittest_docs'
        settings.PRIVATE_DOCUMENT_FOLDER = '_unittest_private_docs'
        self._clean_files()
        u = User.objects.create(username='toto')
        u.is_superuser = True
        u.set_password('toto')
        u.save()

    def tearDown(self):
        self._clean_files()
        
    def _get_file(self, file_name='unittest1.txt'):
        full_name = os.path.normpath(os.path.dirname(__file__) + '/fixtures/' + file_name)
        return open(full_name, 'rb')
    
    def test_upload_public_doc(self):
        data = {
            'doc': self._get_file(),
            'is_private': False,
            'descr': 'a test file',
        }
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        public_docs = Document.objects.filter(is_private=False)
        self.assertEquals(1, public_docs.count())
        self.assertEqual(public_docs[0].name, data['descr'])
        f = public_docs[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file().read())
        
    def test_upload_doc_missing_fields(self):
        data = {
            'is_private': False,
        }
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, 'close_popup_and_media_slide')
        self.assertEquals(0, Document.objects.all().count())

    def test_upload_doc_anonymous_user(self):
        data = {
            'doc': self._get_file(),
            'is_private': False,
        }
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, 'close_popup_and_media_slide')
        self.assertEquals(0, Document.objects.all().count())
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)

        
    def test_upload_private_doc(self):
        data = {
            'doc': self._get_file(),
            'is_private': True,
        }
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        private_docs = Document.objects.filter(is_private=True)
        self.assertEquals(1, private_docs.count())
        self.assertEqual(private_docs[0].name, 'unittest1')
        f = private_docs[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file().read())
    
    def test_view_docs(self):
        file1 = File(self._get_file())
        doc1 = mommy.make_one(Document, is_private=True, file=file1)
        file2 = File(self._get_file())
        doc2 = mommy.make_one(Document, is_private=False, file=file2)
        
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.get(reverse('coop_cms_media_documents'))
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, reverse('coop_cms_download_doc', args=[doc1.id]))
        self.assertNotContains(response, doc1.file.url)
        self.assertNotContains(response, reverse('coop_cms_download_doc', args=[doc2.id]))
        self.assertContains(response, doc2.file.url)
        
    def test_view_docs_anonymous(self):
        response = self.client.get(reverse('coop_cms_media_documents'), follow=True)
        self.assertEqual(response.status_code, 200)
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)
    
    def test_download_public(self):
        #create a public doc
        file = File(self._get_file())
        doc = mommy.make_one(Document, is_private=False, file=file)
        
        #check the url
        private_url = reverse('coop_cms_download_doc', args=[doc.id])
        self.assertNotEqual(doc.get_download_url(), private_url)
        
        #login and download
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, self._get_file().read())
        
        #logout and download
        self.client.logout()
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self._get_file().read())
        
    
    def test_download_private(self):
        #create a public doc
        file = File(self._get_file())
        doc = mommy.make_one(Document, is_private=True, file=file)
        
        #check the url
        private_url = reverse('coop_cms_download_doc', args=[doc.id])
        self.assertEqual(doc.get_download_url(), private_url)
        
        #login and download
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response['Content-Disposition'], "attachment; filename=unittest1.txt")
        self.assertEquals(response['Content-Type'], "text/plain")
        self.assertEqual(response.content, self._get_file().read())
        
        #logout and download
        self.client.logout()
        response = self.client.get(doc.get_download_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)
        
        
class NewsletterTest(TestCase):
    
    def setUp(self):
        self.editor = None

    def _log_as_editor(self):
        if not self.editor:
            self.editor = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
            self.editor.is_staff = True
            can_edit_newsletter = Permission.objects.get(content_type__app_label='coop_cms', codename='change_newsletter')
            self.editor.user_permissions.add(can_edit_newsletter)
            self.editor.save()
        
        self.client.login(username='toto', password='toto')
        
    def test_create_article_for_newsletter(self):
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        
        art = Article.objects.create(in_newsletter=True)
        self.assertEqual(1, NewsletterItem.objects.count())
        item = NewsletterItem.objects.get(content_type=ct, object_id=art.id)
        self.assertEqual(item.content_object, art)
        
        art.delete()
        self.assertEqual(0, NewsletterItem.objects.count())

    def test_create_article_not_for_newsletter(self):
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        
        art = Article.objects.create(in_newsletter=False)
        self.assertEqual(0, NewsletterItem.objects.count())
        
        art.delete()
        self.assertEqual(0, NewsletterItem.objects.count())

    def test_create_article_commands(self):
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        art1 = Article.objects.create(in_newsletter=True)
        art2 = Article.objects.create(in_newsletter=True)
        art3 = Article.objects.create(in_newsletter=False)
        self.assertEqual(2, NewsletterItem.objects.count())
        NewsletterItem.objects.all().delete()
        self.assertEqual(0, NewsletterItem.objects.count())
        management.call_command('create_newsletter_items', verbosity=0, interactive=False)
        self.assertEqual(2, NewsletterItem.objects.count())
        item1 = NewsletterItem.objects.get(content_type=ct, object_id=art1.id)
        item2 = NewsletterItem.objects.get(content_type=ct, object_id=art2.id)

    def test_view_newsletter(self):
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        
        art1 = mommy.make_one(Article, title="Art 1", in_newsletter=True)
        art2 = mommy.make_one(Article, title="Art 2", in_newsletter=True)
        art3 = mommy.make_one(Article, title="Art 3", in_newsletter=True)
        
        newsletter = mommy.make_one(Newsletter, content="a little intro for this newsletter",
            template="test/newsletter_blue.html")
        newsletter.items.add(NewsletterItem.objects.get(content_type=ct, object_id=art1.id))
        newsletter.items.add(NewsletterItem.objects.get(content_type=ct, object_id=art2.id))
        newsletter.save()
        
        url = reverse('coop_cms_view_newsletter', args=[newsletter.id])
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        
        self.assertContains(response, newsletter.content)
        self.assertContains(response, art1.title)
        self.assertContains(response, art2.title)
        self.assertNotContains(response, art3.title)
        
    def test_edit_newsletter(self):
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        
        art1 = mommy.make_one(Article, title="Art 1", in_newsletter=True)
        art2 = mommy.make_one(Article, title="Art 2", in_newsletter=True)
        art3 = mommy.make_one(Article, title="Art 3", in_newsletter=True)
        
        newsletter = mommy.make_one(Newsletter, content="a little intro for this newsletter",
            template="test/newsletter_blue.html")
        newsletter.items.add(NewsletterItem.objects.get(content_type=ct, object_id=art1.id))
        newsletter.items.add(NewsletterItem.objects.get(content_type=ct, object_id=art2.id))
        newsletter.save()
        
        self._log_as_editor()
        url = reverse('coop_cms_edit_newsletter', args=[newsletter.id])
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        
        self.assertContains(response, newsletter.content)
        self.assertContains(response, art1.title)
        self.assertContains(response, art2.title)
        self.assertNotContains(response, art3.title)
        
        data = {'content': 'A better intro'}
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        self.assertNotContains(response, newsletter.content)
        self.assertContains(response, data['content'])
        self.assertContains(response, art1.title)
        self.assertContains(response, art2.title)
        self.assertNotContains(response, art3.title)
        
    def test_edit_newsletter_anonymous(self):
        original_data = {'content': "a little intro for this newsletter",
            'template': "test/newsletter_blue.html"}
        newsletter = mommy.make_one(Newsletter, **original_data)
        
        url = reverse('coop_cms_edit_newsletter', args=[newsletter.id])
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        
        response = self.client.post(url, data={'content': ':OP'})
        self.assertEqual(302, response.status_code)
        
        newsletter = Newsletter.objects.get(id=newsletter.id)
        self.assertEqual(newsletter.content, original_data['content'])
        
    def test_edit_newsletter_no_articles(self):
        self._log_as_editor()
        original_data = {'content': "a little intro for this newsletter",
            'template': "test/newsletter_blue.html"}
        newsletter = mommy.make_one(Newsletter, **original_data)
        
        url = reverse('coop_cms_edit_newsletter', args=[newsletter.id])
        
        data = {'content': ':OP'}
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, data['content'])
        
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, data['content'])
        
    def test_newsletter_templates(self):
        
        Article = get_article_class()
        ct = ContentType.objects.get_for_model(Article)
        
        art1 = mommy.make_one(Article, title="Art 1", in_newsletter=True)
        poh = mommy.make_one(PieceOfHtml, div_id="newsletter_header", content="HELLO!!!")
        
        newsletter = mommy.make_one(Newsletter, content="a little intro for this newsletter",
            template="test/newsletter_blue.html")
        newsletter.items.add(NewsletterItem.objects.get(content_type=ct, object_id=art1.id))
        newsletter.save()
        
        self._log_as_editor()
        
        view_names = ['coop_cms_view_newsletter', 'coop_cms_edit_newsletter']
        for view_name in view_names:
            url = reverse(view_name, args=[newsletter.id])
            response = self.client.get(url)
            self.assertEqual(200, response.status_code)
            
            self.assertContains(response, newsletter.content)
            self.assertContains(response, art1.title)
            self.assertContains(response, "background: blue;")
            self.assertNotContains(response, poh.content)
        
        newsletter.template = "test/newsletter_red.html"
        newsletter.save()
        
        for view_name in view_names:
            url = reverse(view_name, args=[newsletter.id])
            response = self.client.get(url)
            
            self.assertEqual(200, response.status_code)
            
            self.assertContains(response, newsletter.content)
            self.assertContains(response, art1.title)
            self.assertContains(response, "background: red;")
            self.assertContains(response, poh.content)
            
    def test_change_newsletter_templates(self):
        settings.COOP_CMS_NEWSLETTER_TEMPLATES = (
            ('test/newsletter_red.html', 'Red'),
            ('test/newsletter_blue.html', 'Blue'),
        )
        self._log_as_editor()
        
        newsletter = mommy.make_one(Newsletter, template='test/newsletter_blue.html')
        
        url = reverse('coop_cms_change_newsletter_template', args=[newsletter.id])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
        for tpl, name in settings.COOP_CMS_NEWSLETTER_TEMPLATES:
            self.assertContains(response, tpl)
            self.assertContains(response, name)
            
        data={'template': 'test/newsletter_red.html'}
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, reverse('coop_cms_edit_newsletter', args=[newsletter.id]))
        
        newsletter = Newsletter.objects.get(id=newsletter.id)
        self.assertEqual(newsletter.template, data['template'])
        
    def test_change_newsletter_templates_anonymous(self):
        settings.COOP_CMS_NEWSLETTER_TEMPLATES = (
            ('test/newsletter_red.html', 'Red'),
            ('test/newsletter_blue.html', 'Blue'),
        )
        original_data={'template': 'test/newsletter_blue.html'}
        newsletter = mommy.make_one(Newsletter, **original_data)
        
        url = reverse('coop_cms_change_newsletter_template', args=[newsletter.id])
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        
        data={'template': 'test/newsletter_red.html'}
        response = self.client.post(url, data=data)
        self.assertEqual(302, response.status_code)
        
        newsletter = Newsletter.objects.get(id=newsletter.id)
        self.assertEqual(newsletter.template, original_data['template'])
        
    def test_change_newsletter_unknow_template(self):
        settings.COOP_CMS_NEWSLETTER_TEMPLATES = (
            ('test/newsletter_red.html', 'Red'),
            ('test/newsletter_blue.html', 'Blue'),
        )
        original_data={'template': 'test/newsletter_blue.html'}
        newsletter = mommy.make_one(Newsletter, **original_data)
        
        self._log_as_editor()
        url = reverse('coop_cms_change_newsletter_template', args=[newsletter.id])
        data={'template': 'test/newsletter_yellow.html'}
        response = self.client.post(url, data=data)
        self.assertEqual(200, response.status_code)
        
        newsletter = Newsletter.objects.get(id=newsletter.id)
        self.assertEqual(newsletter.template, original_data['template'])
        
    def test_send_test_newsletter(self, template='test/newsletter_blue.html'):
        settings.COOP_CMS_FROM_EMAIL = 'contact@toto.fr'
        settings.COOP_CMS_TEST_EMAILS = ('toto@toto.fr', 'titi@toto.fr')
        settings.COOP_CMS_SITE_PREFIX = 'http://toto.fr'
        
        rel_content = '''
            <h1>Title</h1><a href="{0}/toto/"><img src="{0}/toto.jpg"></a><br /><img src="{0}/toto.jpg">
            <div><a href="http://www.google.fr">Google</a></div>
        '''
        original_data = {
            'template': template,
            'subject': 'test email',
            'content': rel_content.format("")
        }
        newsletter = mommy.make_one(Newsletter, **original_data)
        
        self._log_as_editor()
        url = reverse('coop_cms_test_newsletter', args=[newsletter.id])
        response = self.client.post(url, data={})
        self.assertEqual(200, response.status_code)
        
        self.assertEqual([[e] for e in settings.COOP_CMS_TEST_EMAILS], [e.to for e in mail.outbox])
        for e in mail.outbox:
            self.assertEqual(e.from_email, settings.COOP_CMS_FROM_EMAIL)
            self.assertEqual(e.subject, newsletter.subject)
            self.assertTrue(e.body.find('Title')>=0)
            self.assertTrue(e.body.find('Google')>=0)
            self.assertTrue(e.alternatives[0][1], "text/html")
            self.assertTrue(e.alternatives[0][0].find('Title')>=0)
            self.assertTrue(e.alternatives[0][0].find('Google')>=0)
            self.assertTrue(e.alternatives[0][0].find(settings.COOP_CMS_SITE_PREFIX)>=0)
        
    def test_schedule_newsletter_sending(self):
        newsletter = mommy.make_one(Newsletter)
        
        self._log_as_editor()
        url = reverse('coop_cms_schedule_newsletter_sending', args=[newsletter.id])
        
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
        sch_dt = "2030-12-12 12:00:00"
        response = self.client.post(url, data={'scheduling_dt': sch_dt})
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '$.colorbox.close()')
        self.assertEqual(1, NewsletterSending.objects.count())
        self.assertEqual(newsletter, NewsletterSending.objects.all()[0].newsletter)
        self.assertEqual(2030, NewsletterSending.objects.all()[0].scheduling_dt.year)
        
    def test_schedule_newsletter_sending_invalid_value(self):
        newsletter = mommy.make_one(Newsletter)
        
        self._log_as_editor()
        url = reverse('coop_cms_schedule_newsletter_sending', args=[newsletter.id])
        
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
        sch_dt = ''
        response = self.client.post(url, data={'scheduling_dt': sch_dt})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, NewsletterSending.objects.count())
        
        sch_dt = 'toto'
        response = self.client.post(url, data={'scheduling_dt': sch_dt})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, NewsletterSending.objects.count())
        
        sch_dt = "2005-12-12 12:00:00"
        response = self.client.post(url, data={'scheduling_dt': sch_dt})
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, NewsletterSending.objects.count())
    
    def test_schedule_anonymous(self):
        newsletter = mommy.make_one(Newsletter)
        
        login_url = reverse('django.contrib.auth.views.login')
        url = reverse('coop_cms_schedule_newsletter_sending', args=[newsletter.id])
        
        response = self.client.get(url, follow=False)
        redirect_url = response['Location']
        self.assertTrue(redirect_url.find(login_url)>0)
        
        sch_dt =datetime.now()+timedelta(1)
        response = self.client.post(url, data={'sending_dt': sch_dt})
        redirect_url = response['Location']
        self.assertTrue(redirect_url.find(login_url)>0)
    
    def test_send_newsletter(self):
        
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<h2>Hello guys!</h2><p>Visit <a href="http://toto.fr">us</a></p>',
            'template': 'test/newsletter_blue.html',
        }
        newsletter = mommy.make_one(Newsletter, **newsletter_data)
        
        sch_dt = datetime.now() - timedelta(1)
        sending = mommy.make_one(NewsletterSending, newsletter=newsletter, scheduling_dt= sch_dt, sending_dt= None)
        
        management.call_command('send_newsletter', 'toto@toto.fr', verbosity=0, interactive=False)
        
        sending = NewsletterSending.objects.get(id=sending.id)
        self.assertNotEqual(sending.sending_dt, None)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['toto@toto.fr'])
        self.assertEqual(email.subject, newsletter_data['subject'])
        self.assertTrue(email.body.find('Hello guys')>=0)
        self.assertTrue(email.alternatives[0][1], "text/html")
        self.assertTrue(email.alternatives[0][0].find('Hello guys')>=0)
        
        #check whet happens if command is called again
        mail.outbox = []
        management.call_command('send_newsletter', 'toto@toto.fr', verbosity=0, interactive=False)
        self.assertEqual(len(mail.outbox), 0)
        
        
    def test_send_newsletter_several(self):
        
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<h2>Hello guys!</h2><p>Visit <a href="http://toto.fr">us</a></p>',
            'template': 'test/newsletter_blue.html',
        }
        newsletter = mommy.make_one(Newsletter, **newsletter_data)
        
        sch_dt = datetime.now() - timedelta(1)
        sending = mommy.make_one(NewsletterSending, newsletter=newsletter, scheduling_dt= sch_dt, sending_dt= None)
        
        addresses = ';'.join(['toto@toto.fr']*5)
        management.call_command('send_newsletter', addresses, verbosity=0, interactive=False)
        
        sending = NewsletterSending.objects.get(id=sending.id)
        self.assertNotEqual(sending.sending_dt, None)
        
        self.assertEqual(len(mail.outbox), 5)
        for email in mail.outbox:
            self.assertEqual(email.to, ['toto@toto.fr'])
            self.assertEqual(email.subject, newsletter_data['subject'])
            self.assertTrue(email.body.find('Hello guys')>=0)
            self.assertTrue(email.alternatives[0][1], "text/html")
            self.assertTrue(email.alternatives[0][0].find('Hello guys')>=0)
        
        #check whet happens if command is called again
        mail.outbox = []
        management.call_command('send_newsletter', 'toto@toto.fr', verbosity=0, interactive=False)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_newsletter_not_yet(self):
        
        newsletter_data = {
            'subject': 'This is the subject',
            'content': '<h2>Hello guys!</h2><p>Visit <a href="http://toto.fr">us</a></p>',
            'template': 'test/newsletter_blue.html',
        }
        newsletter = mommy.make_one(Newsletter, **newsletter_data)
        
        sch_dt = datetime.now() + timedelta(1)
        sending = mommy.make_one(NewsletterSending, newsletter=newsletter, scheduling_dt= sch_dt, sending_dt= None)
        
        management.call_command('send_newsletter', 'toto@toto.fr', verbosity=0, interactive=False)
        
        sending = NewsletterSending.objects.get(id=sending.id)
        self.assertEqual(sending.sending_dt, None)
        
        self.assertEqual(len(mail.outbox), 0)
        
class AbsUrlTest(TestCase):
    
    def test_href(self):
        test_html = '<a href="%s/toto">This is a link</a>'
        rel_html = test_html % ""
        abs_html = test_html % settings.COOP_CMS_SITE_PREFIX
        self.assertEqual(abs_html, make_links_absolute(rel_html))
        
    def test_src(self):
        test_html = '<h1>My image</h1><img src="%s/toto">'
        rel_html = test_html % ""
        abs_html = test_html % settings.COOP_CMS_SITE_PREFIX
        self.assertEqual(abs_html, make_links_absolute(rel_html))
        
    def test_relative_path(self):
        test_html = '<h1>My image</h1><img src="%s/toto">'
        rel_html = test_html % "../../.."
        abs_html = test_html % settings.COOP_CMS_SITE_PREFIX
        self.assertEqual(abs_html, make_links_absolute(rel_html))
    
    def test_src_and_img(self):
        test_html = '<h1>My image</h1><a href="{0}/a1">This is a link</a><img src="{0}/toto"><img src="{0}/titi"><a href="{0}/a2">This is another link</a>'
        rel_html = test_html.format("")
        abs_html = test_html.format(settings.COOP_CMS_SITE_PREFIX)
        self.assertEqual(abs_html, make_links_absolute(rel_html))
        
    def test_href_rel_and_abs(self):
        test_html = '<a href="%s/toto">This is a link</a><a href="http://www.apidev.fr">another</a>'
        rel_html = test_html % ""
        abs_html = test_html % settings.COOP_CMS_SITE_PREFIX
        self.assertEqual(abs_html, make_links_absolute(rel_html))
        
class NavigationTreeTest(TestCase):
    
    def setUp(self):
        ct = ContentType.objects.get_for_model(get_article_class())
        nt_articles = NavType.objects.create(content_type=ct, search_field='title',
            label_rule=NavType.LABEL_USE_SEARCH_FIELD)
        
        ct = ContentType.objects.get(app_label='coop_cms', model='link')
        nt_links = NavType.objects.create(content_type=ct, search_field='url',
            label_rule=NavType.LABEL_USE_SEARCH_FIELD)
        
        self.default_tree = get_navTree_class().objects.create()
        self.tree1 = get_navTree_class().objects.create(name="tree1")
        self.tree2 = get_navTree_class().objects.create(name="tree2")
        self.tree2.types.add(nt_links)
        self.tree2.save()
        
    def test_view_default_navigation(self):
        tpl = Template('{% load coop_navigation %}{% navigation_as_nested_ul %}')
        
        link1 = Link.objects.create(url='http://www.google.fr')
        link2 = Link.objects.create(url='http://www.apidev.fr')
        art1 = get_article_class().objects.create(title='Article Number One', content='oups')
        art2 = get_article_class().objects.create(title='Article Number Two', content='hello')
        art3 = get_article_class().objects.create(title='Article Number Three', content='bye-bye')
        
        node1 = NavNode.objects.create(tree=self.default_tree, label=link1.url, content_object=link1, ordering=1, parent=None)
        node2 = NavNode.objects.create(tree=self.default_tree, label=art1.title, content_object=art1, ordering=2, parent=None)
        node3 = NavNode.objects.create(tree=self.default_tree, label=art2.title, content_object=art2, ordering=1, parent=node2)
        node4 = NavNode.objects.create(tree=self.tree1, label=art3.title, content_object=art3, ordering=1, parent=None)
        node5 = NavNode.objects.create(tree=self.tree1, label=art1.title, content_object=art1, ordering=2, parent=None)
        node6 = NavNode.objects.create(tree=self.tree1, label=link2.url, content_object=link2, ordering=2, parent=node5)
        
        nodes_in, nodes_out = [art1, art2, link1], [art3, link2]
        
        html = tpl.render(Context({}))
        
        for n in nodes_in:
            self.assertTrue(html.find(unicode(n))>=0)
            
        for n in nodes_out:
            self.assertFalse(html.find(unicode(n))>=0)
            
    def test_view_alternative_navigation(self):
        tpl = Template('{% load coop_navigation %}{% navigation_as_nested_ul tree=tree1 %}')
        
        link1 = Link.objects.create(url='http://www.google.fr')
        link2 = Link.objects.create(url='http://www.apidev.fr')
        art1 = get_article_class().objects.create(title='Article Number One', content='oups')
        art2 = get_article_class().objects.create(title='Article Number Two', content='hello')
        art3 = get_article_class().objects.create(title='Article Number Three', content='bye-bye')
        
        node1 = NavNode.objects.create(tree=self.default_tree, label=link1.url, content_object=link1, ordering=1, parent=None)
        node2 = NavNode.objects.create(tree=self.default_tree, label=art1.title, content_object=art1, ordering=2, parent=None)
        node3 = NavNode.objects.create(tree=self.default_tree, label=art2.title, content_object=art2, ordering=1, parent=node2)
        node4 = NavNode.objects.create(tree=self.tree1, label=art3.title, content_object=art3, ordering=1, parent=None)
        node5 = NavNode.objects.create(tree=self.tree1, label=art1.title, content_object=art1, ordering=2, parent=None)
        node6 = NavNode.objects.create(tree=self.tree1, label=link2.url, content_object=link2, ordering=2, parent=node5)
        
        nodes_in, nodes_out = [art1, art3, link2], [art2, link1]
        
        html = tpl.render(Context({}))
        
        for n in nodes_in:
            self.assertTrue(html.find(unicode(n))>=0)
            
        for n in nodes_out:
            self.assertFalse(html.find(unicode(n))>=0)
            
            
    def test_view_several_navigation(self):
        tpl = Template('{% load coop_navigation %}{% navigation_as_nested_ul tree=tree1 %}{% navigation_as_nested_ul tree=tree2 %}{% navigation_as_nested_ul %}')
        
        link1 = Link.objects.create(url='http://www.google.fr')
        link2 = Link.objects.create(url='http://www.apidev.fr')
        art1 = get_article_class().objects.create(title='Article Number One', content='oups')
        art2 = get_article_class().objects.create(title='Article Number Two', content='hello')
        art3 = get_article_class().objects.create(title='Article Number Three', content='bye-bye')
        
        node1 = NavNode.objects.create(tree=self.default_tree, label=link1.url, content_object=link1, ordering=1, parent=None)
        node2 = NavNode.objects.create(tree=self.default_tree, label=art1.title, content_object=art1, ordering=2, parent=None)
        node3 = NavNode.objects.create(tree=self.default_tree, label=art2.title, content_object=art2, ordering=1, parent=node2)
        node4 = NavNode.objects.create(tree=self.tree1, label=art3.title, content_object=art3, ordering=1, parent=None)
        node5 = NavNode.objects.create(tree=self.tree1, label=art1.title, content_object=art1, ordering=2, parent=None)
        node6 = NavNode.objects.create(tree=self.tree2, label=link2.url, content_object=link2, ordering=2, parent=node5)
        
        nodes_in = [art1, art3, link2, art2, link1]
        
        html = tpl.render(Context({}))
        
        for n in nodes_in:
            self.assertTrue(html.find(unicode(n))>=0)
            
class HomepageTest(TestCase):
    
    def test_only_one_homepage(self):
        a1 = get_article_class().objects.create(title="python", content='python')
        a2 = get_article_class().objects.create(title="django", content='django', is_homepage=True)
        a3 = get_article_class().objects.create(title="home", content='homepage')
        
        self.assertEqual(1, get_article_class().objects.filter(is_homepage=True).count())
        self.assertEqual(a2.title, get_article_class().objects.filter(is_homepage=True)[0].title)
        
        a3.is_homepage = True
        a3.save()
        
        self.assertEqual(1, get_article_class().objects.filter(is_homepage=True).count())
        self.assertEqual(a3.title, get_article_class().objects.filter(is_homepage=True)[0].title)
        
    def test_only_one_homepage_again(self):
        a1 = get_article_class().objects.create(title="python", content='python')
        a2 = get_article_class().objects.create(title="django", content='django')
        a3 = get_article_class().objects.create(title="home", content='homepage')
        
        self.assertEqual(0, get_article_class().objects.filter(is_homepage=True).count())
        
        a3.is_homepage = True
        a3.save()
        
        self.assertEqual(1, get_article_class().objects.filter(is_homepage=True).count())
        self.assertEqual(a3.title, get_article_class().objects.filter(is_homepage=True)[0].title)
        