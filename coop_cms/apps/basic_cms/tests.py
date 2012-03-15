# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.template import Template, Context
from coop_cms.models import Link, NavNode, NavType
from coop_cms.apps.basic_cms.models import Article
import json
from django.core.exceptions import ValidationError
from coop_cms.settings import get_article_class, get_article_templates


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
        article = get_article_class().objects.create(title="test", publication=Article.PUBLISHED)
        self.assertEqual(article.slug, 'test')
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_404_ok(self):
        response = self.client.get("/jhjhjkahekhj", follow=True)
        self.assertEqual(404, response.status_code)
        
    def test_is_navigable(self):
        article = get_article_class().objects.create(title="test", publication=Article.PUBLISHED)
        self.assertEqual('/test/', article.get_absolute_url())

    def test_create_slug(self):
        article = get_article_class().objects.create(title=u"voici l'été", publication=Article.PUBLISHED)
        self.assertEqual(article.slug, 'voici-lete')
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_edit_article(self):
        article = get_article_class().objects.create(title="test", publication=Article.PUBLISHED)
        
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
        article = get_article_class().objects.create(publication=Article.PUBLISHED, **initial_data)
        
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
        article = get_article_class().objects.create(publication=Article.PUBLISHED, **initial_data)
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
        article = get_article_class().objects.create(publication=Article.PUBLISHED, **initial_data)
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
        article = get_article_class().objects.create(publication=Article.PUBLISHED, **initial_data)
        response = self.client.get(article.get_absolute_url())
        self.assertFalse(self._is_aloha_found(response))
        
        self._log_as_editor()
        response = self.client.get(article.get_edit_url())
        self.assertTrue(self._is_aloha_found(response))
        
    def test_checks_aloah_links(self):
        slugs = ("un", "deux", "trois", "quatre")
        for slug in slugs:
            get_article_class().objects.create(publication=Article.PUBLISHED, title=slug)
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(**initial_data)
        
        self._log_as_editor()
        response = self.client.get(reverse('aloha_init'))
        
        context_slugs = [article.slug for article in response.context['links']]
        for slug in slugs:
            self.assertTrue(slug in context_slugs)
        
    def test_view_draft_article(self):
        article = get_article_class().objects.create(title="test", publication=Article.DRAFT)
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(404, response.status_code)
        self._log_as_editor()
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_accept_regular_html(self):
        article = get_article_class().objects.create(title="test", publication=Article.PUBLISHED)
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
    #    article = get_article_class().objects.create(publication=Article.PUBLISHED, **initial_data)
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
        article = get_article_class().objects.create(publication=Article.DRAFT, **initial_data)
        
        self._log_as_editor()
        
        data = {
            'publication': Article.PUBLISHED,
        }
        
        response = self.client.post(article.get_publish_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        article = get_article_class().objects.get(id=article.id)
        self.assertEqual(article.title, initial_data['title'])
        self.assertEqual(article.content, initial_data['content'])
        self.assertEqual(article.publication, Article.PUBLISHED)

    def test_draft_article(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=Article.PUBLISHED, **initial_data)
        
        self._log_as_editor()
        
        data = {
            'publication': Article.DRAFT,
        }
        
        response = self.client.post(article.get_publish_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        article = get_article_class().objects.get(id=article.id)
        self.assertEqual(article.title, initial_data['title'])
        self.assertEqual(article.content, initial_data['content'])
        self.assertEqual(article.publication, Article.DRAFT)
        
    def test_new_article(self):
        Article = get_article_class()
        
        self._log_as_editor()
        data = {
            'title': "Un titre",
            'publication': Article.DRAFT,
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
            'publication': Article.PUBLISHED,
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
            'publication': Article.DRAFT,
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
            'publication': Article.DRAFT,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': None,
        }
        
        response = self.client.post(reverse('coop_cms_new_article'), data=data, follow=True)
        self.assertEqual(403, response.status_code)
        self.assertEqual(Article.objects.count(), 0)
        
    def test_new_article_navigation(self):
        Article = get_article_class()
        
        self._log_as_editor()
        data = {
            'title': "Un titre",
            'publication': Article.PUBLISHED,
            'template': get_article_templates(None, self.user)[0][0],
            'navigation_parent': 0,
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
        
    def test_new_article_navigation_leaf(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        Article = get_article_class()
        art1 = get_article_class().objects.create(publication=Article.PUBLISHED, **initial_data)
        
        ct = ContentType.objects.get_for_model(Article)
        node1 = NavNode.objects.create(content_type=ct, object_id=art1.id)
        
        self._log_as_editor()
        data = {
            'title': "Un titre",
            'publication': Article.PUBLISHED,
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
        
        
        
        
        