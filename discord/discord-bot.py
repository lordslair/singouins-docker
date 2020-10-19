#!/usr/bin/python3 -u
# -*- coding: utf8 -*-

import asyncio
import discord
import inspect
import os
import re
import sys

from datetime       import datetime,timedelta
from discord.ext    import commands
from termcolor      import colored

from queries        import *
from variables      import token
from utils.messages import *
from utils.histograms import draw

client = commands.Bot(command_prefix = '!')

# Shorted definition for actual now() with proper format
def mynow(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Welcome message in the logs on daemon start
print('{} [{}] {} [{}]'.format(mynow(),'BOT', 'Daemon started', colored('✓', 'green')))
# Pre-flich check for SQL connection
if query_up(): tick = colored('✓', 'green')
else         : tick = colored('✗', 'red')
print('{} [{}] {} [{}]'.format(mynow(),'BOT', 'SQL connection', tick))

@client.event
async def on_ready():
    channel = discord.utils.get(client.get_all_channels(), name='admins')
    if channel:
        tick = colored('✓', 'green')
        await channel.send(msg_ready)
    else: tick = colored('✗', 'red')
    print('{} [{}] {}  [{}]'.format(mynow(),'BOT', 'Discord ready', tick))

@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round (client.latency * 1000)}ms ')

@client.command(pass_context=True)
async def register(ctx,arg):
    member       = ctx.message.author
    discordname  = member.name + '#' + member.discriminator
    user         = query_get_user(discordname)
    registration = discord.utils.get(client.get_all_channels(), name='registration')

    print('{} [{}][{}] !register <{}> | {}'.format(mynow(),member,ctx.message.channel,arg,user.name))

    if (ctx.message.channel != discord.utils.get(client.get_all_channels(), name='registration')):
        # The command is entered in the wrong channel
        # Delete the !register <monkey> message sent by the user
        await ctx.message.delete()
        # Send help DM to user
        await ctx.message.author.send(msg_registration_help)
    else:
        if user:
            # The discordname is in DB
            if arg == user.d_monkeys:
                # Delete the !register <monkey> message sent by the user
                await ctx.message.delete()
                # Fetch the Discord role
                role = discord.utils.get(member.guild.roles, name='Singouins')
                # Apply role on user
                await ctx.message.author.add_roles(role)
                # Rename user
                await ctx.message.author.edit(nick = user.name)
                # Validate user association in DB
                query_validate_user(discordname)
                # Send registered DM to user
                answer = msg_registered.format(ctx.message.author,user.name)
                await ctx.message.author.send(answer)
                print('{} [{}][{}]   registration done'.format(mynow(),member,ctx.message.channel))
            else:
                # The monkey-code is wrong
               await ctx.message.author.send(msg_wrong_monkeys)
               print('{} [{}][{}]   registration failed (wrong monkeys)'.format(mynow(),member,ctx.message.channel))
        else:
            # The discordname is not in DB
            await ctx.message.author.send(msg_unknown_discordname)
            print('{} [{}][{}]   registration failed (unknown discordname)'.format(mynow(),member,ctx.message.channel))

@client.command(pass_context=True)
async def histo(ctx,arg):
    member       = ctx.message.author
    discordname  = member.name + '#' + member.discriminator
    adminrole    = discord.utils.get(member.guild.roles, name='Admins')
    adminchannel = discord.utils.get(client.get_all_channels(), name='admins')

    if adminrole in ctx.author.roles and ctx.message.channel == adminchannel:
        # This command is to be used only by Admin role
        # This command is to be used only in #admins
        print('{} [{}][{}] !histo <{}>'.format(mynow(),member,ctx.message.channel,arg))

        # We'll draw a chart with Creatures Level occurences
        array  = query_histo(arg)
        answer = draw(array)
        if answer:
            await ctx.send(answer)
            print('{} [{}][{}] └> Histogram sent'.format(mynow(),member,ctx.message.channel,arg))
        else:
            print('{} [{}][{}] └> I failed (._.) '.format(mynow(),member,ctx.message.channel,arg))
    else:
        await ctx.send(f'You need to have the role {adminrole.name}')


@client.event
async def on_member_join(member):
    answer = msg_welcome.format(member.mention,'username',member.name,member.discriminator)
    await member.send(answer)

client.run(token)
