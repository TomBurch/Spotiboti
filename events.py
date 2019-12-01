from discord.ext import commands
import shutil #For deleting folders

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('spotiboti is online')

    @commands.Cog.listener()
    async def on_message(self, msg):
        author = msg.author
        content = msg.content
        print('{}: {}'.format(author, content))
        #await self.bot.process_commands(msg)

    @commands.Cog.listener()
    async def on_disconnect(self):
        shutil.rmtree("audio_cache")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id == 536994001019076627 and after.channel == None:
            shutil.rmtree("audio_cache")


def setup(bot):
    bot.add_cog(Events(bot))