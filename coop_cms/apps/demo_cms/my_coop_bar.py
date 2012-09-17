from coop_cms.coop_bar_cfg import *

def load_commands(coop_bar):

    coop_bar.register([
        #[django_admin, django_admin_edit_article],
        [edit_newsletter, cancel_edit_newsletter, save_newsletter,
            change_newsletter_settings, change_newsletter_template,
            test_newsletter, schedule_newsletter],
        [cms_edit, cms_view, cms_save, cms_cancel],
        [cms_new_article, cms_article_settings],
        [cms_publish],
        [cms_media_library, cms_upload_image, cms_upload_doc],
        [log_out]
    ])

