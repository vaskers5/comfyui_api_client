import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import os

def open_websocket_connection():
  server_address=os.getenv('COMFYUI_SERVER_ADDRESS', '127.0.0.1:8188')
  print(server_address)
  client_id=str(uuid.uuid4())

  ws = websocket.WebSocket()
  ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
  return ws, server_address, client_id