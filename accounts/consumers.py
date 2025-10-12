# accounts/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class MessageConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if user and getattr(user, 'is_authenticated', False):
            self.group_name = f"user_{user.id}"
        else:
            self.group_name = "broadcast"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        await self.send_json({
            "type": "echo",
            "data": content
        })

    async def payment_success(self, event):
        await self.send_json({
            "type": "payment_success",
            "data": event.get("data", {})
        })
