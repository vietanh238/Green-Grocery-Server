from rest_framework import serializers


class UpdateProductSerializer(serializers.ModelSerializer):

    def validateData(data):
        error_code = 0
        name_product = data.get('productName')
        sku = data.get('sku')
        cost_price = data.get('costPrice')
        price = data.get('price')
        quantity = data.get('quantity')
        unit = data.get('unit')
        category = data.get('category')
        bar_code = data.get('sku')

        if (
            not name_product or
            not sku or
            not cost_price or
            not price or
            not quantity or
            not unit or
            not category or
            not bar_code
        ):
            error_code = 1
            return error_code

        return error_code