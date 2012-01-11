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
from coop_cms.settings import get_article_class


class ArticleTest(TestCase):
    
    def _log_as_editor(self):
        user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
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
        
    def test_no_malicious_when_editing(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=Article.PUBLISHED, **initial_data)
        
        data1 = {'content': "<script>alert('aahhh');</script>", 'title': 'ok'}
        data2 = {'title': '<a href="/">home</a>', 'content': 'ok'}
        
        self._log_as_editor()
        response = self.client.post(article.get_edit_url(), data=data1, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article_not_changed(article, data1, initial_data)
        
        response = self.client.post(article.get_edit_url(), data=data2, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article_not_changed(article, data2, initial_data)
        
    def test_publish_article(self):
        initial_data = {'title': "test", 'content': "this is my article content"}
        article = get_article_class().objects.create(publication=Article.DRAFT, **initial_data)
        
        self._log_as_editor()
        response = self.client.post(article.get_publish_url(), data={}, follow=True)
        self.assertEqual(response.status_code, 200)
        
        article = get_article_class().objects.get(id=article.id)
        self.assertEqual(article.title, initial_data['title'])
        self.assertEqual(article.content, initial_data['content'])
        self.assertEqual(article.publication, Article.PUBLISHED)
