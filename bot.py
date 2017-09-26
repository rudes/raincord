import os
import asyncio
import logging
import discord
from discord.ext import commands

logging.basicConfig(format="%(asctime)s %(name)s:%(levelname)-8s %(message)s",
        filename="/var/log/raincord.log", level=logging.INFO)

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

class VoiceEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.songs = asyncio.Queue()
        self.play_next_song = asyncio.Event()
        self.bot = bot
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False
        return not self.current.player.is_done()

    def skip(self):
        self.current.player.stop()

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            self.current.player.start()
            await self.play_next_song.wait()

class Rain:
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def _play(self, ctx, sound):
        opts = {
                'default_search': 'auto',
                'quiet': True,
                }
        sounds = {
                'rain': 'https://www.youtube.com/watch?v=tP0zE1zXTVA',
                'ocean': 'https://www.youtube.com/watch?v=7F-F8-qHmq0',
                'fire': 'https://www.youtube.com/watch?v=L_LUpnjgPso',
                'city': 'https://www.youtube.com/watch?v=cDWZkXjDYsc',
                'jungle': 'https://www.youtube.com/watch?v=bv7ogWz7zGQ',
                }
        chan = ctx.message.author.voice_channel
        if chan is None:
            await self.bot.delete_message(ctx.message)
            await self.bot.say('You are not in a voice channel.')
            return False
        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(chan)
        else:
            await state.voice.move_to(chan)

        if state.is_playing():
            state.skip()

        try:
            player = await state.voice.create_ytdl_player(sounds[sound],
                    ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            await self.bot.send_message(ctx.message.channel,
                    "Unable to play {}: {}: {}".format(sound, type(e).__name__, e))
        else:
            player.volume = 0.6
            entry = VoiceEntry(ctx.message, player)
            await state.songs.put(entry)
        await self.bot.delete_message(ctx.message)
        logging.info('play,{0.author.name},playing {1} in {0.server.name}'.format(ctx.message,
            sound))

    @commands.command(pass_context=True, no_pm=True)
    async def rain(self, ctx):
        """Join the curent channel and start playing rain sounds."""
        await self._play(ctx, 'rain')

    @commands.command(pass_context=True, no_pm=True)
    async def ocean(self, ctx):
        """Join the curent channel and start playing ocean sounds."""
        await self._play(ctx, 'ocean')

    @commands.command(pass_context=True, no_pm=True)
    async def city(self, ctx):
        """Join the curent channel and start playing city sounds."""
        await self._play(ctx, 'city')

    @commands.command(pass_context=True, no_pm=True)
    async def fire(self, ctx):
        """Join the curent channel and start playing fireplace sounds."""
        await self._play(ctx, 'fire')

    @commands.command(pass_context=True, no_pm=True)
    async def jungle(self, ctx):
        """Join the curent channel and start playing jungle sounds."""
        await self._play(ctx, 'jungle')

    @commands.command(pass_context=True, no_pm=True)
    async def leave(self, ctx):
        """Leave the current channel."""
        server = ctx.message.server
        state = self.get_voice_state(server)
        state.audio_player.cancel()
        del self.voice_states[server.id]
        await state.voice.disconnect()
        await self.bot.delete_message(ctx.message)
        logging.info('leave,{},{}'.format(ctx.message.author.name,
            ctx.message.server.name))

bot = commands.Bot(command_prefix=commands.when_mentioned_or('..'),
        description="Ambient Rain Sounds")
bot.add_cog(Rain(bot))

@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name="say ..help"))
    logging.info('on_ready,{},presence state set'.format(bot.user.name))

bot.run(str(os.environ['DISCORD_BOTKEY']))
