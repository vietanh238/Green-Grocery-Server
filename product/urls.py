from django.urls import path
from .create_new_product.views import CreateProduct
from .get_category.views import GetCategory

urlpatterns = [
    path('create/', CreateProduct.as_view()),
    path('categories/', GetCategory.as_view())
]
