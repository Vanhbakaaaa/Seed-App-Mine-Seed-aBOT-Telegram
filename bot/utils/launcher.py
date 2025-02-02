import os
import glob
import asyncio
import argparse
import sys
from itertools import cycle

from pyrogram import Client
from better_proxy import Proxy

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.query import run_tapper_query
from bot.core.registrator import register_sessions
from .ps import check_base_url


start_text = """

    ░██████╗███████╗███████╗██████╗░  ███╗░░░███╗██╗███╗░░██╗███████╗██████╗░
    ██╔════╝██╔════╝██╔════╝██╔══██╗  ████╗░████║██║████╗░██║██╔════╝██╔══██╗
    ╚█████╗░█████╗░░█████╗░░██║░░██║  ██╔████╔██║██║██╔██╗██║█████╗░░██████╔╝
    ░╚═══██╗██╔══╝░░██╔══╝░░██║░░██║  ██║╚██╔╝██║██║██║╚████║██╔══╝░░██╔══██╗
    ██████╔╝███████╗███████╗██████╔╝  ██║░╚═╝░██║██║██║░╚███║███████╗██║░░██║
    ╚═════╝░╚══════╝╚══════╝╚═════╝░  ╚═╝░░░░░╚═╝╚═╝╚═╝░░╚══╝╚══════╝╚═╝░░╚═╝
                                    BY VANHBAKA                                                                                                       
                                                                   
Select an action:

    1. Run clicker (session)
    2. Create session
    3. Run clicker (query)
"""

global tg_clients

def get_session_names() -> list[str]:
    session_names = sorted(glob.glob("sessions/*.session"))
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]

    return session_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


async def get_tg_clients() -> list[Client]:
    global tg_clients

    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]

    return tg_clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")

    logger.info(f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies")

    if check_base_url() is False:
        if settings.ADVANCED_ANTI_DETECTION:
            sys.exit("Detected index js file change. Contact me to check if it's safe to continue: https://t.me/vanhbakaaa")
        else:
            sys.exit(
                "Detected api change! Stopped the bot for safety. Contact me here to update the bot: https://t.me/vanhbakaaa")

    action = parser.parse_args().action

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ["1", "2", "3"]:
                logger.warning("Action must be 1, 2 or 3")
            else:
                action = int(action)
                break

    if action == 2:
        await register_sessions()
    elif action == 1:
        tg_clients = await get_tg_clients()

        await run_tasks(tg_clients=tg_clients)
    elif action == 3:
        with open("data.txt", "r") as f:
            query_ids = [line.strip() for line in f.readlines()]
        proxies = get_proxies()
        # print(query_ids)
        await run_tapper_query(query_ids, proxies)



async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
            )
        )
        for tg_client in tg_clients
    ]

    await asyncio.gather(*tasks)
