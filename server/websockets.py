# app/websockets.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from typing import List
import uuid

router = APIRouter()

active_connections: dict[str, WebSocket] = {}
async def connect(websocket: WebSocket, socket_id: str):
    print(f"New WebSocket connection: {socket_id}")
    await websocket.accept()
    active_connections[socket_id]=websocket

def disconnect(websocket: WebSocket):
    for socket_id, connection in active_connections.items():
        if connection == websocket:
            del active_connections[socket_id]
            break

async def broadcast(message: dict):
    print(f"Active connections: {len(active_connections)}", active_connections)
    for connection in active_connections.values():
        print("connection:", connection)
        await connection.send_json(message)

async def send_to_client(client_id: str, message: dict):
    websocket = active_connections.get(client_id)
    print("websocket:", websocket)
    if websocket:
        await websocket.send_json(message)

@router.websocket("/ws/client")
async def websocket_endpoint(websocket: WebSocket, client_id: str = Query(default=None)):
    if not client_id:
        client_id = str(uuid.uuid4())
    await connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("data")

            if event == "purge":
                # handle purge action
                print(f"Purging ad: {payload}")
                # await broadcast({"type": "purge_ack", "data": payload})
                await send_to_client(client_id, {"type": "purge_back", "data": payload})

            elif event == "heartbeat":
                print("Got heartbeat")
                await websocket.send_json({"type": "heartbeat_ack"})
            
            # you can add more event handlers here
    except WebSocketDisconnect:
        disconnect(websocket)
