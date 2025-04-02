# generate_session.py
# python telegram_client.py --api_id YOUR_API_ID --api_hash YOUR_API_HASH --phone +123456789
import argparse
import asyncio
from pyrogram import Client

parser = argparse.ArgumentParser(description="Generate Pyrogram session string")
parser.add_argument("--api_id", required=True, help="Your API ID")
parser.add_argument("--api_hash", required=True, help="Your API Hash")
args = parser.parse_args()

async def generate_session():
    async with Client("cli_session", api_id=args.api_id, api_hash=args.api_hash) as app:
        print("Successfully logged in.")
        session_str = await app.export_session_string()
        print(f"\nYour session string:\n\n{session_str}\n")

asyncio.run(generate_session())