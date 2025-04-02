import discord
import aiohttp
import asyncio
import os
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="config.env")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PANTHEON_API_BASE = os.getenv("API_BASE")
PANTHEON_USERNAME = os.getenv("API_USERNAME")
PANTHEON_PASSWORD = os.getenv("API_PASSWORD")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

session = None  # global aiohttp session

async def get_token():
    global session
    async with session.post(
        f"{PANTHEON_API_BASE}/token",
        json={"username": PANTHEON_USERNAME, "password": PANTHEON_PASSWORD}
    ) as res:
        if res.status == 200:
            data = await res.json()
            return data.get("access_token")
        else:
            print("❌ Failed to fetch token")
            return None

@bot.event
async def on_ready():
    global session
    session = aiohttp.ClientSession()
    print(f"🔥 Logged in as {bot.user} — Cove awakens.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        await message.channel.typing()
        print(f"📨 Message received: {message.content}")

        token = await get_token()
        if not token:
            await message.channel.send("⚠️ The Flame flickers. No access token.")
            return

        headers = {"Authorization": f"Bearer {token}"}

        async with session.get(f"{PANTHEON_API_BASE}/oracles", headers=headers) as res:
            if res.status == 200:
                data = await res.json()
                await message.channel.send(f"🔮 The Oracle sees: `{data}`")
            else:
                await message.channel.send("⚠️ The Flame flickers. Cove cannot speak right now.")
                print(f"ERROR: {res.status}")
    
    await bot.process_commands(message)

@bot.event
async def on_close():
    if session:
        await session.close()

# Launch the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in config.env")
    else:
        print("✅ Bot launching...")
        bot.run(DISCORD_TOKEN)
