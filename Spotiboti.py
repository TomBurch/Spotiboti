import os
from dotenv import load_dotenv
import logging

from discord.ext import commands

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()

bot = commands.Bot(command_prefix = '.')

TOKEN = os.getenv("DISCORD_TOKEN")
startup_extensions = ["admin", "music"]

def loadExtensions():
    for extension in startup_extensions:
        try:
            bot.load_extension("cogs." + extension)
            print("Loaded {} extension".format(extension))
        except Exception as e:
            print("Failed to load {} extension\n".format(extension))
            print(e) 
            print("\n")  

if __name__ == "__main__":
    loadExtensions()

    while True:     
        bot.loop.run_until_complete(bot.start(TOKEN))
        
        print("Reconnecting")
        bot.client = commands.Bot(command_prefix = '.', loop = bot.loop)