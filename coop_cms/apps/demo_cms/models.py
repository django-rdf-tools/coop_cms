# -*- coding: utf-8 -*-
from django.db import models
from coop_cms.models import BaseArticle
from django.contrib.auth.models import User

class Article(BaseArticle):
    author = models.ForeignKey(User, blank=True, default=None, null=True)

class ModeratedArticle(Article):
    class Meta:
        proxy = True
        
    def can_publish_article(self, user):
        return user.is_superuser
    
class PrivateArticle(Article):
    class Meta:
        proxy = True
        
    def can_view_article(self, user):
        return (self.author == user)
        
    def can_edit_article(self, user):
        return (self.author == user)
        
    def can_publish_article(self, user):
        return (self.author == user)