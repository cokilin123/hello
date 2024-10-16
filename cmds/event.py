import discord
from discord.ext import commands
from core.classes import Cog_extension
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv('googleaiKey'))
model = genai.GenerativeModel('gemini-pro')

class Event(Cog_extension):
    @commands.Cog.listener()
    async def on_application_command_error(self, ctx:discord.ApplicationContext, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.followup.send(content='Command on cooldown... please wait', ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            await ctx.followup.send(content="You don't have required permission to ude the command.", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.followup.send(content="There are some arguments missing to use the command.", ephemeral=True)
        else:
            await ctx.followup.send(error, ephemeral=True)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('Command on cooldown... please wait')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have required permission to ude the command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("There are some arguments missing to use the command.")
        else:
            await ctx.send(error)
    
    @commands.Cog.listener()
    async def on_message(self, msg:discord.Message):
        if msg.content.startswith(self.bot.user.mention):
            div = msg.content.split()
            for i in range(len(div)):
                if div[i].startswith('<@'):
                    user:discord.User = await self.bot.fetch_user(div[i][2:-1])
                    div[i] = user.name
            prompt = ' '.join(div)
            response = model.generate_content(prompt)
            await msg.channel.send(response.text)

def setup(bot):
    bot.add_cog(Event(bot))