from django import forms
from coop_cms.models import NavType, NavNode
from django.contrib.contenttypes.models import ContentType
from settings import get_navigable_content_types
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from djaloha.widgets import AlohaInput
import floppyforms
import re
from django.conf import settings
from coop_cms.settings import get_article_class, get_article_templates
from coop_cms.widgets import ImageEdit
from django.core.urlresolvers import reverse
from coop_cms.utils import dehtml

class NavTypeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NavTypeForm, self).__init__(*args, **kwargs)
        self.fields['content_type'].widget = forms.Select(choices=get_navigable_content_types())
        
    def clean_label_rule(self):
        rule = self.cleaned_data['label_rule']
        if rule == NavType.LABEL_USE_GET_LABEL:
            ct = self.cleaned_data['content_type']
            if not 'get_label' in dir(ct.model_class()):
                raise ValidationError(_("Invalid rule for this content type: The object class doesn't have a get_label method"))
        return rule

    class Meta:
        model = NavType

class ArticleForm(floppyforms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        self.article = kwargs.get('instance', None)
        self.set_logo_size()

    class Meta:
        model = get_article_class()
        fields = ('title', 'content', 'logo')
        widgets = {
            'title': AlohaInput(),
            'content': AlohaInput(),
        }
        
    def set_logo_size(self, logo_size=None):
        thumbnail_src = self.logo_thumbnail(logo_size)
        update_url = reverse('coop_cms_update_logo', args=[self.article.id])
        self.fields['logo'].widget = ImageEdit(update_url, thumbnail_src.url if thumbnail_src else '')
        
    def logo_thumbnail(self, logo_size=None):
        if self.article:
            return self.article.logo_thumbnail(True, logo_size=logo_size)

    class Media:
        css = {
            'all': ('css/colorbox.css',),
        }
        js = ('js/jquery.form.js', 'js/jquery.pageslide.js', 'js/jquery.colorbox-min.js')

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if title[-4:].lower() == '<br>':
            title = title[:-4]
        if not title:
            raise ValidationError(_("Title can not be empty"))

        #if re.search(u'<(.*)>', title):
        #    raise ValidationError(_(u'HTML content is not allowed in the title'))
        
        return title
    
    
def get_node_choices():
    prefix = "--"
    choices = [(None, _(u'<not in navigation>')), (0, _(u'<root node>'))]
    for root_node in NavNode.objects.filter(parent__isnull=True).order_by('ordering'):
        for (progeny, level) in root_node.get_progeny():
            choices.append((progeny.id, prefix*level+progeny.label))
    return choices

def get_navigation_parent_help_text():
    return get_article_class().navigation_parent.__doc__

class ArticleAdminForm(forms.ModelForm):
    
    navigation_parent = forms.ChoiceField(
        choices=get_node_choices(), required=False, help_text=get_navigation_parent_help_text()
    )
    
    def __init__(self, *args, **kwargs):
        super(ArticleAdminForm, self).__init__(*args, **kwargs)
        self.article = kwargs.get('instance', None)
        self.fields['navigation_parent'] = forms.ChoiceField(
           choices=get_node_choices(), required=False, help_text=get_navigation_parent_help_text()
        )
        if self.article:
            self.initial['navigation_parent'] = self.article.navigation_parent
        templates = get_article_templates(self.article, self.current_user)
        if templates:
            self.fields['template'].widget = forms.Select(choices=templates)
    
    def clean_navigation_parent(self):
        parent_id = self.cleaned_data['navigation_parent']
        parent_id = int(parent_id) if parent_id != 'None' else None
        if self.article:
            ct = ContentType.objects.get_for_model(get_article_class())
            try:
                node = NavNode.objects.get(object_id=self.article.id, content_type=ct)
                #raise ValidationError if own parent or child of its own child
                node.check_new_navigation_parent(parent_id)
            except NavNode.DoesNotExist:
                pass
        return parent_id
    
    def save(self, commit=True):
        article = super(ArticleAdminForm, self).save(commit=False)
        parent_id = self.cleaned_data['navigation_parent']
        if article.id:
            article.navigation_parent = parent_id
        else:
            setattr(article, '_navigation_parent', parent_id)
        if commit:
            article.save()
        return article
    
    class Meta:
        model = get_article_class()
        widgets = {
            'title': forms.TextInput(attrs={'size': 100})
        }

class AddImageForm(forms.Form):
    image = forms.ImageField(required=True, label = _('Image'),)
    descr = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'size': '35', 'placeholder': _(u'Optional description'),}),
        label = _('Description'),
    )

class AddDocForm(forms.Form):
    doc = forms.FileField(required=True, label = _('File'),)
    descr = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'size': '35', 'placeholder': _(u'Optional description'),}),
        label = _('Description'),
    )
    is_private = forms.BooleanField(required=False)

class ArticleTemplateForm(forms.Form):
    def __init__(self, article, user, *args, **kwargs):
        super(ArticleTemplateForm, self).__init__(*args, **kwargs)
        choices = get_article_templates(article, user)
        if choices:
            self.fields["template"] = forms.ChoiceField(choices=choices)
        else:
            self.fields["template"] = forms.CharField()
        self.fields["template"].initial = article.template
        
    
class ArticleLogoForm(forms.Form):
    image = forms.ImageField(required=True, label = _('Logo'),)

class PublishArticleForm(forms.ModelForm):
    class Meta:
        model = get_article_class()
        fields = ('summary', 'section')
    
    def __init__(self, *args, **kwargs):
        article = kwargs['instance']
        try:
            initials = kwargs['initial']
        except:
            initials = {}
        summary = article.summary
        if not summary:
            summary = dehtml(article.content)[:250]
        initials.update({'summary': summary})
        kwargs['initial'] = initials
        super(PublishArticleForm, self).__init__(*args, **kwargs)
        
            
        
