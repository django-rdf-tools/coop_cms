from coop_cms.coop_bar_cfg import *

def load_commands(coop_bar):
    
    coop_bar.register([
        #[django_admin, django_admin_add_article, django_admin_edit_article],
        [edit_newsletter, cancel_edit_newsletter, save_newsletter,
            change_newsletter_settings, change_newsletter_template,
            test_newsletter, schedule_newsletter],
        [cms_media_library, cms_upload_image, cms_upload_doc],
        [cms_edit],
        [cms_change_template],
        [cms_save, cms_publish, cms_cancel, cms_view],
        [log_out]
    ])
    
    coop_bar.register_header(cms_extra_js)
