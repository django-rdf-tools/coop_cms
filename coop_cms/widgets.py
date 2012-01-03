# -*- coding: utf-8 -*-

from floppyforms.widgets import ClearableFileInput

class ImageEdit(ClearableFileInput):
    template_name = 'coop_cms/widgets/imageedit.html'
    
    def __init__(self, update_url, thumbnail_src, *args, **kwargs):
        super(ImageEdit, self).__init__(*args, **kwargs)
        self._extra_context = {
            'update_url': update_url,
            'thumbnail_src': thumbnail_src
        }
        
    def get_context(self, *args, **kwargs):
        context = super(ImageEdit, self).get_context(*args, **kwargs)
        context.update(self._extra_context)
        return context