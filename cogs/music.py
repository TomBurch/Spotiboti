import time
import sys
import os
from json.decoder import JSONDecodeError
#import sqlite3 as sql3
import asyncio
import random
import re

import discord
from discord.ext import commands

_loop = asyncio.get_event_loop()

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

load_queues = {}
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

    @commands.command()
    async def join(self, ctx):
        """Connects the bot to your voice channel"""

        server = ctx.message.guild
        channel = ctx.message.author.voice.channel
        server_settings[server.id] = {'shuffle' : False}
        server_data[server.id] = {'ctx' : ctx}

        await channel.connect()
        
    @commands.command()
    async def leave(self, ctx):
        """Disconnects the bot from voice channel"""

        await ctx.voice_client.disconnect()

    @commands.command()
    async def play(self, ctx, *, url : str):
        """Plays the song from youtube url"""

        print(url)
        server = ctx.message.author.guild
        channel = ctx.voice_client

        async with ctx.typing(): #Spotiboti is typing...
            player = await YTDLSource.from_url(url, loop = self.bot.loop)
            channel.play(player, after = lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song"""

        channel = ctx.voice_client

        if channel.is_playing():
            channel.pause()
        else:
            await ctx.send('No song playing')

    @commands.command()
    async def resume(self, ctx):
        """Resumes the current song"""

        channel = ctx.voice_client

        if channel.is_paused():
            channel.resume()
        else:
            await ctx.send('No song paused')

    #@commands.command()
    #async def stop(self, ctx):
    #    """Stops playing music"""
    #
    #    channel = ctx.voice_client
    #    if channel.is_playing() or channel.is_paused():
    #        self.stopped = True
    #        channel.stop()
    #    else:
    #        await ctx.send("No current song")

    #@commands.command(pass_context = True)
    #async def queue(ctx):
    #    server = ctx.message.server
    #    await client.say(full_queues[server.id])

    @commands.command()
    async def skip(self, ctx):
        """Skip the current song"""

        channel = ctx.voice_client
        server = ctx.message.guild

        if channel.is_playing() or channel.is_paused():
            channel.stop()
        else:
            await ctx.send("No current song")

    @commands.command()
    async def volume(self, ctx, volume : int):
        """Changes the player's volume from 0-200"""

        channel = ctx.voice_client

        channel.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command()
    async def shuffle(self, ctx):
        """Turn shuffle on/off"""

        server = ctx.message.guild   
        currentSetting = server_settings[server.id]['shuffle']

        server_settings[server.id]['shuffle'] = not currentSetting

        if server_settings[server.id]['shuffle'] == True:
            await ctx.send('Shuffle turned on')
        else:
            await ctx.send('Shuffle turned off')

    def find_playlist_id(self, username, pl):
        """Find spotify playlist ID from name"""

        playlists = sp.user_playlists(username)
        print('pl: ' + pl)
        for playlist in playlists['items']:
            print(playlist['name'])
            if playlist['name'].lower() == pl:
                return playlist['id']
        return False

    async def update_queue(self, server, channel, ctx):
        shuffled = server_settings[server.id]['shuffle']
        popInt = None

        if self.lastPlayer != None:
            print(self.lastPlayer)
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
                    player, filename = await YTDLSource.from_name(song, loop = self.bot.loop)
                    self.lastPlayer = filename
                except Exception as e:
                    print(e)
                    print('Error downloading: ' + song) 
                if player:
                    await ctx.send('Now playing: ' + song)
                    channel.play(player, after = lambda e: asyncio.run_coroutine_threadsafe(self.update_queue(server, channel, ctx), channel.loop))
                else:
                    print("No player")
            else:
                print('Queue empty')

    @commands.command()
    async def playlist(self, ctx, plQuery : str):
        """Queues up a spotify playlist by name"""

        author = str(ctx.message.author)
        channel = ctx.voice_client
        server = ctx.message.guild   

        #Convert discord name to spotify name
        if author in usernames:
            username = usernames[author]
        else:
            return await ctx.send('Username not found')
            
        if plQuery.startswith('https://open.spotify.com/playlist/'):
            plQuery = plQuery[34:56]
            print("Playlist id = " + plQuery)
            playlist = getPlaylistFromId(plQuery, client_credentials_manager.get_access_token())
            if not playlist:
                return await ctx.send('Playlist not found')
        else:       
            #Find ID of target playlist
            playlist_id = self.find_playlist_id(username, plQuery)
            if not playlist_id: 
                return await ctx.send('Playlist not found') 
            #Use ID to get playlist
            playlist = sp.user_playlist(username, playlist_id)
            

        #Create table of songs from playlist
        tracks = playlist['tracks']['items']
        songs = []
        for track in tracks:
            track = track['track']
            song = '{} - {}'.format(track['artists'][0]['name'], track['name'])
            song = re.sub('[/]', ' ', song) # '/' in string causes http errors
            songs.append(song)

        full_queues[server.id] = songs

        await self.update_queue(server, channel, ctx)

    @commands.command(name="trace", hidden=True)
    @commands.is_owner()
    async def _trace(self, ctx):
        sp.trace_out = not sp.trace_out
        sp.trace = not sp.trace
        await ctx.send("Trace = {}".format(sp.trace))


def setup(bot):
    bot.add_cog(Music(bot))
