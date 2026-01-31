import json
import aiofiles
import asyncio
from typing import Any, Dict, Optional
import config

class ConfigManager:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
    
    async def _read_json(self, filepath: str) -> Dict:
        try:
            async with aiofiles.open(filepath, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
    
    async def _write_json(self, filepath: str, data: Dict):
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(json.dumps(data, indent=4))
    
    async def get_guild_config(self, guild_id: int) -> Dict:
        async with self._lock:
            data = await self._read_json(config.CONFIG_FILE)
            return data.get(str(guild_id), {})
    
    async def set_guild_config(self, guild_id: int, key: str, value: Any):
        async with self._lock:
            data = await self._read_json(config.CONFIG_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {}
            data[str(guild_id)][key] = value
            await self._write_json(config.CONFIG_FILE, data)
    
    async def get_log_channel(self, guild_id: int, log_type: str) -> Optional[int]:
        guild_config = await self.get_guild_config(guild_id)
        return guild_config.get('log_channels', {}).get(log_type)
    
    async def set_log_channel(self, guild_id: int, log_type: str, channel_id: int):
        async with self._lock:
            data = await self._read_json(config.CONFIG_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {}
            if 'log_channels' not in data[str(guild_id)]:
                data[str(guild_id)]['log_channels'] = {}
            data[str(guild_id)]['log_channels'][log_type] = channel_id
            await self._write_json(config.CONFIG_FILE, data)
    
    async def get_hardbans(self, guild_id: int) -> Dict:
        async with self._lock:
            data = await self._read_json(config.HARDBANS_FILE)
            return data.get(str(guild_id), {})
    
    async def add_hardban(self, guild_id: int, user_id: int, reason: str, banned_by: int):
        async with self._lock:
            data = await self._read_json(config.HARDBANS_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {}
            data[str(guild_id)][str(user_id)] = {
                'reason': reason,
                'banned_by': banned_by
            }
            await self._write_json(config.HARDBANS_FILE, data)
    
    async def remove_hardban(self, guild_id: int, user_id: int) -> bool:
        async with self._lock:
            data = await self._read_json(config.HARDBANS_FILE)
            if str(guild_id) in data and str(user_id) in data[str(guild_id)]:
                del data[str(guild_id)][str(user_id)]
                await self._write_json(config.HARDBANS_FILE, data)
                return True
            return False
    
    async def get_fake_perms(self, guild_id: int) -> Dict:
        async with self._lock:
            data = await self._read_json(config.FAKE_PERMS_FILE)
            return data.get(str(guild_id), {'users': {}, 'roles': {}})
    
    async def add_fake_perm(self, guild_id: int, target_id: int, target_type: str, perms: list):
        async with self._lock:
            data = await self._read_json(config.FAKE_PERMS_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {'users': {}, 'roles': {}}
            if target_type not in data[str(guild_id)]:
                data[str(guild_id)][target_type] = {}
            
            if str(target_id) not in data[str(guild_id)][target_type]:
                data[str(guild_id)][target_type][str(target_id)] = []
            
            for perm in perms:
                if perm not in data[str(guild_id)][target_type][str(target_id)]:
                    data[str(guild_id)][target_type][str(target_id)].append(perm)
            
            await self._write_json(config.FAKE_PERMS_FILE, data)
    
    async def remove_fake_perm(self, guild_id: int, target_id: int, target_type: str, perms: list):
        async with self._lock:
            data = await self._read_json(config.FAKE_PERMS_FILE)
            if str(guild_id) in data and target_type in data[str(guild_id)] and str(target_id) in data[str(guild_id)][target_type]:
                for perm in perms:
                    if perm in data[str(guild_id)][target_type][str(target_id)]:
                        data[str(guild_id)][target_type][str(target_id)].remove(perm)
                await self._write_json(config.FAKE_PERMS_FILE, data)
    
    async def get_roleplay_gifs(self, guild_id: int) -> Dict:
        async with self._lock:
            data = await self._read_json(config.ROLEPLAY_GIFS_FILE)
            return data.get(str(guild_id), {})
    
    async def set_roleplay_gif(self, guild_id: int, command: str, url: str):
        async with self._lock:
            data = await self._read_json(config.ROLEPLAY_GIFS_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {}
            data[str(guild_id)][command] = url
            await self._write_json(config.ROLEPLAY_GIFS_FILE, data)
    
    async def get_antinuke_whitelist(self, guild_id: int) -> Dict:
        async with self._lock:
            data = await self._read_json(config.ANTINUKE_DATA_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {'whitelist': {'users': [], 'roles': []}, 'thresholds': {}}
            return data.get(str(guild_id), {}).get('whitelist', {'users': [], 'roles': []})
    
    async def add_antinuke_whitelist(self, guild_id: int, target_id: int, target_type: str):
        async with self._lock:
            data = await self._read_json(config.ANTINUKE_DATA_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {'whitelist': {'users': [], 'roles': []}, 'thresholds': {}}
            if 'whitelist' not in data[str(guild_id)]:
                data[str(guild_id)]['whitelist'] = {'users': [], 'roles': []}
            
            if target_id not in data[str(guild_id)]['whitelist'][target_type]:
                data[str(guild_id)]['whitelist'][target_type].append(target_id)
            
            await self._write_json(config.ANTINUKE_DATA_FILE, data)
    
    async def remove_antinuke_whitelist(self, guild_id: int, target_id: int, target_type: str):
        async with self._lock:
            data = await self._read_json(config.ANTINUKE_DATA_FILE)
            if str(guild_id) in data and 'whitelist' in data[str(guild_id)]:
                if target_id in data[str(guild_id)]['whitelist'][target_type]:
                    data[str(guild_id)]['whitelist'][target_type].remove(target_id)
                await self._write_json(config.ANTINUKE_DATA_FILE, data)
    
    async def get_antinuke_thresholds(self, guild_id: int) -> Dict:
        async with self._lock:
            data = await self._read_json(config.ANTINUKE_DATA_FILE)
            if str(guild_id) not in data:
                return {}
            return data[str(guild_id)].get('thresholds', {})
    
    async def set_antinuke_threshold(self, guild_id: int, action: str, count: int, hours: int):
        async with self._lock:
            data = await self._read_json(config.ANTINUKE_DATA_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {'whitelist': {'users': [], 'roles': []}, 'thresholds': {}}
            if 'thresholds' not in data[str(guild_id)]:
                data[str(guild_id)]['thresholds'] = {}
            
            data[str(guild_id)]['thresholds'][action] = {'count': count, 'hours': hours}
            await self._write_json(config.ANTINUKE_DATA_FILE, data)
    
    async def get_hardban_perms(self, guild_id: int) -> Dict:
        guild_config = await self.get_guild_config(guild_id)
        return guild_config.get('hardban_perms', {'users': [], 'roles': []})
    
    async def add_hardban_perm(self, guild_id: int, target_id: int, target_type: str):
        async with self._lock:
            data = await self._read_json(config.CONFIG_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {}
            if 'hardban_perms' not in data[str(guild_id)]:
                data[str(guild_id)]['hardban_perms'] = {'users': [], 'roles': []}
            
            if str(target_id) not in data[str(guild_id)]['hardban_perms'][target_type]:
                data[str(guild_id)]['hardban_perms'][target_type].append(str(target_id))
            
            await self._write_json(config.CONFIG_FILE, data)
    
    async def remove_hardban_perm(self, guild_id: int, target_id: int, target_type: str):
        async with self._lock:
            data = await self._read_json(config.CONFIG_FILE)
            if str(guild_id) in data and 'hardban_perms' in data[str(guild_id)]:
                if str(target_id) in data[str(guild_id)]['hardban_perms'][target_type]:
                    data[str(guild_id)]['hardban_perms'][target_type].remove(str(target_id))
                await self._write_json(config.CONFIG_FILE, data)
    
    async def get_antinuke_action(self, guild_id: int) -> str:
        async with self._lock:
            data = await self._read_json(config.ANTINUKE_DATA_FILE)
            if str(guild_id) not in data:
                return 'jail'
            return data[str(guild_id)].get('default_action', 'jail')
    
    async def set_antinuke_action(self, guild_id: int, action: str):
        async with self._lock:
            data = await self._read_json(config.ANTINUKE_DATA_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {'whitelist': {'users': [], 'roles': []}, 'thresholds': {}}
            data[str(guild_id)]['default_action'] = action
            await self._write_json(config.ANTINUKE_DATA_FILE, data)
    
    async def add_antinuke_history(self, guild_id: int, action_data: Dict):
        async with self._lock:
            data = await self._read_json(config.ANTINUKE_DATA_FILE)
            if str(guild_id) not in data:
                data[str(guild_id)] = {'whitelist': {'users': [], 'roles': []}, 'thresholds': {}, 'action_history': []}
            if 'action_history' not in data[str(guild_id)]:
                data[str(guild_id)]['action_history'] = []
            
            data[str(guild_id)]['action_history'].append(action_data)
            
            if len(data[str(guild_id)]['action_history']) > 50:
                data[str(guild_id)]['action_history'] = data[str(guild_id)]['action_history'][-50:]
            
            await self._write_json(config.ANTINUKE_DATA_FILE, data)
    
    async def get_antinuke_history(self, guild_id: int, limit: int = 10) -> list:
        async with self._lock:
            data = await self._read_json(config.ANTINUKE_DATA_FILE)
            if str(guild_id) not in data or 'action_history' not in data[str(guild_id)]:
                return []
            return data[str(guild_id)]['action_history'][-limit:]
