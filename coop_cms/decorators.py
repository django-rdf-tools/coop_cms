# -*- coding: utf-8 -*-

from django.http import HttpResponse

def popup_redirect(view_func):
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        if response.status_code == 302:
            script = '<script>$.colorbox.close(); window.location="%s";</script>' % response['Location']
            return HttpResponse(script)
        else:
            return response
    return wrapper

def popup_close(view_func):
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        if not response:
            script = '<script>$.colorbox.close();</script>'
            response = HttpResponse(script)
        return response
    return wrapper

class HttpResponseClosePopup(HttpResponse):
    def __init__(self):
        super(HttpResponseClosePopup, self).__init__("close_popup")

class HttpResponseClosePopupAndMediaSlide(HttpResponse):
    def __init__(self):
        super(HttpResponseClosePopupAndMediaSlide, self).__init__("close_popup_and_media_slide")
