import time
import sys
import os
from json.decoder import JSONDecodeError
import sqlite3 as sql3
import asyncio
import random
import re

import discord
from discord.ext import commands

_loop = asyncio.get_event_loop()

import youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

#Spotify variables
usernames = os.getenv("SPOTIFY_NAMES")

client_id = os.getenv("SPOTIFY_ID")
client_secret = os.getenv("SPOTIFY_SECRET")

client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

players = {}
load_queues = {}
full_queues = {}
settings = {}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
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
        print(cls)
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download = not stream))

        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data = data)



class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #def find_player(self, server):
    #    if server.id in players:
    #        player = players[server.id]
    #        print('Player = ' + str(player))
    #        return player
    #    else:
    #        return False

    #def find_queue(self, server):
    #    if server.id in queues:
    #        queue = queues[server.id]
    #        print('Queue = ' + str(queue))
    #        return queue
    #    else:
    #        return False

    #async def update_queue(self, server, voice_client, channel):
    #    if full_queues[server.id] != []:
    #        player = load_queues[server.id].pop(0)
    #        players[server.id] = player
    #        player.start()

    #        shuffled = settings[server.id]['shuffle']
    #        popInt = None
    #        while len(load_queues[server.id]) < 10:
    #            try:
    #                popInt = random.randint(0, len(full_queues[server.id])) if shuffled else 0
    #                song = full_queues[server.id].pop(popInt)
    #                print('Downloading: ' + song)
    #                player = await voice_client.create_ytdl_player(song, ytdl_options = {'default_search' : 'auto',
    #                                                                                                      'quiet' : True,
    #                                                                                                      'ignore-errors' : True},
    #                                                                                      before_options = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
    #                                                                                      after = lambda: asyncio.run_coroutine_threadsafe(update_queue(server, voice_client, channel), _loop))
    #                load_queues[server.id].append(player)
    #            except Exception as e:
    #               print(e)
    #               print('Error downloading: ' + song)
    #               await client.send_message(channel, 'Error downloading: ' + song)    
    #    else:
    #        print('Queue empty')

    @commands.command(pass_context = True)
    async def join(self, ctx):
        """Connects the bot to your voice channel"""

        server = ctx.message.author.guild
        channel = ctx.message.author.voice.channel
        settings[server.id] = {'shuffle' : False}

        await channel.connect()
        
    @commands.command(pass_context = True)
    async def leave(self, ctx):
        """Disconnects the bot from voice channel"""

        await ctx.voice_client.disconnect()

    @commands.command(pass_context = True)
    async def play(self, ctx, *, url : str):
        print(url)
        server = ctx.message.guild
        voice_channel = server.voice_client

        async with ctx.typing(): #Spotiboti is typing...
            player = await YTDLSource.from_url(url, loop = self.bot.loop)
            voice_channel.play(player, after = lambda e: print('Player error: %s' % e) if e else None)
        await ctx.send('Now playing: {}'.format(player.title))

    #@commands.command(pass_context = True)
    #async def pause(ctx):
    #    server = ctx.message.server
    #    player = find_player(server)
    #    if player:
    #        player.pause()
    #    else:
    #        await client.say('No active player')

    #@commands.command(pass_context = True)
    #async def resume(ctx):
    #    server = ctx.message.server
    #    player = find_player(server)
    #    if player:
    #        player.resume()
    #    else:
    #        await client.say('No active player')

    #@commands.command(pass_context = True)
    #async def stop(ctx):
    #    server = ctx.message.server
    #    player = find_player(server)
    #    if player:
    #        player.stop()
    #    else:
    #        await client.say('No active player')

    #@commands.command(pass_context = True)
    #async def queue(ctx):
    #    server = ctx.message.server
    #    await client.say(full_queues[server.id])

    #@commands.command(pass_context = True)
    #async def skip(ctx):
    #    server = ctx.message.server
    #    player = find_player(server)

    #    if player:
    #        player.stop()
    #    else:
    #        await client.say('No active player')

    #@commands.command(pass_context = True)
    #async def volume(ctx, v):
    #    server = ctx.message.server
    #    player = find_player(server)
    #    if player:
    #        player.volume = int(v) / 100
    #    else:
    #        await client.say('No active player')

    #@commands.command(pass_context = True)
    #async def shuffle(ctx):
    #    server = ctx.message.server
    #    settings[server.id]['shuffle'] = True
    #    await client.say('Shuffle turned on')

    #@commands.command(pass_context = True)
    #async def unshuffle(ctx):
    #    server = ctx.message.server
    #    settings[server.id]['shuffle'] = False
    #    await client.say('Shuffle turned off')

    #def find_playlist_id(username, pl):
    #    playlists = sp.user_playlists(username)
    #    print('pl: ' + pl)
    #    for playlist in playlists['items']:
    #        print(playlist['name'])
    #        if playlist['name'].lower() == pl:
    #            return playlist['id']
    #    return False

    #@commands.command(pass_context = True)
    #async def playlist(ctx, *args):
    #    " Super helpful message "
    #    author = str(ctx.message.author)
    #    server = ctx.message.server
    #    channel = ctx.message.channel
    #    voice_client = client.voice_client_in(server)
    #    pl = ' '.join(args).lower()

    #    #Convert discord name to spotify name
    #    if author in usernames:
    #        username = usernames[author]
    #    else:
    #        await client.say('Username not found')
    #        return
    
    #    #Find ID of target playlist
    #    playlist_id = find_playlist_id(username, pl)
    #    if not playlist_id: 
    #        await client.say('Playlist not found') 
    #        return

    #    #Use ID to get playlist
    #    playlist = sp.user_playlist(username, playlist_id)

    #    #Create table of songs in playlist
    #    tracks = playlist['tracks']['items']
    #    songs = []
    #    for track in tracks:
    #        track = track['track']
    #        song = '{} - {}'.format(track['artists'][0]['name'], track['name'])
    #        song = re.sub('[/]', ' ', song) # '/' in string causes http errors
    #        songs.append(song)

    #    full_queues[server.id] = songs
    #    player = find_player(server)
    #    try:
    #        if player: player.stop()
    #    except:
    #        print('No player to stop')
    #    i = 0
    #    playing = False

    #    load_queues[server.id] = []

    #    shuffled = settings[server.id]['shuffle']
    #    popInt = random.randint(0, len(full_queues[server.id])) if shuffled else 0
    #    song = full_queues[server.id].pop(popInt)

    #    player = await voice_client.create_ytdl_player(song, ytdl_options = {'default_search': 'auto',
    #                                                                         'quiet' : True,
    #                                                                         'ignore-errors' : True},
    #                                                   before_options = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", 
    #                                                   after = lambda: asyncio.run_coroutine_threadsafe(update_queue(server, voice_client, channel), _loop))
    #    load_queues[server.id].append(player)

    #    await update_queue(server, voice_client, channel)

def setup(bot):
    bot.add_cog(Music(bot))
