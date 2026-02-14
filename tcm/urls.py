from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.contrib import admin
from django.views.generic import RedirectView
# --- START FIX: Restore 'length_is' filter for Django 5.1+ ---
from django.template.defaulttags import register


@register.filter(name='length_is')
def length_is(value, arg):
    """
    Monkey patch to restore the 'length_is' filter removed in Django 5.1.
    Required for Jazzmin/Admin themes to work on newer Django versions.
    """
    try:
        return len(value) == int(arg)
    except (ValueError, TypeError):
        return ""


# --- END FIX ---
# This changes the text "Django administration" in the header (your image)
admin.site.site_header = "TCM admin"

# This changes the browser tab title
admin.site.site_title = "My Admin Portal"

# This changes the text on the index page (above the app list)
admin.site.index_title = "Welcome"

urlpatterns = [

    # 1. Add this line at the top to redirect empty path '' to '/admin/'
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    # path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.site.urls),

]
