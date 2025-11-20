"""
Inventory Management Service
Centralized service for managing all inventory transactions
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import time

from core.models import Product, InventoryTransaction


class InventoryService:
    """
    Service để quản lý tồn kho tập trung
    - Track tất cả biến động kho
    - Đảm bảo data consistency
    - Audit trail đầy đủ
    """

    @staticmethod
    def generate_transaction_code(transaction_type):
        """Generate unique transaction code"""
        timestamp = int(time.time() * 1000)
        prefix = {
            'import': 'IMP',
            'export': 'EXP',
            'adjustment': 'ADJ',
            'return': 'RET',
            'damage': 'DMG',
            'lost': 'LOST'
        }.get(transaction_type, 'TXN')
        return f"{prefix}{timestamp}"

    @staticmethod
    @transaction.atomic
    def create_transaction(product, transaction_type, quantity, unit_price, reference_type=None, reference_id=None, note=None, user=None):
        """
        Generic method to create any type of inventory transaction
        """
        try:
            # Route to specific method based on transaction_type
            if transaction_type == 'import':
                return InventoryService.import_stock(
                    product_id=product.id if hasattr(product, 'id') else product,
                    quantity=quantity,
                    unit_price=unit_price,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    note=note,
                    created_by=user
                )
            elif transaction_type == 'export':
                return InventoryService.export_stock(
                    product_id=product.id if hasattr(product, 'id') else product,
                    quantity=quantity,
                    unit_price=unit_price,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    note=note,
                    created_by=user
                )
            elif transaction_type == 'adjustment':
                # For adjustment, quantity is the difference, so need current + diff
                if hasattr(product, 'stock_quantity'):
                    new_quantity = product.stock_quantity + quantity
                else:
                    prod = Product.objects.get(id=product)
                    new_quantity = prod.stock_quantity + quantity
                return InventoryService.adjust_stock(
                    product_id=product.id if hasattr(product, 'id') else product,
                    new_quantity=new_quantity,
                    reason=note or 'Điều chỉnh tồn kho',
                    created_by=user
                )
            elif transaction_type == 'damage':
                return InventoryService.record_damage(
                    product_id=product.id if hasattr(product, 'id') else product,
                    quantity=abs(quantity),
                    reason=note or 'Hàng hư hỏng',
                    created_by=user
                )
            elif transaction_type == 'lost':
                return InventoryService.record_lost(
                    product_id=product.id if hasattr(product, 'id') else product,
                    quantity=abs(quantity),
                    reason=note or 'Hàng mất',
                    created_by=user
                )
            elif transaction_type == 'return':
                return InventoryService.return_stock(
                    product_id=product.id if hasattr(product, 'id') else product,
                    quantity=quantity,
                    unit_price=unit_price,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    note=note,
                    created_by=user
                )
            else:
                raise ValueError(f"Invalid transaction type: {transaction_type}")

        except Exception as e:
            raise Exception(f"Error creating inventory transaction: {str(e)}")

    @staticmethod
    @transaction.atomic
    def export_stock(product_id, quantity, unit_price, reference_type=None, reference_id=None, note=None, created_by=None):
        """
        Xuất hàng (bán hàng, xuất kho)
        """
        try:
            product = Product.objects.select_for_update().get(id=product_id)

            # Validate stock
            if product.stock_quantity < quantity:
                raise ValueError(f"Không đủ hàng trong kho. Tồn: {product.stock_quantity}, Cần: {quantity}")

            quantity_before = product.stock_quantity
            product.stock_quantity -= quantity
            quantity_after = product.stock_quantity

            # Update last sold date
            product.last_sold_date = timezone.now()
            product.save()

            # Create transaction record
            inventory_txn = InventoryTransaction.objects.create(
                transaction_code=InventoryService.generate_transaction_code('export'),
                transaction_type='export',
                product=product,
                quantity=-quantity,  # Negative for export
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                unit_price=unit_price,
                total_value=Decimal(str(quantity)) * Decimal(str(unit_price)),
                reference_type=reference_type,
                reference_id=reference_id,
                note=note or f"Xuất hàng: {product.name}",
                created_by=created_by,
                updated_by=created_by
            )

            return {
                'success': True,
                'transaction': inventory_txn,
                'product': product,
                'quantity_before': quantity_before,
                'quantity_after': quantity_after
            }

        except Product.DoesNotExist:
            raise ValueError(f"Không tìm thấy sản phẩm ID: {product_id}")
        except Exception as e:
            raise Exception(f"Lỗi xuất kho: {str(e)}")

    @staticmethod
    @transaction.atomic
    def import_stock(product_id, quantity, unit_price, reference_type=None, reference_id=None, note=None, created_by=None):
        """
        Nhập hàng vào kho
        """
        try:
            product = Product.objects.select_for_update().get(id=product_id)

            quantity_before = product.stock_quantity
            product.stock_quantity += quantity
            quantity_after = product.stock_quantity

            # Update last restock date
            product.last_restock_date = timezone.now()
            product.save()

            # Create transaction record
            inventory_txn = InventoryTransaction.objects.create(
                transaction_code=InventoryService.generate_transaction_code('import'),
                transaction_type='import',
                product=product,
                quantity=quantity,  # Positive for import
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                unit_price=unit_price,
                total_value=Decimal(str(quantity)) * Decimal(str(unit_price)),
                reference_type=reference_type,
                reference_id=reference_id,
                note=note or f"Nhập hàng: {product.name}",
                created_by=created_by,
                updated_by=created_by
            )

            return {
                'success': True,
                'transaction': inventory_txn,
                'product': product,
                'quantity_before': quantity_before,
                'quantity_after': quantity_after
            }

        except Product.DoesNotExist:
            raise ValueError(f"Không tìm thấy sản phẩm ID: {product_id}")
        except Exception as e:
            raise Exception(f"Lỗi nhập kho: {str(e)}")

    @staticmethod
    @transaction.atomic
    def adjust_stock(product_id, new_quantity, reason, created_by=None):
        """
        Điều chỉnh tồn kho (kiểm kê, sửa sai số, ...)
        """
        try:
            product = Product.objects.select_for_update().get(id=product_id)

            quantity_before = product.stock_quantity
            quantity_after = new_quantity
            quantity_diff = quantity_after - quantity_before

            product.stock_quantity = new_quantity
            product.save()

            # Create transaction record
            inventory_txn = InventoryTransaction.objects.create(
                transaction_code=InventoryService.generate_transaction_code('adjustment'),
                transaction_type='adjustment',
                product=product,
                quantity=quantity_diff,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                unit_price=product.cost_price,
                total_value=abs(Decimal(str(quantity_diff))) * product.cost_price,
                reference_type='adjustment',
                reference_id=None,
                note=reason,
                created_by=created_by,
                updated_by=created_by
            )

            return {
                'success': True,
                'transaction': inventory_txn,
                'product': product,
                'quantity_before': quantity_before,
                'quantity_after': quantity_after,
                'quantity_diff': quantity_diff
            }

        except Product.DoesNotExist:
            raise ValueError(f"Không tìm thấy sản phẩm ID: {product_id}")
        except Exception as e:
            raise Exception(f"Lỗi điều chỉnh kho: {str(e)}")

    @staticmethod
    @transaction.atomic
    def record_damage(product_id, quantity, reason, created_by=None):
        """
        Ghi nhận hàng hư hỏng
        """
        try:
            product = Product.objects.select_for_update().get(id=product_id)

            if product.stock_quantity < quantity:
                raise ValueError(f"Không đủ hàng để ghi nhận hư hỏng")

            quantity_before = product.stock_quantity
            product.stock_quantity -= quantity
            quantity_after = product.stock_quantity
            product.save()

            # Create transaction record
            inventory_txn = InventoryTransaction.objects.create(
                transaction_code=InventoryService.generate_transaction_code('damage'),
                transaction_type='damage',
                product=product,
                quantity=-quantity,  # Negative
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                unit_price=product.cost_price,
                total_value=Decimal(str(quantity)) * product.cost_price,
                reference_type='damage',
                reference_id=None,
                note=reason,
                created_by=created_by,
                updated_by=created_by
            )

            return {
                'success': True,
                'transaction': inventory_txn,
                'product': product,
                'quantity_before': quantity_before,
                'quantity_after': quantity_after
            }

        except Product.DoesNotExist:
            raise ValueError(f"Không tìm thấy sản phẩm ID: {product_id}")
        except Exception as e:
            raise Exception(f"Lỗi ghi nhận hư hỏng: {str(e)}")

    @staticmethod
    @transaction.atomic
    def record_lost(product_id, quantity, reason, created_by=None):
        """
        Ghi nhận hàng mất
        """
        try:
            product = Product.objects.select_for_update().get(id=product_id)

            if product.stock_quantity < quantity:
                raise ValueError(f"Không đủ hàng để ghi nhận mất")

            quantity_before = product.stock_quantity
            product.stock_quantity -= quantity
            quantity_after = product.stock_quantity
            product.save()

            # Create transaction record
            inventory_txn = InventoryTransaction.objects.create(
                transaction_code=InventoryService.generate_transaction_code('lost'),
                transaction_type='lost',
                product=product,
                quantity=-quantity,  # Negative
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                unit_price=product.cost_price,
                total_value=Decimal(str(quantity)) * product.cost_price,
                reference_type='lost',
                reference_id=None,
                note=reason,
                created_by=created_by,
                updated_by=created_by
            )

            return {
                'success': True,
                'transaction': inventory_txn,
                'product': product,
                'quantity_before': quantity_before,
                'quantity_after': quantity_after
            }

        except Product.DoesNotExist:
            raise ValueError(f"Không tìm thấy sản phẩm ID: {product_id}")
        except Exception as e:
            raise Exception(f"Lỗi ghi nhận mất hàng: {str(e)}")

    @staticmethod
    @transaction.atomic
    def return_stock(product_id, quantity, unit_price, reference_type=None, reference_id=None, note=None, created_by=None):
        """
        Trả hàng về kho (khách trả, trả NCC)
        """
        try:
            product = Product.objects.select_for_update().get(id=product_id)

            quantity_before = product.stock_quantity
            product.stock_quantity += quantity
            quantity_after = product.stock_quantity
            product.save()

            # Create transaction record
            inventory_txn = InventoryTransaction.objects.create(
                transaction_code=InventoryService.generate_transaction_code('return'),
                transaction_type='return',
                product=product,
                quantity=quantity,  # Positive
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                unit_price=unit_price,
                total_value=Decimal(str(quantity)) * Decimal(str(unit_price)),
                reference_type=reference_type,
                reference_id=reference_id,
                note=note or f"Trả hàng: {product.name}",
                created_by=created_by,
                updated_by=created_by
            )

            return {
                'success': True,
                'transaction': inventory_txn,
                'product': product,
                'quantity_before': quantity_before,
                'quantity_after': quantity_after
            }

        except Product.DoesNotExist:
            raise ValueError(f"Không tìm thấy sản phẩm ID: {product_id}")
        except Exception as e:
            raise Exception(f"Lỗi trả hàng: {str(e)}")

    @staticmethod
    def get_product_inventory_history(product_id, limit=50):
        """
        Lấy lịch sử biến động kho của sản phẩm
        """
        transactions = InventoryTransaction.objects.filter(
            product_id=product_id
        ).select_related('product', 'created_by').order_by('-created_at')[:limit]

        return transactions

    @staticmethod
    def get_inventory_summary(start_date=None, end_date=None):
        """
        Tổng hợp biến động kho theo khoảng thời gian
        """
        queryset = InventoryTransaction.objects.all()

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        summary = {
            'total_import': 0,
            'total_export': 0,
            'total_adjustment': 0,
            'total_damage': 0,
            'total_lost': 0,
            'total_return': 0,
        }

        for txn in queryset:
            if txn.transaction_type == 'import':
                summary['total_import'] += abs(txn.quantity)
            elif txn.transaction_type == 'export':
                summary['total_export'] += abs(txn.quantity)
            elif txn.transaction_type == 'adjustment':
                summary['total_adjustment'] += abs(txn.quantity)
            elif txn.transaction_type == 'damage':
                summary['total_damage'] += abs(txn.quantity)
            elif txn.transaction_type == 'lost':
                summary['total_lost'] += abs(txn.quantity)
            elif txn.transaction_type == 'return':
                summary['total_return'] += abs(txn.quantity)

        return summary

