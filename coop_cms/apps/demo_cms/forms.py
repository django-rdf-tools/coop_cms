
import floppyforms as forms
from coop_cms.forms import ArticleForm as CmsArticleForm
from coop_cms.settings import get_article_class
from djaloha.widgets import AlohaInput
from django.conf import settings

class ArticleForm(CmsArticleForm):
    class Meta(CmsArticleForm.Meta):
        model = get_article_class()
        fields = CmsArticleForm.Meta.fields +('author',)
