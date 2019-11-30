from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def on_ready(self):
        print('spotiboti is online')

    async def on_message(self, msg):
        author = msg.author
        content = msg.content
        print('{}: {}'.format(author, content))
        await bot.process_commands(msg)

def setup(bot):
    bot.add_cog(Events(bot))