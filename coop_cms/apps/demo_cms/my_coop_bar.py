from coop_cms.coop_bar_cfg import *

def load_commands(coop_bar):
    #coop_bar.register_command(django_admin)
    #coop_bar.register_command(django_admin_add_article)
    #coop_bar.register_command(django_admin_edit_article)
    #coop_bar.register_separator()
    coop_bar.register_command(cms_media_library)
    coop_bar.register_command(cms_upload_image)
    coop_bar.register_command(cms_upload_doc)
    coop_bar.register_separator()
    coop_bar.register_command(cms_edit)
    coop_bar.register_separator()
    coop_bar.register_command(cms_change_template)
    coop_bar.register_separator()
    coop_bar.register_command(cms_save)
    coop_bar.register_command(cms_publish)
    coop_bar.register_command(cms_cancel)
    coop_bar.register_separator()
    coop_bar.register_command(log_out)
    
    coop_bar.register_header(cms_extra_js)
