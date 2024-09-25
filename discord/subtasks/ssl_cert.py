# -*- coding: utf8 -*-

import asyncio
import discord

from datetime import datetime
from loguru import logger
from urllib.request import ssl, socket

from variables import env_vars


async def validator(bot: discord.Client, timer: int):
    while bot.is_ready:
        if bot.user:
            try:
                context = ssl.create_default_context()
                SSL_TARGET = env_vars['SSL_TARGET_HOST'] + ':' + env_vars['SSL_TARGET_PORT']

                with socket.create_connection(
                    (env_vars['SSL_TARGET_HOST'], env_vars['SSL_TARGET_PORT'])
                ) as sock:
                    with context.wrap_socket(
                        sock,
                        server_hostname=env_vars['SSL_TARGET_HOST'],
                    ) as ssock:
                        certificate = ssock.getpeercert()
            except Exception as e:
                logger.error(f"SSL Cert Query KO ({SSL_TARGET}) [{e}]")
                continue
            else:
                logger.trace(f"SSL Cert Query OK ({SSL_TARGET})")

            try:
                channel = discord.utils.get(bot.get_all_channels(), name=env_vars['SSL_CHANNEL'])
            except Exception as e:
                logger.error(f"Discord Channel Query KO (channel:#{env_vars['SSL_CHANNEL']}) [{e}]") # noqa E501
                continue

            try:
                cert_expires = datetime.strptime(certificate['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (cert_expires - datetime.now()).days
                common_name = certificate['subject'][0][0][1]
                description = f'The SSL cert. for {common_name} expires in **{days_left}** days'

                if days_left > 15:
                    # Everything is fine
                    logger.debug(description)
                    embed = None
                elif 7 < days_left < 15:
                    # We need to do something
                    logger.warning(description)
                    embed = discord.Embed(
                        title='SSL Certificate Validator',
                        description=description,
                        colour=discord.Colour.orange()
                    )
                    embed.set_thumbnail(url=env_vars['SSL_IMG_URL'])
                elif days_left <= 7:
                    # We need to do something FAST
                    logger.error(description)
                    embed = discord.Embed(
                        title='SSL Certificate Validator',
                        description=description,
                        colour=discord.Colour.red()
                    )
                    embed.set_thumbnail(url=env_vars['SSL_IMG_URL'])
            except Exception as e:
                logger.error(f'Discord Embed KO [{e}]')
                continue
            else:
                if embed:
                    await channel.send(embed=embed)
                    logger.trace('Discord Embed OK')

        await asyncio.sleep(timer)
