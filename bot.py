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

    async def _play(self, ctx, state):
        opts = {
                'default_search': 'auto',
                'quiet': True,
                }
        rain_sounds = "https://www.youtube.com/watch?v=tP0zE1zXTVA"
        try:
            player = await state.voice.create_ytdl_player(rain_sounds,
                    ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            await self.bot.send_message(ctx.message.channel,
                    "Unable to play rain: {}: {}".format(type(e).__name__, e))
        else:
            player.volume = 0.6
            entry = VoiceEntry(ctx.message, player)
            await state.songs.put(entry)



    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx):
        """Join the curent channel and start playing rain."""
        chan = ctx.message.author.voice_channel
        if chan is None:
            await self.bot.say('You are not in a voice channel.')
            return False
        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(chan)
        else:
            await state.voice.move_to(chan)

        await self._play(ctx, state)

        logging.info('join,{},{}'.format(ctx.message.author.name,
            ctx.message.server.name))
        return True

    @commands.command(pass_context=True, no_pm=True)
    async def leave(self, ctx):
        """Leave the current channel."""
        server = ctx.message.server
        state = self.get_voice_state(server)
        state.audio_player.cancel()
        del self.voice_states[server.id]
        await state.voice.disconnect()
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
