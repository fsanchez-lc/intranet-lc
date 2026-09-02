import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RegataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'sala_regata_principal'

        # Unir al usuario a la sala del juego
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Sacar al usuario de la sala si cierra la pestaña
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Recibir un mensaje desde el navegador del usuario (ej. hizo clic)
    async def receive(self, text_data):
        datos = json.loads(text_data)
        
        # Ignorar mensajes de ping mantenendores de conexión
        if datos.get('tipo') == 'ping':
            return

        buque_id = datos.get('buque_id')
        if buque_id:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'movimiento_buque',
                    'buque_id': buque_id,
                }
            )

    # Función que envía físicamente el aviso a los navegadores
    async def movimiento_buque(self, event):
        buque_id = event['buque_id']
        await self.send(text_data=json.dumps({
            'accion': 'mover',
            'buque_id': buque_id
        }))