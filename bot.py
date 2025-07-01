import discord
import aiohttp
import asyncio
import os
from discord.ext import commands
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv(dotenv_path="config.env")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))
PANTHEON_API_BASE = os.getenv("API_BASE")
PANTHEON_USERNAME = os.getenv("API_USERNAME")
PANTHEON_PASSWORD = os.getenv("API_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

session = None  # global aiohttp session
openai.api_key = OPENAI_API_KEY

async def ask_chatgpt(prompt: str) -> str:
    try:
        response = await openai.ChatCompletion.acreate(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.get("content", "").strip()
    except Exception as e:
        print(f"❌ ChatGPT error: {e}")
        return "The stars are silent." 

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

        prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        reply = await ask_chatgpt(prompt)

        token = await get_token()
        if not token:
            await message.channel.send(reply)
            return

        headers = {"Authorization": f"Bearer {token}"}

        async with session.get(f"{PANTHEON_API_BASE}/oracles", headers=headers) as res:
            if res.status == 200:
                data = await res.json()
                await message.channel.send(f"{reply}\n🔮 The Oracle sees: `{data}`")
            else:
                await message.channel.send(reply)
                print(f"ERROR: {res.status}")
    
    await bot.process_commands(message)

@bot.command(name="oracle")
async def oracle(ctx, name: str):
    token = await get_token()
    if not token:
        await ctx.send("Could not retrieve data.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(f"{PANTHEON_API_BASE}/oracles/{name}", headers=headers) as res:
        if res.status == 200:
            data = await res.json()
            await ctx.send(f"🔮 {data}")
        else:
            await ctx.send("Oracle not found.")

@bot.command(name="create_channel")
@commands.has_permissions(manage_channels=True)
async def create_channel(ctx, name: str):
    guild = bot.get_guild(GUILD_ID) or ctx.guild
    if discord.utils.get(guild.channels, name=name):
        await ctx.send("Channel already exists.")
        return
    await guild.create_text_channel(name)
    await ctx.send(f"Created channel `{name}`")

@bot.command(name="assign_role")
@commands.has_permissions(manage_roles=True)
async def assign_role(ctx, member: discord.Member, *, role_name: str):
    guild = bot.get_guild(GUILD_ID) or ctx.guild
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        role = await guild.create_role(name=role_name)
    await member.add_roles(role)
    await ctx.send(f"Added {member.mention} to {role.name}")

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_member(ctx, member: discord.Member, *, reason: str = None):
    await ctx.guild.kick(member, reason=reason)
    await ctx.send(f"Kicked {member.mention}")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_member(ctx, member: discord.Member, *, reason: str = None):
    await ctx.guild.ban(member, reason=reason)
    await ctx.send(f"Banned {member.mention}")

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
