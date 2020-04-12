import os

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix = '.')

TOKEN = os.getenv("DISCORD_TOKEN")
startup_extensions = ["admin", "music"]

if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension("cogs." + extension)
            print("Loaded {} extension".format(extension))
        except Exception as e:
            print("Failed to load {} extension\n".format(extension))
            print(e) 
            print("\n")

    bot.run(TOKEN)