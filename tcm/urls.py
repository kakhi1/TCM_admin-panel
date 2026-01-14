from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.contrib import admin
from django.views.generic import RedirectView
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
