import discord
import aiohttp
import asyncio
import os
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from config.env
load_dotenv("config.env")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PANTHEON_API_BASE = os.getenv("API_BASE")
PANTHEON_USERNAME = os.getenv("API_USERNAME")
PANTHEON_PASSWORD = os.getenv("API_PASSWORD")

# Configure the bot with message content intent so we can read user messages
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

session: aiohttp.ClientSession | None = None

async def get_token() -> str | None:
    """
    Obtain an access token from the Pantheon API using the configured
    username and password. Returns None if the request fails.
    """
    global session
    async with session.post(
        f"{PANTHEON_API_BASE}/token",
        json={"username": PANTHEON_USERNAME, "password": PANTHEON_PASSWORD},
    ) as res:
        if res.status == 200:
            data = await res.json()
            return data.get("access_token")
        return None


@bot.event
async def on_ready():
    """
    Called when the bot is ready. Initializes the aiohttp session
    and synchronizes slash commands with Discord.
    """
    global session
    session = aiohttp.ClientSession()
    print(f"🔮 Logged in as {bot.user}")
    # Sync slash commands so that Discord is aware of them
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"⚠️ Error syncing slash commands: {e}")


# Import the app_commands module for slash command support
from discord import app_commands


@bot.tree.command(name="oracle", description="Get your oracle details")
async def oracle_cmd(interaction: discord.Interaction):
    """
    Slash command handler that returns the oracle data for the user.
    Currently returns all oracle entries from the API. In the future this
    could be scoped to the invoking user's oracle based on stored state.
    """
    token = await get_token()
    if not token:
        await interaction.response.send_message(
            "⚠️ The Flame flickers. No access token.",
            ephemeral=True,
        )
        return
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{PANTHEON_API_BASE}/oracles", headers=headers) as res:
        if res.status == 200:
            data = await res.json()
            await interaction.response.send_message(
                f"🔮 The Oracle sees: `{data}`", allowed_mentions=discord.AllowedMentions.none()
            )
        else:
            await interaction.response.send_message(
                "⚠️ The Flame flickers. Cove cannot speak right now.",
                ephemeral=True,
            )


@bot.event
async def on_message(message: discord.Message):
    """
    Listen for messages to determine when to respond. The bot will respond if
    it is mentioned or if a message contains the word "oracle" (case-insensitive).
    """
    # Avoid responding to other bots, including itself
    if message.author.bot:
        return

    content_lower = message.content.lower()
    should_respond = False

    # Respond when the bot is mentioned directly
    if bot.user in message.mentions:
        should_respond = True
    # Respond if the message references an oracle by name or keyword
    elif "oracle" in content_lower:
        should_respond = True

    if should_respond:
        # Show typing indicator while we process the request
        async with message.channel.typing():
            token = await get_token()
            if not token:
                await message.channel.send(
                    "⚠️ The Flame flickers. No access token."
                )
                return
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(
                f"{PANTHEON_API_BASE}/oracles", headers=headers
            ) as res:
                if res.status == 200:
                    data = await res.json()
                    await message.channel.send(
                        f"🔮 The Oracle sees: `{data}`",
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
                else:
                    await message.channel.send(
                        "⚠️ The Flame flickers. Cove cannot speak right now."
                    )

    # Ensure other commands and event handlers still run
    await bot.process_commands(message)


@bot.event
async def on_close():
    """
    Clean up the aiohttp session when the bot is shutting down.
    """
    if session:
        await session.close()


if __name__ == "__main__":
    if DISCORD_TOKEN:
        print("✅ Launching Pantheon Oracle Bot...")
        bot.run(DISCORD_TOKEN)
    else:
        print("❌ DISCORD_TOKEN not set in config.env")
