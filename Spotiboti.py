import os
import asyncio
from collections import namedtuple
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

Entry = namedtuple('Entry', 'client event')
bot = Entry(client = commands.Bot(command_prefix = '.'), 
            event = asyncio.Event())

TOKEN = os.getenv("DISCORD_TOKEN")
startup_extensions = ["admin", "music"]

def loadExtensions():
    for extension in startup_extensions:
        try:
            bot.client.load_extension("cogs." + extension)
            print("Loaded {} extension".format(extension))
        except Exception as e:
            print("Failed to load {} extension\n".format(extension))
            print(e) 
            print("\n")  

async def login():
    await bot.client.login(TOKEN)

async def connect():
    try:
        await bot.client.connect()
    except Exception as e:
        await bot.client.close()
        print("Failed to connect")
        print(e)
        bot.event.set()

async def checkClosed():
    futures = [bot.event.wait()]
    await asyncio.wait(futures)

if __name__ == "__main__":
    loadExtensions()
    loop = asyncio.get_event_loop()

    loop.run_until_complete(login())

    loop.create_task(connect())

    #Wait for client to close
    loop.run_until_complete(checkClosed())

    loop.close()
