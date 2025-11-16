from django.urls import path
from .create_new_product.views import CreateProduct
from .get_category.views import GetCategory
from .get_product.views import GetProduct
from .delete_product.views import DeleteProductView
from .update_product.views import UpdateProductView
from .bulk_create.views import BulkCreateProducts

urlpatterns = [
    path('create/', CreateProduct.as_view()),
    path('categories/', GetCategory.as_view()),
    path('products/', GetProduct.as_view()),
    path('delete/<str:bar_code>/', DeleteProductView.as_view()),
    path('update/', UpdateProductView.as_view()),
    path('bulk-create/', BulkCreateProducts.as_view(), name='bulk-create-products'),
]
