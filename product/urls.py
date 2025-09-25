from django.urls import path
from .create_new_product.views import CreateProduct

urlpatterns = [
    path('create/', CreateProduct.as_view())
]
