import discord
from discord.ext import commands
from utils.config_manager import ConfigManager
from utils.checks import is_admin

class Roleplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = ConfigManager()
        
        self.interaction_commands = {
            'hug': '🤗', 'kiss': '💋', 'airkiss': '😘', 'pat': '👋', 'slap': '👋',
            'poke': '👉', 'cuddle': '🤗', 'holdhands': '🤝', 'highfive': '🙌',
            'bite': '😬', 'tickle': '🤭', 'brofist': '👊', 'cheers': '🥂',
            'clap': '👏', 'handhold': '🤝', 'lick': '👅', 'love': '❤️',
            'nom': '😋', 'nuzzle': '🥰', 'pinch': '🤏', 'smack': '👋',
            'sorry': '🙏', 'thumbsup': '👍', 'punch': '👊', 'rpkick': '🦵',
            'bonk': '🔨', 'stare': '👀', 'wave': '👋', 'yeet': '🚀'
        }
        
        self.emote_commands = {
            'yes': '✅', 'dance': '💃', 'run': '🏃', 'jump': '🦘', 'hide': '🙈',
            'sleep': '😴', 'eat': '🍽️', 'drink': '🥤', 'headbang': '🤘',
            'peek': '👀', 'shrug': '🤷', 'sip': '☕', 'yawn': '🥱',
            'cry': '😭', 'laugh': '😂', 'blush': '😊', 'pout': '😤',
            'smile': '😊', 'wink': '😉', 'angry': '😠', 'angrystare': '😡',
            'confused': '😕', 'facepalm': '🤦', 'happy': '😄', 'mad': '😡',
            'nervous': '😰', 'sad': '😢', 'scared': '😨', 'shy': '😳',
            'sigh': '😮‍💨', 'smug': '😏', 'surprised': '😲', 'sweat': '😅',
            'tired': '😫', 'woah': '😮', 'yay': '🎉', 'bleh': '😛',
            'celebrate': '🎊', 'cool': '😎', 'drool': '🤤', 'evillaugh': '😈',
            'nyah': '😝', 'shout': '😤', 'slowclap': '👏', 'sneeze': '🤧',
            'explode': '💥'
        }
    
    async def is_roleplay_enabled(self, guild_id: int) -> bool:
        guild_config = await self.config_manager.get_guild_config(guild_id)
        return guild_config.get('roleplay_enabled', True)
    
    async def get_roleplay_gif(self, guild_id: int, command: str) -> str:
        gifs = await self.config_manager.get_roleplay_gifs(guild_id)
        return gifs.get(command)
    
    async def send_roleplay_message(self, ctx, action: str, emoji: str, target: discord.Member = None):
        if not await self.is_roleplay_enabled(ctx.guild.id):
            await ctx.send("❌ Roleplay commands are disabled in this server")
            return
        
        gif_url = await self.get_roleplay_gif(ctx.guild.id, action)
        
        if target:
            text = f"{ctx.author.mention} {action}s {target.mention} {emoji}"
        else:
            text = f"You {action}ed yourself! {emoji} {ctx.author.mention}"
        
        if gif_url:
            embed = discord.Embed(description=text, color=discord.Color.purple())
            embed.set_image(url=gif_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(text)
    
    @commands.command(name='roleplay')
    @is_admin()
    async def roleplay_toggle(self, ctx, status: str = None):
        if not status or status.lower() not in ['on', 'off']:
            await ctx.send("❌ Usage: `.roleplay on` or `.roleplay off`")
            return
        
        enabled = status.lower() == 'on'
        await self.config_manager.set_guild_config(ctx.guild.id, 'roleplay_enabled', enabled)
        await ctx.send(f"✅ Roleplay commands {'enabled' if enabled else 'disabled'}")
    
    @commands.command(name='rolegif')
    @is_admin()
    async def set_roleplay_gif(self, ctx, command: str = None, url: str = None):
        if not command or not url:
            await ctx.send("❌ Usage: `.rolegif <command> <gif_url>`")
            return
        
        if command not in self.interaction_commands and command not in self.emote_commands:
            await ctx.send(f"❌ Invalid command. Must be a valid roleplay command.")
            return
        
        await self.config_manager.set_roleplay_gif(ctx.guild.id, command, url)
        await ctx.send(f"✅ Set GIF for `.{command}` command")
    
    @commands.command(name='hug')
    async def hug(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'hug', self.interaction_commands['hug'], member)
    
    @commands.command(name='kiss')
    async def kiss(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'kiss', self.interaction_commands['kiss'], member)
    
    @commands.command(name='airkiss')
    async def airkiss(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'airkiss', self.interaction_commands['airkiss'], member)
    
    @commands.command(name='pat')
    async def pat(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'pat', self.interaction_commands['pat'], member)
    
    @commands.command(name='slap')
    async def slap(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'slap', self.interaction_commands['slap'], member)
    
    @commands.command(name='poke')
    async def poke(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'poke', self.interaction_commands['poke'], member)
    
    @commands.command(name='cuddle')
    async def cuddle(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'cuddle', self.interaction_commands['cuddle'], member)
    
    @commands.command(name='holdhands')
    async def holdhands(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'holdhand', self.interaction_commands['holdhands'], member)
    
    @commands.command(name='highfive')
    async def highfive(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'highfive', self.interaction_commands['highfive'], member)
    
    @commands.command(name='bite')
    async def bite(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'bite', self.interaction_commands['bite'], member)
    
    @commands.command(name='tickle')
    async def tickle(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'tickle', self.interaction_commands['tickle'], member)
    
    @commands.command(name='brofist')
    async def brofist(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'brofist', self.interaction_commands['brofist'], member)
    
    @commands.command(name='cheers')
    async def cheers(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'cheer', self.interaction_commands['cheers'], member)
    
    @commands.command(name='clap')
    async def clap(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'clap', self.interaction_commands['clap'], member)
    
    @commands.command(name='handhold')
    async def handhold(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'handhold', self.interaction_commands['handhold'], member)
    
    @commands.command(name='lick')
    async def lick(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'lick', self.interaction_commands['lick'], member)
    
    @commands.command(name='love')
    async def love(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'love', self.interaction_commands['love'], member)
    
    @commands.command(name='nom')
    async def nom(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'nom', self.interaction_commands['nom'], member)
    
    @commands.command(name='nuzzle')
    async def nuzzle(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'nuzzle', self.interaction_commands['nuzzle'], member)
    
    @commands.command(name='pinch')
    async def pinch(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'pinch', self.interaction_commands['pinch'], member)
    
    @commands.command(name='smack')
    async def smack(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'smack', self.interaction_commands['smack'], member)
    
    @commands.command(name='sorry')
    async def sorry(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'apologize to', self.interaction_commands['sorry'], member)
    
    @commands.command(name='thumbsup')
    async def thumbsup(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'give a thumbs up to', self.interaction_commands['thumbsup'], member)
    
    @commands.command(name='punch')
    async def punch(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'punch', self.interaction_commands['punch'], member)
    
    @commands.command(name='rpkick')
    async def rpkick(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'kick', self.interaction_commands['rpkick'], member)
    
    @commands.command(name='bonk')
    async def bonk(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'bonk', self.interaction_commands['bonk'], member)
    
    @commands.command(name='stare')
    async def stare(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'stare at', self.interaction_commands['stare'], member)
    
    @commands.command(name='wave')
    async def wave(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'wave at', self.interaction_commands['wave'], member)
    
    @commands.command(name='yeet')
    async def yeet(self, ctx, member: discord.Member = None):
        await self.send_roleplay_message(ctx, 'yeet', self.interaction_commands['yeet'], member)
    
    @commands.command(name='yes')
    async def yes(self, ctx):
        await self.send_roleplay_message(ctx, 'say yes', self.emote_commands['yes'])
    
    @commands.command(name='dance')
    async def dance(self, ctx):
        await self.send_roleplay_message(ctx, 'dance', self.emote_commands['dance'])
    
    @commands.command(name='run')
    async def run(self, ctx):
        await self.send_roleplay_message(ctx, 'run', self.emote_commands['run'])
    
    @commands.command(name='jump')
    async def jump(self, ctx):
        await self.send_roleplay_message(ctx, 'jump', self.emote_commands['jump'])
    
    @commands.command(name='hide')
    async def hide(self, ctx):
        await self.send_roleplay_message(ctx, 'hide', self.emote_commands['hide'])
    
    @commands.command(name='sleep')
    async def sleep(self, ctx):
        await self.send_roleplay_message(ctx, 'sleep', self.emote_commands['sleep'])
    
    @commands.command(name='eat')
    async def eat(self, ctx):
        await self.send_roleplay_message(ctx, 'eat', self.emote_commands['eat'])
    
    @commands.command(name='drink')
    async def drink(self, ctx):
        await self.send_roleplay_message(ctx, 'drink', self.emote_commands['drink'])
    
    @commands.command(name='headbang')
    async def headbang(self, ctx):
        await self.send_roleplay_message(ctx, 'headbang', self.emote_commands['headbang'])
    
    @commands.command(name='peek')
    async def peek(self, ctx):
        await self.send_roleplay_message(ctx, 'peek', self.emote_commands['peek'])
    
    @commands.command(name='shrug')
    async def shrug(self, ctx):
        await self.send_roleplay_message(ctx, 'shrug', self.emote_commands['shrug'])
    
    @commands.command(name='sip')
    async def sip(self, ctx):
        await self.send_roleplay_message(ctx, 'sip', self.emote_commands['sip'])
    
    @commands.command(name='yawn')
    async def yawn(self, ctx):
        await self.send_roleplay_message(ctx, 'yawn', self.emote_commands['yawn'])
    
    @commands.command(name='cry')
    async def cry(self, ctx):
        await self.send_roleplay_message(ctx, 'cry', self.emote_commands['cry'])
    
    @commands.command(name='laugh')
    async def laugh(self, ctx):
        await self.send_roleplay_message(ctx, 'laugh', self.emote_commands['laugh'])
    
    @commands.command(name='blush')
    async def blush(self, ctx):
        await self.send_roleplay_message(ctx, 'blush', self.emote_commands['blush'])
    
    @commands.command(name='pout')
    async def pout(self, ctx):
        await self.send_roleplay_message(ctx, 'pout', self.emote_commands['pout'])
    
    @commands.command(name='smile')
    async def smile(self, ctx):
        await self.send_roleplay_message(ctx, 'smile', self.emote_commands['smile'])
    
    @commands.command(name='wink')
    async def wink(self, ctx):
        await self.send_roleplay_message(ctx, 'wink', self.emote_commands['wink'])
    
    @commands.command(name='angry')
    async def angry(self, ctx):
        await self.send_roleplay_message(ctx, 'look angry', self.emote_commands['angry'])
    
    @commands.command(name='angrystare')
    async def angrystare(self, ctx):
        await self.send_roleplay_message(ctx, 'angrily stare', self.emote_commands['angrystare'])
    
    @commands.command(name='confused')
    async def confused(self, ctx):
        await self.send_roleplay_message(ctx, 'look confused', self.emote_commands['confused'])
    
    @commands.command(name='facepalm')
    async def facepalm(self, ctx):
        await self.send_roleplay_message(ctx, 'facepalm', self.emote_commands['facepalm'])
    
    @commands.command(name='happy')
    async def happy(self, ctx):
        await self.send_roleplay_message(ctx, 'look happy', self.emote_commands['happy'])
    
    @commands.command(name='mad')
    async def mad(self, ctx):
        await self.send_roleplay_message(ctx, 'look mad', self.emote_commands['mad'])
    
    @commands.command(name='nervous')
    async def nervous(self, ctx):
        await self.send_roleplay_message(ctx, 'look nervous', self.emote_commands['nervous'])
    
    @commands.command(name='sad')
    async def sad(self, ctx):
        await self.send_roleplay_message(ctx, 'look sad', self.emote_commands['sad'])
    
    @commands.command(name='scared')
    async def scared(self, ctx):
        await self.send_roleplay_message(ctx, 'look scared', self.emote_commands['scared'])
    
    @commands.command(name='shy')
    async def shy(self, ctx):
        await self.send_roleplay_message(ctx, 'look shy', self.emote_commands['shy'])
    
    @commands.command(name='sigh')
    async def sigh(self, ctx):
        await self.send_roleplay_message(ctx, 'sigh', self.emote_commands['sigh'])
    
    @commands.command(name='smug')
    async def smug(self, ctx):
        await self.send_roleplay_message(ctx, 'look smug', self.emote_commands['smug'])
    
    @commands.command(name='surprised')
    async def surprised(self, ctx):
        await self.send_roleplay_message(ctx, 'look surprised', self.emote_commands['surprised'])
    
    @commands.command(name='sweat')
    async def sweat(self, ctx):
        await self.send_roleplay_message(ctx, 'sweat', self.emote_commands['sweat'])
    
    @commands.command(name='tired')
    async def tired(self, ctx):
        await self.send_roleplay_message(ctx, 'look tired', self.emote_commands['tired'])
    
    @commands.command(name='woah')
    async def woah(self, ctx):
        await self.send_roleplay_message(ctx, 'say woah', self.emote_commands['woah'])
    
    @commands.command(name='yay')
    async def yay(self, ctx):
        await self.send_roleplay_message(ctx, 'say yay', self.emote_commands['yay'])
    
    @commands.command(name='bleh')
    async def bleh(self, ctx):
        await self.send_roleplay_message(ctx, 'stick tongue out', self.emote_commands['bleh'])
    
    @commands.command(name='celebrate')
    async def celebrate(self, ctx):
        await self.send_roleplay_message(ctx, 'celebrate', self.emote_commands['celebrate'])
    
    @commands.command(name='cool')
    async def cool(self, ctx):
        await self.send_roleplay_message(ctx, 'look cool', self.emote_commands['cool'])
    
    @commands.command(name='drool')
    async def drool(self, ctx):
        await self.send_roleplay_message(ctx, 'drool', self.emote_commands['drool'])
    
    @commands.command(name='evillaugh')
    async def evillaugh(self, ctx):
        await self.send_roleplay_message(ctx, 'laugh evilly', self.emote_commands['evillaugh'])
    
    @commands.command(name='nyah')
    async def nyah(self, ctx):
        await self.send_roleplay_message(ctx, 'say nyah', self.emote_commands['nyah'])
    
    @commands.command(name='shout')
    async def shout(self, ctx):
        await self.send_roleplay_message(ctx, 'shout', self.emote_commands['shout'])
    
    @commands.command(name='slowclap')
    async def slowclap(self, ctx):
        await self.send_roleplay_message(ctx, 'slowly clap', self.emote_commands['slowclap'])
    
    @commands.command(name='sneeze')
    async def sneeze(self, ctx):
        await self.send_roleplay_message(ctx, 'sneeze', self.emote_commands['sneeze'])
    
    @commands.command(name='explode')
    async def explode(self, ctx):
        await self.send_roleplay_message(ctx, 'explode', self.emote_commands['explode'])

async def setup(bot):
    await bot.add_cog(Roleplay(bot))
