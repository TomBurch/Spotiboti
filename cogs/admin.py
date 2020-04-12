from discord.ext import commands
import shutil #For deleting folders
import os

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #===Commands===#

    @commands.command(name = "reload", hidden = True)
    @commands.is_owner()
    async def _reload(self, ctx, ext: str):
        try:
            self.bot.reload_extension("cogs." + ext)
            print("Reloaded {} extension\n".format(ext))
        except Exception as e:
            print("Failed to reload {} extension\n".format(ext))
            print(e)
            print("\n")

    @commands.command(name="shutdown", hidden = True)
    @commands.is_owner()
    async def _shutdown(self, ctx):
        self.remove_audio_cache()
        await ctx.voice_client.disconnect()
        exit()

    #===Utility===#

    def remove_audio_cache(self):
        if os.path.isdir("audio_cache"):
            shutil.rmtree("audio_cache")
            print("Removed audio_cache")
        else:
            print("No audio_cache exists")

def setup(bot):
    bot.add_cog(Admin(bot))