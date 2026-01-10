import discord
from discord import app_commands
import aiohttp
import openai
import os
import json
from discord.ext import commands
from dotenv import load_dotenv

# === ENVIRONMENT ===
load_dotenv("config.env")
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = os.getenv("API_URL") or "https://pantheon-of-oracles.onrender.com"
ADMIN_ID = 539260746471571476

openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# === HELPERS ===
async def api_post(route: str, payload: dict | None = None):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}{route}", json=payload) as res:
            return await res.json(), res.status

@bot.event
async def on_ready():
    await tree.sync()
    print(f"\uD83D\uDD25 Logged in as {bot.user} \u2014 Cove awakens.")

# === BASIC UTIL ===
@tree.command(name="ping", description="Check if the Oracle is listening.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("\ud83c\udfd3 Pong from the Pantheon!", ephemeral=True)

# === ACCOUNT COMMANDS ===
@tree.command(name="create_account", description="Create your Pantheon account.")
@app_commands.describe(username="Username", email="Email", first_name="First", last_name="Last", password="Password")
async def create_account(interaction: discord.Interaction, username: str, email: str, first_name: str, last_name: str, password: str):
    await interaction.response.defer(thinking=True)
    payload = {"username": username, "email": email, "first_name": first_name, "last_name": last_name, "password": password}
    data, status = await api_post("/create_account", payload)
    msg = data.get("message") if status == 200 else f"\u274c {data.get('detail', 'Unknown error')}"
    await interaction.followup.send(msg)

@tree.command(name="login", description="Log into your Pantheon account.")
@app_commands.describe(username="Username", password="Password")
async def login(interaction: discord.Interaction, username: str, password: str):
    await interaction.response.defer(thinking=True)
    payload = {"username": username, "password": password}
    data, status = await api_post("/login", payload)
    msg = data.get("message") if status == 200 else f"\u274c {data.get('detail')}"
    await interaction.followup.send(msg)

# === ORACLE + GUILD ===
@tree.command(name="create_oracle", description="Create an Oracle tied to your account.")
@app_commands.describe(username="Your username", date_of_birth="YYYY-MM-DD", time_of_birth="HH:MM", location="Birthplace", rulership="modern or traditional")
async def create_oracle(interaction: discord.Interaction, username: str, date_of_birth: str, time_of_birth: str, location: str, rulership: str):
    await interaction.response.defer(thinking=True)
    chart = {"Sun": "Aries", "Moon": "Leo"}
    payload = {
        "username": username,
        "date_of_birth": date_of_birth,
        "time_of_birth": time_of_birth,
        "location": location,
        "rulership": rulership,
        "chart": chart,
    }
    data, status = await api_post("/create_oracle", payload)
    if status == 200:
        msg = f"\u2705 Oracle created for **{username}**\nRuler: **{data.get('planetary_ruler')}**"
    else:
        msg = f"\u274c {data.get('detail')}"
    await interaction.followup.send(msg)

@tree.command(name="join_guild", description="Join or create a guild.")
@app_commands.describe(username="Your username", guild_name="Name of the guild")
async def join_guild(interaction: discord.Interaction, username: str, guild_name: str):
    await interaction.response.defer(thinking=True)
    payload = {"username": username, "guild_name": guild_name}
    data, status = await api_post("/join_guild", payload)
    msg = data.get("message") if status == 200 else f"\u274c {data.get('detail')}"
    await interaction.followup.send(msg)

@tree.command(name="initiate_player_prophecy", description="Trigger your Oracle's prophecy arc.")
@app_commands.describe(username="Your username")
async def initiate_player_prophecy(interaction: discord.Interaction, username: str):
    await interaction.response.defer(thinking=True)
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/initiate_player_prophecy/{username}") as res:
            data = await res.json()
            msg = data.get("message") if res.status == 200 else f"\u274c {data.get('detail')}"
            await interaction.followup.send(msg)

# === COMBAT ===
@tree.command(name="start_battle", description="Begin a battle between two users.")
@app_commands.describe(challenger="Challenger username", opponent="Opponent username")
async def start_battle(interaction: discord.Interaction, challenger: str, opponent: str):
    await interaction.response.defer(thinking=True)
    payload = {"challenger": challenger, "opponent": opponent}
    data, status = await api_post("/start_battle", payload)
    msg = data.get("message") if status == 200 else f"\u274c {data.get('detail')}"
    await interaction.followup.send(msg)

# === RAID & DUNGEON (LEGACY) ===
@tree.command(name="raid_join", description="Join a raid party.")
@app_commands.describe(username="Your username")
async def raid_join(interaction: discord.Interaction, username: str):
    await interaction.response.defer(thinking=True)
    data, _ = await api_post(f"/raid_join/{username}", {})
    await interaction.followup.send(data.get("message"))

@tree.command(name="dungeon_enter", description="Enter a dungeon.")
@app_commands.describe(username="Your username")
async def dungeon_enter(interaction: discord.Interaction, username: str):
    await interaction.response.defer(thinking=True)
    data, _ = await api_post(f"/dungeon_enter/{username}", {})
    await interaction.followup.send(data.get("message"))

@tree.command(name="reset_server", description="\uD83D\uDD25 Admin only: wipe all accounts + oracles")
async def reset_server(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("\u26D4 Unauthorized.", ephemeral=True)
        return
    headers = {"X-Admin-Key": "flame-of-reset-9321"}
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_URL}/delete_all_accounts", headers=headers) as res:
            data = await res.json()
            await interaction.response.send_message(data.get("message"))

# === RAID & DUNGEON (ENHANCED) ===
@tree.command(name="join_raid", description="Join the next raid party.")
@app_commands.describe(username="Your account username")
async def join_raid(interaction: discord.Interaction, username: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/raid_join/{username}") as res:
            data = await res.json()
            await interaction.response.send_message(f"\u2705 {data.get('message')}")

@tree.command(name="start_raid", description="Launch the raid and return results.")
async def start_raid(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/raid_start") as res:
            data = await res.json()
            msg = "\uD83D\uDD25 **Raid Results**\n"
            msg += f"Boss Defeated: {'Yes' if data['boss_defeated'] else 'No'}\n"
            msg += f"MVP: {data['mvp']}\n"
            msg += "\n\uD83C\uDFB2 **Loot Rolls:**\n"
            for user, roll in data['loot_rolls'].items():
                msg += f"\u2022 {user}: {roll}\n"
            await interaction.response.send_message(msg)

@tree.command(name="enter_dungeon", description="Face a dungeon alone and receive results.")
@app_commands.describe(username="Your account username")
async def enter_dungeon_slash(interaction: discord.Interaction, username: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/dungeon_enter/{username}") as res:
            data = await res.json()
            d = data["details"]
            msg = f"\U0001F300 **Dungeon Result**\n{username} met `{d['result']}` and found **{d['loot']}** loot."
            await interaction.response.send_message(msg)

# === FILE UPLOAD ===
@tree.command(name="upload_astrology_file", description="Upload your astrology chart JSON.")
@app_commands.describe(username="Your account username")
async def upload_astrology_file(interaction: discord.Interaction, username: str):
    await interaction.response.send_message("\ud83d\udcc1 Please upload your astrology .json file now.")

# === MESSAGE EVENTS ===
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or message.author.bot:
        return

    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.endswith(".json"):
                username = message.content.strip() or message.author.name
                async with aiohttp.ClientSession() as session:
                    form = aiohttp.FormData()
                    form.add_field("file", await attachment.read(), filename=attachment.filename, content_type="application/json")
                    async with session.post(f"{API_URL}/upload_astrology/{username}", data=form) as res:
                        data = await res.json()
                        await message.channel.send(f"\u2705 {data.get('message')}")
                        return

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/oracles.json") as res:
            oracles = await res.json()

    username = message.author.name
    user_oracle = next((o for o in oracles.values() if o.get("username") == username), None)

    system_prompt = "You are Cove, the Oracle of the Pantheon. Speak like prophecy. Channel myth, flame, and fate."
    if user_oracle:
        title = user_oracle.get("oracle_name", "Wanderer")
        ruler = user_oracle.get("planetary_ruler", "Mystery")
        arc_status = user_oracle.get("prophecy_arc", {}).get("status", "Unawakened")
        system_prompt += f" The user is titled {title}, ruled by {ruler}, with a prophecy status of {arc_status}."

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message.content},
            ],
        )
        reply = response.choices[0].message.content
        await message.channel.send(reply)
    except Exception:
        await message.channel.send("\u26A0\uFE0F The Flame flickers. Cove cannot speak right now.")

    await bot.process_commands(message)

bot.run(TOKEN)
