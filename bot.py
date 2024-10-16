import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from keep_alive import keep_alive
keep_alive()

intents=discord.Intents.all()

load_dotenv()

bot=commands.Bot(command_prefix='a!', intents=intents)

@bot.event
async def on_ready():
    await bot.sync_commands()
    print('Bot is online!')

@bot.command()
async def load(ctx, extension):
    bot.load_extension(f"cmds.{extension}")
    await ctx.send(f'已載入 {extension}')

@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f"cmds.{extension}")
    await ctx.send(f'已取消載入 {extension}')

@bot.command()
async def reload(ctx, extension):
    bot.reload_extension(f"cmds.{extension}")
    await ctx.send(f'已重新載入 {extension}')

for filename in os.listdir('./cmds'):
    if filename.endswith('.py'):
        bot.load_extension(f"cmds.{filename[:-3]}")

if __name__ == '__main__':
    bot.run(os.environ.get('token'))
