from django.urls import path
from .create_new_product.views import CreateProduct
from .get_category.views import GetCategory
from .get_product.views import GetProduct

urlpatterns = [
    path('create/', CreateProduct.as_view()),
    path('categories/', GetCategory.as_view()),
    path('products/', GetProduct.as_view())
]
