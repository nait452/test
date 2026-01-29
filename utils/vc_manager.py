import discord
import asyncio
import json
import aiofiles
from typing import Dict, Optional
import config
from datetime import datetime, timedelta

class VCManager:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VCManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.vc_data = {}
            self.owner_left_times = {}
    
    async def _read_data(self) -> Dict:
        try:
            async with aiofiles.open(config.VC_DATA_FILE, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
    
    async def _write_data(self, data: Dict):
        async with aiofiles.open(config.VC_DATA_FILE, 'w') as f:
            await f.write(json.dumps(data, indent=4))
    
    async def create_vc(self, channel_id: int, owner_id: int):
        async with self._lock:
            data = await self._read_data()
            data[str(channel_id)] = {
                'owner_id': owner_id,
                'trusted': [],
                'blocked': [],
                'locked': False
            }
            await self._write_data(data)
            self.vc_data[channel_id] = data[str(channel_id)]
    
    async def get_vc_data(self, channel_id: int) -> Optional[Dict]:
        if channel_id in self.vc_data:
            return self.vc_data[channel_id]
        
        async with self._lock:
            data = await self._read_data()
            vc_data = data.get(str(channel_id))
            if vc_data:
                self.vc_data[channel_id] = vc_data
            return vc_data
    
    async def delete_vc(self, channel_id: int):
        async with self._lock:
            data = await self._read_data()
            if str(channel_id) in data:
                del data[str(channel_id)]
                await self._write_data(data)
            if channel_id in self.vc_data:
                del self.vc_data[channel_id]
            if channel_id in self.owner_left_times:
                del self.owner_left_times[channel_id]
    
    async def update_vc_owner(self, channel_id: int, new_owner_id: int):
        async with self._lock:
            data = await self._read_data()
            if str(channel_id) in data:
                data[str(channel_id)]['owner_id'] = new_owner_id
                await self._write_data(data)
                if channel_id in self.vc_data:
                    self.vc_data[channel_id]['owner_id'] = new_owner_id
    
    async def toggle_lock(self, channel_id: int) -> bool:
        async with self._lock:
            data = await self._read_data()
            if str(channel_id) in data:
                data[str(channel_id)]['locked'] = not data[str(channel_id)]['locked']
                await self._write_data(data)
                if channel_id in self.vc_data:
                    self.vc_data[channel_id]['locked'] = data[str(channel_id)]['locked']
                return data[str(channel_id)]['locked']
            return False
    
    async def add_trusted(self, channel_id: int, user_id: int):
        async with self._lock:
            data = await self._read_data()
            if str(channel_id) in data:
                if user_id not in data[str(channel_id)]['trusted']:
                    data[str(channel_id)]['trusted'].append(user_id)
                    await self._write_data(data)
                    if channel_id in self.vc_data:
                        self.vc_data[channel_id]['trusted'] = data[str(channel_id)]['trusted']
    
    async def remove_trusted(self, channel_id: int, user_id: int):
        async with self._lock:
            data = await self._read_data()
            if str(channel_id) in data and user_id in data[str(channel_id)]['trusted']:
                data[str(channel_id)]['trusted'].remove(user_id)
                await self._write_data(data)
                if channel_id in self.vc_data:
                    self.vc_data[channel_id]['trusted'] = data[str(channel_id)]['trusted']
    
    async def add_blocked(self, channel_id: int, user_id: int):
        async with self._lock:
            data = await self._read_data()
            if str(channel_id) in data:
                if user_id not in data[str(channel_id)]['blocked']:
                    data[str(channel_id)]['blocked'].append(user_id)
                    await self._write_data(data)
                    if channel_id in self.vc_data:
                        self.vc_data[channel_id]['blocked'] = data[str(channel_id)]['blocked']
    
    async def remove_blocked(self, channel_id: int, user_id: int):
        async with self._lock:
            data = await self._read_data()
            if str(channel_id) in data and user_id in data[str(channel_id)]['blocked']:
                data[str(channel_id)]['blocked'].remove(user_id)
                await self._write_data(data)
                if channel_id in self.vc_data:
                    self.vc_data[channel_id]['blocked'] = data[str(channel_id)]['blocked']
    
    def set_owner_left_time(self, channel_id: int):
        self.owner_left_times[channel_id] = datetime.utcnow()
    
    def clear_owner_left_time(self, channel_id: int):
        if channel_id in self.owner_left_times:
            del self.owner_left_times[channel_id]
    
    def can_claim(self, channel_id: int) -> bool:
        if channel_id not in self.owner_left_times:
            return False
        
        time_left = datetime.utcnow() - self.owner_left_times[channel_id]
        return time_left >= timedelta(seconds=30)
