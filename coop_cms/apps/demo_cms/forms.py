
import floppyforms as forms
from coop_cms.forms import ArticleForm as CmsArticleForm
from coop_cms.forms import NewsletterForm
from coop_cms.settings import get_article_class
from djaloha.widgets import AlohaInput
from django.conf import settings
from coop_cms.models import ArticleCategory

class ArticleForm(CmsArticleForm):
    class Meta(CmsArticleForm.Meta):
        model = get_article_class()
        fields = CmsArticleForm.Meta.fields +('author',)

class SortableNewsletterForm(NewsletterForm):
    sortable = forms.CharField(required=False, widget=forms.HiddenInput())

    class Media(NewsletterForm.Media):
        js = NewsletterForm.Media.js + ('js/jquery.sortElements.js',)

    def save(self, *args, **kwargs):
        ret = super(SortableNewsletterForm, self).save(*args, **kwargs)

        order = self.cleaned_data['sortable']
        if order:
            order = [int(x) for x in order.split(';')]
            for id in order:
                section = ArticleCategory.objects.get(id=id)
                section.ordering = order.index(id)+1
                section.save()

        return ret