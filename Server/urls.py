from django.contrib import admin
from django.urls import path
from django.urls import include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/account/', include('accounts.urls')),
    path('api/home/', include('home.urls')),
    path('api/product/', include('product.urls')),
    path('api/payments/', include('payments.urls'))
]
