# -*- coding: utf-8 -*-

from django.test import TestCase
from django.conf import settings
from model_mommy import mommy
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from coop_cms.settings import get_article_class
from coop_cms.apps.basic_cms import tests as basic_cms_tests

class ArticleTest(basic_cms_tests.ArticleTest): 
    def setUp(self):
        settings.COOP_CMS_ARTICLE_CLASS = 'coop_cms.apps.demo_cms.models.Article'

class AuthorPermissionTest(TestCase):

    def setUp(self):
        settings.COOP_CMS_ARTICLE_CLASS = 'coop_cms.apps.demo_cms.models.PrivateArticle'
        self.user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
    def tearDown(self):
        settings.COOP_CMS_ARTICLE_CLASS = 'coop_cms.apps.demo_cms.models.Article'
        
    def test_view_private_article(self):
        article = mommy.make_one(get_article_class(), author=self.user)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        
    def test_cant_view_private_article(self):
        article = mommy.make_one(get_article_class())
        
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(404, response.status_code)
        
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(404, response.status_code)
        
    def test_edit_private_article(self):
        article = mommy.make_one(get_article_class(), author=self.user)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_edit_url(), data={'title': 'A', 'content': 'B', 'author': article.author.id}, follow=True)
        #self.assertEqual(200, self.client.get(article.get_absolute_url()).status_code)
        self.assertEqual(200, response.status_code)
        article = get_article_class().objects.get(id=article.id)#refresh
        self.assertEqual('A', article.title)
        self.assertEqual('B', article.content)
        
    def test_cant_edit_private_article(self):
        article = mommy.make_one(get_article_class())
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_edit_url(), data={'title': 'A', 'content': 'B', 'author': None}, follow=True)
        self.assertEqual(403, response.status_code)
        article = get_article_class().objects.get(id=article.id)#refresh
        self.assertNotEqual('A', article.title)
        self.assertNotEqual('B', article.content)
        
    def test_publish_private_article(self):
        klass = get_article_class()
        article = mommy.make_one(klass, author=self.user)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_publish_url(), data={}, follow=True)
        self.assertEqual(200, response.status_code)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.publication, klass.PUBLISHED)
        
    def test_cant_publish_private_article(self):
        klass = get_article_class()
        article = mommy.make_one(klass)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_publish_url(), data={}, follow=True)
        self.assertEqual(403, response.status_code)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.publication, klass.DRAFT)
        
    def test_can_change_author_article(self):
        klass = get_article_class()
        article = mommy.make_one(klass, author=self.user)
        titi = User.objects.create_user('titi', 'titi@toto.fr', 'toto')
        
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        response = self.client.post(article.get_edit_url(), data={'title': 'A', 'content': 'B', 'author': titi.id}, follow=True)
        self.assertEqual(404, response.status_code)
        
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.author, titi)
        
        
class TemplateTest(TestCase):

    def setUp(self):
        settings.COOP_CMS_ARTICLE_CLASS = 'coop_cms.apps.demo_cms.models.Article'
        self.user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
    def test_view_article(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make_one(klass, publication=klass.PUBLISHED)
        response = self.client.get(article.get_absolute_url())
        self.assertTemplateUsed(response, 'coop_cms/article.html')
        self.assertEqual(200, response.status_code)
        
    def test_view_article_custom_template(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make_one(klass, publication=klass.PUBLISHED, template='standard.html')
        response = self.client.get(article.get_absolute_url())
        self.assertTemplateUsed(response, 'standard.html')
        self.assertEqual(200, response.status_code)
        
    def test_change_template(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make_one(klass)
        self.assertTrue(self.client.login(username=self.user.username, password='toto'))
        url = reverse('coop_cms_change_template', args=[article.id])
        response = self.client.post(url, data={'template': 'standard.html'}, follow=True)
        self.assertEqual(200, response.status_code)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.template, 'standard.html')
        
    def test_change_template_permission(self):
        #Check that we are do not using the PrivateArticle anymore
        klass = get_article_class()
        article = mommy.make_one(klass)
        url = reverse('coop_cms_change_template', args=[article.id])
        response = self.client.post(url, data={'template': 'standard.html'}, follow=True)
        self.assertEqual(200, response.status_code)
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)
        article = klass.objects.get(id=article.id)#refresh
        self.assertEqual(article.template, '')
        
        
        