# product/urls.py
from django.urls import path
from .get_product.views import GetProductView
from .get_category.views import GetCategoryView
from .create_new_product.views import CreateProductView
from .update_product.views import UpdateProductView
from .delete_product.views import DeleteProductView
from .bulk_create.views import BulkCreateProductsView
from .get_supplier.views import GetSuppliersView, CreateSupplierView

urlpatterns = [
    path('products/', GetProductView.as_view(), name='get-products'),
    path('categories/', GetCategoryView.as_view(), name='get-categories'),
    path('create/', CreateProductView.as_view(), name='create-product'),
    path('update/', UpdateProductView.as_view(), name='update-product'),
    path('delete/<str:bar_code>/',
         DeleteProductView.as_view(), name='delete-product'),
    path('bulk-create/', BulkCreateProductsView.as_view(),
         name='bulk-create-products'),
    path('suppliers/', GetSuppliersView.as_view(), name='get-suppliers'),
    path('supplier/create/', CreateSupplierView.as_view(), name='create-supplier'),
]
