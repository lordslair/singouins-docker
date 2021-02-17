# -*- coding: utf8 -*-

import os
import re
import sys

from datetime           import datetime,timedelta
from termcolor          import colored

# Shorted definition for actual now() with proper format
def mynow(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Log Discord imports
print('{} [{}] {} [{}]'.format(mynow(),'BOT', 'System   imports finished', colored('✓', 'green')))

import asyncio
import discord
import inspect

from discord.ext        import commands

# Log Discord imports
print('{} [{}] {} [{}]'.format(mynow(),'BOT', 'Discord  imports finished', colored('✓', 'green')))

from mysql.methods      import *
from mysql.utils        import redis
from variables          import token
from utils.messages     import *
from utils.histograms   import draw

from mysql.methods.fn_creature import fn_creature_get
from mysql.methods.fn_user     import fn_user_get_from_member

# Log Discord imports
print('{} [{}] {} [{}]'.format(mynow(),'BOT', 'Internal imports finished', colored('✓', 'green')))

client = commands.Bot(command_prefix = '!')

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
        #await channel.send(msg_ready)
    else: tick = colored('✗', 'red')
    print('{} [{}] {}  [{}]'.format(mynow(),'BOT', 'Discord ready', tick))

#
# Commands
#

# !ping
@client.command(name='ping', help='Gives you Discord bot latency')
async def ping(ctx):
    member       = ctx.message.author
    discordname  = member.name + '#' + member.discriminator

    print('{} [{}][{}] !ping'.format(mynow(),ctx.message.channel,member))
    await ctx.send(f'Pong! {round (client.latency * 1000)}ms ')

#
# Commands for Registration/Grant
#

# !register {user.mail}
@client.command(pass_context=True,name='register', help='Register a Discord user with a Singouins user')
async def register(ctx, usermail: str = None):
    member       = ctx.message.author
    discordname  = member.name + '#' + member.discriminator

    print('{} [{}][{}] !register <usermail:{}>'.format(mynow(),ctx.message.channel,member,usermail))

    if usermail is None:
        print('{} [{}][{}] └> Sent Helper'.format(mynow(),ctx.message.channel,member))
        await ctx.message.author.send(msg_register_helper)
        return

    # Validate user association in DB
    user = query_user_validate(usermail,discordname)
    if user:
        # Send registered DM to user
        answer = msg_register_ok.format(ctx.message.author)
        await ctx.message.author.send(answer)
        print('{} [{}][{}] └> Validation in DB Successful'.format(mynow(),ctx.message.channel,member))
    else:
        # Send failure DM to user
        await ctx.message.author.send(msg_register_ko)
        print('{} [{}][{}] └> Validation in DB Failed'.format(mynow(),ctx.message.channel,member))

# !grant
@client.command(pass_context=True,name='grant', help='Grant a Discord user relative roles')
async def register(ctx):
    member       = ctx.message.author

    print('{} [{}][{}] !grant'.format(mynow(),ctx.message.channel,member))

    # Check if the command is used in a channel or a DM
    if isinstance(ctx.message.channel, discord.DMChannel):
        # In DM
        print('{} [{}][{}] └> Sent Helper'.format(mynow(),ctx.message.channel,member))
        await ctx.message.author.send(msg_grant_helper)
        return
    else:
        # In a Channel
        pass

    # Delete the message sent by the user
    try:
        await ctx.message.delete()
    except:
        pass
    else:
        print('{} [{}][{}] └> Message deleted'.format(mynow(),ctx.message.channel,member))

    user = fn_user_get_from_member(member)
    if user:
        # Fetch the Discord role
        try:
            role = discord.utils.get(member.guild.roles, name='Singouins')
        except Exception as e:
            # Something went wrong
            print('{} [{}][{}] └> Member get-role Failed'.format(mynow(),ctx.message.channel,member))
        else:
            print('{} [{}][{}] └> Member get-role Successful'.format(mynow(),ctx.message.channel,member))

        # Apply role on user
        try:
            await ctx.message.author.add_roles(role)
        except Exception as e:
            # Something went wrong during commit
            print('{} [{}][{}] └> Member add-role Failed'.format(mynow(),ctx.message.channel,member))
            # Send failure DM to user
            await ctx.message.author.send(msg_grant_ko)
        else:
            # Send success DM to user
            await ctx.message.author.send(msg_grant_ok)
            print('{} [{}][{}] └> Member add-role Successful'.format(mynow(),ctx.message.channel,member))
    else:
        # Send failure DM to user
        await ctx.message.author.send(msg_grant_ko)
        print('{} [{}][{}] └> Query in DB Failed'.format(mynow(),ctx.message.channel,member))

#
# Commands for Admins
#

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

@client.command(pass_context=True)
async def admin(ctx,*args):
    member       = ctx.message.author
    discordname  = member.name + '#' + member.discriminator
    adminrole    = discord.utils.get(member.guild.roles, name='Admins')

    if adminrole not in ctx.author.roles:
        # This command is to be used only by Admin role
        print('{} [{}][{}] !admin <{}> [{}]'.format(mynow(),ctx.message.channel,member,args,'Unauthorized user'))

    # Channel and User are OK
    print('{} [{}][{}] !admin <{}>'.format(mynow(),ctx.message.channel,member,args))

    if args[0] == 'help':
        await ctx.send(f'```{msg_cmd_admin_help}```')
        return

    if len(args) < 4:
        await ctx.send('`!admin needs more arguments`')
        return

    module = args[0]
    action = args[1]
    select = args[2]
    pcid   = int(args[3])

    pc = fn_creature_get(None,pcid)[3]
    if pc is None:
        await ctx.send(f'`Unknown creature pcid:{pcid}`')
        return

    if module == 'redis':
        if action == 'reset':
            if select == 'all':
                redis.reset_pa(pc,True,True)
                await ctx.send(f'`Reset PA {select} done for pcid:{pc.id}`')
            elif select == 'red':
                redis.reset_pa(pc,False,True)
                await ctx.send(f'`Reset PA {select} done for pcid:{pc.id}`')
            elif select == 'blue':
                redis.reset_pa(pc,True,False)
                await ctx.send(f'`Reset PA {select} done for pcid:{pc.id}`')
        elif action == 'get':
            if select == 'all':
                pa = redis.get_pa(pc)
                await ctx.send(pa)
        elif action == 'help':
            await ctx.send('`!admin redis {reset|get} {all|blue|red} {pcid}`')
    if module == 'wallet':
        if action == 'get':
            if select == 'all':
                wallet = query_wallet_get(pc)
                if wallet:
                    await ctx.send(wallet)
        elif action == 'help':
            await ctx.send('`!admin wallet {get} {all} {pcid}`')

#
# Commands for Singouins
#
# DM Only Commands
@client.command(pass_context=True,name='mysingouins', help='Display your Singouins')
async def mysingouins(ctx):
    member       = ctx.message.author

    print('{} [{}][{}] !mysingouins'.format(mynow(),ctx.message.channel,member))

    # Check if the command is used in a channel or a DM
    if isinstance(ctx.message.channel, discord.DMChannel):
        # In DM
        pass
    else:
        # In a Channel
        # Delete the command message sent by the user
        try:
            await ctx.message.delete()
        except:
            pass
        else:
            print('{} [{}][{}] └> Message deleted'.format(mynow(),ctx.message.channel,member))
        return

    emojiM = discord.utils.get(client.emojis, name='statM')
    emojiR = discord.utils.get(client.emojis, name='statR')
    emojiV = discord.utils.get(client.emojis, name='statV')
    emojiG = discord.utils.get(client.emojis, name='statG')
    emojiP = discord.utils.get(client.emojis, name='statP')
    emojiB = discord.utils.get(client.emojis, name='statB')

    emojiRaceC = discord.utils.get(client.emojis, name='raceC')
    emojiRaceG = discord.utils.get(client.emojis, name='raceG')
    emojiRaceM = discord.utils.get(client.emojis, name='raceM')
    emojiRaceO = discord.utils.get(client.emojis, name='raceO')
    emojiRace = [emojiRaceC,
                 emojiRaceG,
                 emojiRaceM,
                 emojiRaceO]

    pcs = query_pcs_get(member)[3]
    if pcs is None:
        await ctx.send(f'`No Singouin found in DB`')

    mydesc = ''
    for pc in pcs:
        emojiMyRace = emojiRace[pc.race - 1]
        mydesc += f'{emojiMyRace} [{pc.id}] {pc.name}\n'

    embed = discord.Embed(
        title = 'Mes Singouins:',
        description = mydesc,
        colour = discord.Colour.blue()
    )

    await ctx.send(embed=embed)

@client.command(pass_context=True,name='mysingouin', help='Display a Singouin profile')
async def mysingouin(ctx, pcid: int = None):
    member       = ctx.message.author

    print('{} [{}][{}] !mysingouin <{}>'.format(mynow(),ctx.message.channel,member,pcid))

    if pcid is None:
        print('{} [{}][{}] └> Sent Helper'.format(mynow(),ctx.message.channel,member))
        await ctx.message.author.send(msg_mysingouin_helper)
        return

    # Check if the command is used in a channel or a DM
    if isinstance(ctx.message.channel, discord.DMChannel):
        # In DM
        pass
    else:
        # In a Channel
        # Delete the command message sent by the user
        try:
            await ctx.message.delete()
        except:
            pass
        else:
            print('{} [{}][{}] └> Message deleted'.format(mynow(),ctx.message.channel,member))
        return

    pc = query_pc_get(pcid,member)[3]
    if pc is None:
        await ctx.send(f'`Singouin not yours/not found in DB (pcid:{pcid})`')
        return

    stuff = query_mypc_items_get(pcid,member)[3]
    if stuff is None:
        await ctx.send(f'`Singouin Stuff not found in DB (pcid:{pcid})`')
        return

    embed = discord.Embed(
        title = f'[{pc.id}] {pc.name}\n',
        #description = 'Profil:',
        colour = discord.Colour.blue()
    )

    emojiM = discord.utils.get(client.emojis, name='statM')
    emojiR = discord.utils.get(client.emojis, name='statR')
    emojiV = discord.utils.get(client.emojis, name='statV')
    emojiG = discord.utils.get(client.emojis, name='statG')
    emojiP = discord.utils.get(client.emojis, name='statP')
    emojiB = discord.utils.get(client.emojis, name='statB')

    msg_stats = 'Stats:'
    msg_nbr   = 'Nbr:'
    embed.add_field(name=f'`{msg_stats: >9}`      {emojiM}      {emojiR}      {emojiV}      {emojiG}      {emojiP}      {emojiB}',
                    value=f'`{msg_nbr: >9}` `{pc.m: >4}` `{pc.r: >4}` `{pc.v: >4}` `{pc.g: >4}` `{pc.p: >4}` `{pc.b: >4}`',
                    inline = False)

    emojiShardL = discord.utils.get(client.emojis, name='shardL')
    emojiShardE = discord.utils.get(client.emojis, name='shardE')
    emojiShardR = discord.utils.get(client.emojis, name='shardR')
    emojiShardU = discord.utils.get(client.emojis, name='shardU')
    emojiShardC = discord.utils.get(client.emojis, name='shardC')
    emojiShardB = discord.utils.get(client.emojis, name='shardB')

    wallet     = stuff['wallet'][0]
    msg_shards = 'Shards:'
    msg_nbr    = 'Nbr:'
    embed.add_field(name=f'`{msg_shards: >9}`      {emojiShardL}      {emojiShardE}      {emojiShardR}      {emojiShardU}      {emojiShardC}      {emojiShardB}',
                    value=f'`{msg_nbr: >9}` `{wallet.legendary: >4}` `{wallet.epic: >4}` `{wallet.rare: >4}` `{wallet.uncommon: >4}` `{wallet.common: >4}` `{wallet.broken: >4}`',
                    inline = False)

    emojiAmmo22  = discord.utils.get(client.emojis, name='ammo22')
    emojiAmmo223 = discord.utils.get(client.emojis, name='ammo223')
    emojiAmmo311 = discord.utils.get(client.emojis, name='ammo311')
    emojiAmmo50  = discord.utils.get(client.emojis, name='ammo50')
    emojiAmmo55  = discord.utils.get(client.emojis, name='ammo55')
    emojiAmmoS   = discord.utils.get(client.emojis, name='ammoShell')

    msg_shards = 'Ammo:'
    msg_nbr    = 'Nbr:'
    embed.add_field(name=f'`{msg_shards: >9}`      {emojiAmmo22}      {emojiAmmo223}      {emojiAmmo311}      {emojiAmmo50}      {emojiAmmo55}      {emojiAmmoS}',
                    value=f'`{msg_nbr: >9}` `{wallet.cal22: >4}` `{wallet.cal223: >4}` `{wallet.cal311: >4}` `{wallet.cal50: >4}` `{wallet.cal55: >4}` `{wallet.shell: >4}`',
                    inline = False)

    emojiAmmoA   = discord.utils.get(client.emojis, name='ammoArrow')
    emojiAmmoB   = discord.utils.get(client.emojis, name='ammoBolt')
    emojiAmmoF   = discord.utils.get(client.emojis, name='ammoFuel')
    emojiAmmoG   = discord.utils.get(client.emojis, name='ammoGrenade')
    emojiAmmoR   = discord.utils.get(client.emojis, name='ammoRocket')

    emojiMoneyB  = discord.utils.get(client.emojis, name='moneyB')

    # Temporary
    wallet.fuel     = 0
    wallet.grenade  = 0
    wallet.rocket   = 0

    msg_shards = 'Specials:'
    msg_nbr    = 'Nbr:'
    embed.add_field(name=f'`{msg_shards: >9}`      {emojiAmmoA}      {emojiAmmoB}      {emojiAmmoF}      {emojiAmmoG}      {emojiAmmoR}      {emojiMoneyB}',
                    value=f'`{msg_nbr: >9}` `{wallet.arrow: >4}` `{wallet.bolt: >4}` `{wallet.fuel: >4}` `{wallet.grenade: >4}` `{wallet.rocket: >4}` `{wallet.currency: >4}`',
                    inline = False)

    await ctx.send(embed=embed)

# Channel only Commands
@client.command(pass_context=True,name='mysquads', help='Singouin Squad actions')
async def mysingouin(ctx, action: str = None):
    member       = ctx.message.author

    print(f'{mynow()} [{ctx.message.channel}][{member}] !mysquad <{action}>')

    # Delete the command message sent by the user
    try:
        await ctx.message.delete()
    except:
        print(f'{mynow()} [{ctx.message.channel}][{member}] ├──> Message deletion failed')
    else:
        print(f'{mynow()} [{ctx.message.channel}][{member}] ├──> Message deleted')

    if action is None:
        print(f'{mynow()} [{ctx.message.channel}][{member}] └──> Sent Helper (action:{action})')
        await ctx.message.author.send(msg_mysquad_helper)
        return

    # Check if the command is used in a channel or a DM
    if isinstance(ctx.message.channel, discord.DMChannel):
        # In DM
        print(f'{mynow()} [{ctx.message.channel}][{member}] └──> Sent Helper (Wrong channel)')
        await ctx.message.author.send(msg_mysquad_helper_dm)
    else:
        # In a Channel
        pass

    if action == 'help':
        print(f'{mynow()} [{ctx.message.channel}][{member}] └──> Sent Helper (action:{action})')
        await ctx.message.author.send(msg_mysquad_helper)
    if action == 'init':
        guild         = ctx.guild
        admin_role    = discord.utils.get(guild.roles, name='Team')
        category      = discord.utils.get(guild.categories, name='Squads')
        squads        = query_squads_get(member)
        overwrites    = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            admin_role: discord.PermissionOverwrite(read_messages=True)
        }

        if squads[3] is not None:
            print(f'{mynow()} [{ctx.message.channel}][{member}] ├──> Received Squads infos ({squads[3]})')
        else:
            print(f'{mynow()} [{ctx.message.channel}][{member}] └──> Received no Squads infos ({squads[3]})')
            return

        squadlist = squads[3]['leader'] + squads[3]['member']
        squadset  = set(squadlist)

        for squadid in squadset:
            print(f'{mynow()} [{ctx.message.channel}][{member}] └──> Squad detected (squadid:{squadid})')

            # Check channel existance
            if discord.utils.get(category.channels, name=f'Squad-{squadid}'.lower()):
                # Channel already exists, do nothing
                print(f'{mynow()} [{ctx.message.channel}][{member}]    ├──> Squad channel already exists (Squads/Squad-{squadid})')
            else:
                # Channel do not exist, create it
                try:
                    mysquadchannel = await guild.create_text_channel(f'Squad-{squadid}',
                                                                     category=category,
                                                                     topic=f'Squad-{squadid} private channel',
                                                                     overwrites=overwrites)
                except:
                    print(f'{mynow()} [{ctx.message.channel}][{member}]    ├──> Squad channel creation failed (squadid:{squadid})')
                else:
                    print(f'{mynow()} [{ctx.message.channel}][{member}]    ├──> Squad channel created (Squads/Squad-{squadid})')

            # Check role existence
            if discord.utils.get(guild.roles, name=f'Squad-{squadid}'):
                # Role already exists, do nothing
                print(f'{mynow()} [{ctx.message.channel}][{member}]    └──> Squad role already exists (squadid:{squadid})')
            else:
                # Role do not exist, create it
                try:
                    role = await guild.create_role(name=f'Squad-{squadid}',
                                                   mentionable=True,
                                                   permissions=discord.Permissions.none())
                except:
                    print(f'{mynow()} [{ctx.message.channel}][{member}]    └──> Squad role creation failed (squadid:{squadid})')
                else:
                    print(f'{mynow()} [{ctx.message.channel}][{member}]    └──> Squad role creation successed (squadid:{squadid})')

    elif action == 'grant':
        guild      = ctx.guild
        squads = query_squads_get(member)
        if squads[3] is not None:
            print(f'{mynow()} [{ctx.message.channel}][{member}] ├──> Received Squads infos ({squads[3]})')

            squadlist = squads[3]['leader'] + squads[3]['member']
            squadset  = set(squadlist)

            for squadid in squadset:
                print(f'{mynow()} [{ctx.message.channel}][{member}] └──> Squad detected (squadid:{squadid})')

                # Add the squad role to the user
                try:
                    squadrole = discord.utils.get(guild.roles, name=f'Squad-{squadid}')
                except:
                    print(f'{mynow()} [{ctx.message.channel}][{member}]    └──> Squad role not found (squadid:{squadid})')
                else:
                    if squadrole in member.roles:
                        print(f'{mynow()} [{ctx.message.channel}][{member}]    └──> Squad add-role already done (squadid:{squadid})')
                        return

                    try:
                        await ctx.author.add_roles(squadrole)
                    except:
                        print(f'{mynow()} [{ctx.message.channel}][{member}]    └──> Squad add-role failed (squadid:{squadid})')
                    else:
                        print(f'{mynow()} [{ctx.message.channel}][{member}]    └──> Squad add-role successed (squadid:{squadid})')

@client.event
async def on_member_join(member):
    await member.send(msg_welcome)

client.run(token)
