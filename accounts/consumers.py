# accounts/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class PaymentConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Lấy user từ AuthMiddlewareStack; nếu chưa đăng nhập, dùng group broadcast
        user = self.scope.get('user')
        if user and getattr(user, 'is_authenticated', False):
            self.group_name = f"user_{user.id}"   # Group riêng cho mỗi user
        else:
            self.group_name = "broadcast"         # Group chung cho demo / khách chưa login
        print(">>> Client joined group:", self.group_name)
        # Thêm kết nối hiện tại vào group tương ứng
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Chấp nhận kết nối từ browser
        await self.accept()

    async def disconnect(self, close_code):
        # Khi client đóng, bỏ kết nối khỏi group để tránh rò rỉ
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Nếu frontend gửi tin lên (ví dụ ping), bạn có thể xử lý
        await self.send_json({
            "type": "echo",
            "data": content
        })

    # Handler nhận sự kiện từ group_send với type='payment_success'
    async def payment_success(self, event):
        # event: {"type": "payment_success", "data": {...}}
        await self.send_json({
            "type": "payment_success",
            "data": event.get("data", {})
        })
