import time
import sys
import os
from json.decoder import JSONDecodeError
import asyncio
import random
import re

import discord
from discord.ext import commands

import youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from SpotiInteract.utility import getPlaylistFromId

#Spotify variables
usernames = {   'BlartzelTheCat#6761'   : 'moonfenceox', 
                'WingWolf#8597'         : 'epicwolf12', 
                'Berkano#6571'          : 'zjqmp49wss8eum0abwp8bj48w', 
                'Simba12371#6037'       : '1138992184', 
                'PigRectum#4296'        : 'ofrench560'}

client_id = os.getenv("SPOTIFY_ID")
client_secret = os.getenv("SPOTIFY_SECRET")

client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

full_queues = {}
server_settings = {}
server_data = {}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'audio_cache/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume = 0.5):
        super().__init__(source, volume)

        self.data = data
        
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop = None, stream = False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download = not stream))

        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data = data)

    @classmethod
    async def from_name(cls, name, *, loop = None, stream = False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info("ytsearch:" + name, download = not stream))

        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data = data), filename



class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lastPlayer = None
        self.stopped = False
        self.server = None

    #===Commands===#
  
    @commands.command()
    async def join(self, ctx):
        """Connects the bot to your voice channel"""

        self.server = ctx.message.guild
        channel = ctx.message.author.voice.channel
        server_settings[self.server.id] = {'shuffle' : False}
        server_data[self.server.id] = {'ctx' : ctx,
                                  'playing_message' : None}

        await channel.connect()
        message = await self.send_message(self.server, "Spotiboti is online")
        server_data[self.server.id]['playing_message'] = message 
        
    @commands.command()
    async def leave(self, ctx):
        """Disconnects the bot from voice channel"""

        await ctx.voice_client.disconnect()

#    @commands.command()
#    async def play(self, ctx, *, url: str):
#        """Plays the song from youtube url"""
#
#        print(url)
#        server = ctx.message.author.guild
#        channel = ctx.voice_client
#
#        player = await YTDLSource.from_url(url, loop = self.bot.loop)
#        channel.play(player, after = lambda e: print('Player error: %s' % e) if e else None)
#
#        await self.send_message(server, 'Now playing: {}'.format(player.title))

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song"""

        channel = ctx.voice_client

        if channel.is_playing():
            channel.pause()
        else:
            await self.send_message(server, 'No song playing')

    @commands.command()
    async def resume(self, ctx):
        """Resumes the current song"""

        channel = ctx.voice_client

        if channel.is_paused():
            channel.resume()
        else:
            await self.send_message(server, 'No song paused')

    @commands.command()
    async def skip(self, ctx):
        """Skip the current song"""

        channel = ctx.voice_client
        server = ctx.message.guild

        if channel.is_playing() or channel.is_paused():
            channel.stop()
        else:
            await self.send_message(server, "No current song")

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume from 0-200"""

        channel = ctx.voice_client

        async with ctx.typing():
            channel.source.volume = volume / 100
            await self.send_message(server, "Changed volume to {}%".format(volume))

    @commands.command()
    async def shuffle(self, ctx):
        """Turn shuffle on/off"""

        server = ctx.message.guild   
        currentSetting = server_settings[server.id]['shuffle']

        server_settings[server.id]['shuffle'] = not currentSetting
        if server_settings[server.id]['shuffle'] == True:
            await self.send_message(server, 'Shuffle turned on')
        else:
            await self.send_message(server, 'Shuffle turned off')

    @commands.command()
    async def playlist(self, ctx, plQuery: str):
        """Queues up a spotify playlist by name"""

        channel = ctx.voice_client
        server = ctx.message.guild   
        author = str(ctx.message.author)

        #Convert discord name to spotify name
        if author in usernames:
            username = usernames[author]
        else:
            await self.send_message(server, 'Username not found')
            return
            
        playlist_id = None
        if plQuery.startswith('https://open.spotify.com/playlist/'):
            playlist_id = plQuery[34:56]
        else:       
            playlist_id = self.find_playlist_id(username, plQuery)

        if not playlist_id: 
            await self.send_message(server, 'Playlist not found')
            return
            
        full_queues[server.id] = getPlaylistFromId(playlist_id, client_credentials_manager.get_access_token())

        await self.update_queue(server)

    @commands.command(name="trace", hidden=True)
    @commands.is_owner()
    async def _trace(self, ctx):
        sp.trace_out = not sp.trace_out
        sp.trace = not sp.trace
        await self.send_message(server, "Trace = {}".format(sp.trace))

    #===Utility===#
   
    def find_playlist_id(self, username, pl):
        """Find spotify playlist ID from name"""

        playlists = sp.user_playlists(username)
        print('pl: ' + pl)
        for playlist in playlists['items']:
            print(playlist['name'])
            if playlist['name'].lower() == pl:
                return playlist['id']
        return False

    async def send_message(self, server, message: str, overwrite: bool = False):
        """Send a message to the text channel"""

        ctx = server_data[server.id]['ctx']
        channel = ctx.channel
        playing_message = server_data[server.id]['playing_message']
        lastMessage = channel.last_message_id

        if overwrite:
            if lastMessage == playing_message.id:
                await playing_message.edit(content = message)         
                return playing_message    
        await ctx.trigger_typing()
        return await ctx.send(message)

    async def update_queue(self, server):
        shuffled = server_settings[server.id]['shuffle']
        ctx = server_data[server.id]['ctx']

        text_channel = ctx.channel
        voice_channel = ctx.voice_client

        popInt = None

        if self.lastPlayer != None:
            #print(self.lastPlayer)
            os.unlink(self.lastPlayer)
            self.lastPlayer = None

        if self.stopped == True:
            self.stopped = False    
        else:
            if full_queues[server.id] != []:
                player = None
                try:
                    popInt = random.randint(0, len(full_queues[server.id])) if shuffled else 0
                    song = full_queues[server.id].pop(popInt)
                    print('Downloading: ' + song)
                    message = await self.send_message(server, 'Downloading: ' + song, overwrite = True)
                    server_data[server.id]['playing_message'] = message
                    player, filename = await YTDLSource.from_name(song, loop = self.bot.loop)
                    self.lastPlayer = filename
                except Exception as e:
                    print(e)
                if player:
                    message = await self.send_message(server, 'Now playing: ' + song, overwrite = True)
                    server_data[server.id]['playing_message'] = message
                    voice_channel.play(player, after = lambda e: asyncio.run_coroutine_threadsafe(self.update_queue(server), voice_channel.loop))
                else:
                    print("No player")
            else:
                print('Queue empty')

    #===Listeners===#

    @commands.Cog.listener()
    async def on_ready(self):
        print('spotiboti is online')
        if full_queues != {}:
            print("Resuming songs")
            await self.update_queue(self.server)


def setup(bot):
    bot.add_cog(Music(bot))
