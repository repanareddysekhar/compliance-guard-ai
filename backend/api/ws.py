from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Map scan_id to list of active websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, scan_id: str):
        await websocket.accept()
        if scan_id not in self.active_connections:
            self.active_connections[scan_id] = []
        self.active_connections[scan_id].append(websocket)

    def disconnect(self, websocket: WebSocket, scan_id: str):
        if scan_id in self.active_connections:
            self.active_connections[scan_id].remove(websocket)
            if not self.active_connections[scan_id]:
                del self.active_connections[scan_id]

    async def broadcast_to_scan(self, scan_id: str, message: dict):
        print(f"Broadcasting to {scan_id}: {message}")
        if scan_id in self.active_connections:
            for connection in self.active_connections[scan_id]:
                await connection.send_text(json.dumps(message))
        else:
            print(f"No active connections for {scan_id}")

manager = ConnectionManager()

@router.websocket("/ws/scan-status")
async def websocket_endpoint(websocket: WebSocket, scan_id: str):
    await manager.connect(websocket, scan_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, scan_id)
