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
        self.stopped = False
        self.server = None
        self.settings = {}
        self.data = {}
        self.queue = []

    #===Commands===#
  
    @commands.command()
    async def join(self, ctx):
        """Connects the bot to your voice channel"""

        self.server = ctx.message.guild
        self.settings = {'shuffle' : False}
        self.data = {'prev_message' : None,
                     'text_channel' : None,
                     'voice_channel' : None,
                     'voice_client' : None}

        self.data['text_channel'] = ctx.channel
        self.data['voice_channel'] = ctx.message.author.voice.channel
        self.data['voice_client'] = await self.data['voice_channel'].connect()
        self.data['prev_message'] = await self.send_message("Spotiboti is online")
        
    @commands.command()
    async def leave(self, ctx):
        """Disconnects the bot from voice channel"""

        voice_client = self.data['voice_client']
        await voice_client.disconnect()

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song"""

        voice_client = self.data['voice_client']

        if voice_client.is_playing():
           voice_client.pause()
        else:
            await self.send_message("No song playing")

    @commands.command()
    async def resume(self, ctx):
        """Resumes the current song"""

        voice_client = self.data['voice_client']

        if voice_client.is_paused():
            voice_client.resume()
        else:
            await self.send_message("No song paused")

    @commands.command()
    async def skip(self, ctx):
        """Skip the current song"""

        voice_client = self.data['voice_client']

        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        else:
            await self.send_message("No current song")

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume from 0-200"""

        voice_client = self.data['voice_client']

        async with ctx.typing():
            voice_client.source.volume = volume / 100
            await self.send_message("Changed volume to {}%".format(volume))

    @commands.command()
    async def shuffle(self, ctx):
        """Turn shuffle on/off"""

        currentSetting = self.settings['shuffle']
        self.settings['shuffle'] = not currentSetting

        if self.settings['shuffle'] == True:
            await self.send_message('Shuffle turned on')
        else:
            await self.send_message('Shuffle turned off')

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
    async def playlist(self, ctx, plQuery: str):
        """Queues up a spotify playlist"""

        #Convert discord name to spotify name
        author = str(ctx.message.author)
        if author in usernames:
            username = usernames[author]
        else:
            await self.send_message('Username not found')
            return
            
        playlist_id = None
        if plQuery.startswith('https://open.spotify.com/playlist/'):
            playlist_id = plQuery[34:56]
        else:       
            playlist_id = self.find_playlist_id(username, plQuery)

        if not playlist_id: 
            await self.send_message('Playlist not found')
            return
        
        await self.send_message('Retrieving playlist')
        self.queue = getPlaylistFromId(playlist_id, client_credentials_manager.get_access_token())

        await self.update_queue()

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

    async def send_message(self, message: str, overwrite: bool = False, immutable: bool = True):
        """Send a message to the text channel"""

        text_channel = self.data['text_channel']
        prev_message = self.data['prev_message']
        newMessage = None

        if overwrite and (text_channel.last_message_id == prev_message.id):
            await prev_message.edit(content = message)         
            newMessage = prev_message
        else:
            await text_channel.trigger_typing()
            newMessage = await text_channel.send(message)
        
        if not immutable:
            self.data['prev_message'] = newMessage

        return newMessage

    async def update_queue(self):
        shuffled = self.settings['shuffle']
        voice_client = self.data['voice_client']

        if self.stopped == True:
            self.stopped = False    
        else:
            if self.queue != []:
                player = None
                try:
                    popInt = random.randint(0, len(self.queue)) if shuffled else 0
                    song = self.queue.pop(popInt)
                    print('Downloading: ' + song)
                    await self.send_message('Downloading: ' + song, overwrite = True, immutable = False)
                    player, filename = await YTDLSource.from_name(song, loop = self.bot.loop)
                except Exception as e:
                    print(e)

                if player:
                    await self.send_message('Now playing: ' + song, overwrite = True, immutable = False)
                    voice_client.play(player, after = lambda e: asyncio.run_coroutine_threadsafe(self.update_queue(), voice_client.loop))
                else:
                    print("No player")
            else:
                print('Queue empty')

    #===Listeners===#

    @commands.Cog.listener()
    async def on_ready(self):
        print('spotiboti is online')

        if self.queue != []:
            print("Resuming songs")
            self.data['voice_client'] = await self.data['voice_channel'].connect()
            await self.update_queue()


def setup(bot):
    bot.add_cog(Music(bot))