from discord.ext import commands
import shutil #For deleting folders
import os

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def remove_audio_cache(self):
        if os.path.isdir("audio_cache"):
            shutil.rmtree("audio_cache")
            print("Removed audio_cache")
        else:
            print("No audio_cache exists")

    @commands.Cog.listener()
    async def on_ready(self):
        print('spotiboti is online')

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.remove_audio_cache()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id == 536994001019076627 and after.channel == None:
            self.remove_audio_cache()


def setup(bot):
    bot.add_cog(Events(bot))