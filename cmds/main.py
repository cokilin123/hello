import discord
from discord.ext import commands
from core.classes import Cog_extension

class Main(Cog_extension):
    @discord.slash_command(description='輸出這機器人的邀請連結')
    async def invite(self, ctx:discord.ApplicationContext):
        await ctx.respond(content='https://discord.com/oauth2/authorize?client_id=1283301891047952424', ephemeral=True)
    
    @discord.slash_command(description='Purge some messages in the channel.')
    @discord.default_permissions(manage_channels=True)
    @discord.option('number', input_type=int, description='The number of messages you want to purge.')
    async def purge(self, ctx:discord.ApplicationContext, number):
        await ctx.respond('Deleting messages, please wait.')
        await ctx.channel.purge(limit=number+1)

def setup(bot):
    bot.add_cog(Main(bot))