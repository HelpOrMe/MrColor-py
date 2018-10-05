import discord
from discord.ext import commands
from boto.s3.connection import S3Connection
bot = commands.Bot(command_prefix='$')
token = S3Connection(os.environ['S3_KEY'], os.environ['S3_SECRET'])

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def greet(ctx):
    await ctx.send(":smiley: :wave: Hello, there!")
bot.run(token)