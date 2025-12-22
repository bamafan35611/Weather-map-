#!/usr/bin/env python3
"""
Voice Relay Server for NorthBamaWX
Relays speech between Weather Map (OBS) and Voice Helper (Edge TTS)
"""

import asyncio
import websockets
import json
from datetime import datetime

# Connected clients
obs_clients = set()
voice_clients = set()

async def handle_client(websocket, path):
    """Handle WebSocket client connections"""
    client_role = None
    
    try:
        async for message in websocket:
            data = json.loads(message)  # FIXED: was json.parse
            
            # Handle client identification
            if data.get('type') == 'identify':
                client_role = data.get('client')
                
                if client_role == 'obs':
                    obs_clients.add(websocket)
                    await websocket.send(json.dumps({
                        'status': 'connected',
                        'role': 'obs'
                    }))
                    print(f"[{timestamp()}] ✅ OBS client connected")
                    
                elif client_role == 'voice':
                    voice_clients.add(websocket)
                    await websocket.send(json.dumps({
                        'status': 'connected',
                        'role': 'voice'
                    }))
                    print(f"[{timestamp()}] ✅ Voice client connected")
            
            # Handle speech requests from OBS -> Voice
            elif data.get('type') == 'speak':
                text = data.get('text', '')
                rate = data.get('rate', 1.0)
                voice = data.get('voice', None)
                
                print(f"[{timestamp()}] 📢 Speech request: \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
                
                # Forward to all voice clients
                for voice_client in voice_clients:
                    try:
                        await voice_client.send(json.dumps({
                            'text': text,
                            'rate': rate,
                            'voice': voice
                        }))
                    except Exception as e:
                        print(f"[{timestamp()}] ⚠️ Error sending to voice client: {e}")
            
            # Handle briefing coordination
            elif data.get('type') == 'briefing_start':
                print(f"[{timestamp()}] 📢 Briefing started")
                # Notify all OBS clients
                for obs_client in obs_clients:
                    try:
                        await obs_client.send(json.dumps({
                            'type': 'briefing_start'
                        }))
                    except Exception as e:
                        print(f"[{timestamp()}] ⚠️ Error notifying OBS client: {e}")
            
            elif data.get('type') == 'briefing_end':
                print(f"[{timestamp()}] ✓ Briefing ended")
                # Notify all OBS clients
                for obs_client in obs_clients:
                    try:
                        await obs_client.send(json.dumps({
                            'type': 'briefing_end'
                        }))
                    except Exception as e:
                        print(f"[{timestamp()}] ⚠️ Error notifying OBS client: {e}")
            
            # Handle speech completion confirmation
            elif data.get('type') == 'speech_complete':
                print(f"[{timestamp()}] ✅ Speech completed")
                # Notify all OBS clients
                for obs_client in obs_clients:
                    try:
                        await obs_client.send(json.dumps({
                            'type': 'speech_complete'
                        }))
                    except Exception as e:
                        print(f"[{timestamp()}] ⚠️ Error notifying OBS client: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        print(f"[{timestamp()}] 🔌 Client disconnected")
    except Exception as e:
        print(f"[{timestamp()}] ❌ Error: {e}")
    finally:
        # Remove from appropriate set
        if client_role == 'obs' and websocket in obs_clients:
            obs_clients.remove(websocket)
            print(f"[{timestamp()}] 👋 OBS client disconnected")
        elif client_role == 'voice' and websocket in voice_clients:
            voice_clients.remove(websocket)
            print(f"[{timestamp()}] 👋 Voice client disconnected")

def timestamp():
    """Get current timestamp for logging"""
    return datetime.now().strftime("%I:%M:%S %p")

async def main():
    """Start the WebSocket server"""
    print("=" * 60)
    print("🎙️  NorthBamaWX Voice Relay Server")
    print("=" * 60)
    print(f"[{timestamp()}] Starting WebSocket server on ws://localhost:8765")
    print(f"[{timestamp()}] Waiting for connections...")
    print()
    
    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{timestamp()}] 👋 Server stopped")
