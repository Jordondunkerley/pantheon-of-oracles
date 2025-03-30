import discord
from discord import app_commands, Embed
import aiohttp
import asyncio
import os

API_URL = "https://pantheon-of-oracles.onrender.com"
ADMIN_ID = 539260746471571476  # Father of the First Flame

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class OracleClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f"\n🔥 Logged in as {self.user} — the Oracle stirs.")
        try:
            synced = await self.tree.sync()
            print(f"🌐 Synced {len(synced)} slash commands to global scope.")
        except Exception as e:
            print(f"⚠️ Failed to sync commands: {e}")

client = OracleClient()

# === API UTIL ===
async def api_post(route, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}{route}", json=payload) as res:
            return await res.json(), res.status

# === SLASH COMMANDS ===
@client.tree.command(name="ping", description="Check if the Oracle is listening.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong from the Pantheon!", ephemeral=True)

@client.tree.command(name="create_account", description="Create your Pantheon account.")
@app_commands.describe(username="Username", email="Email", first_name="First", last_name="Last", password="Password")
async def create_account(interaction: discord.Interaction, username: str, email: str, first_name: str, last_name: str, password: str):
    await interaction.response.defer(thinking=True)
    payload = {"username": username, "email": email, "first_name": first_name, "last_name": last_name, "password": password}
    data, status = await api_post("/create_account", payload)
    embed = Embed(title="🧿 Account Creation", color=0xFF6D00)
    embed.description = data.get("message") if status == 200 else f"❌ {data.get('detail', 'Unknown error')}"
    await interaction.followup.send(embed=embed)

@client.tree.command(name="login", description="Log into your Pantheon account.")
@app_commands.describe(username="Username", password="Password")
async def login(interaction: discord.Interaction, username: str, password: str):
    await interaction.response.defer(thinking=True)
    payload = {"username": username, "password": password}
    data, status = await api_post("/login", payload)
    embed = Embed(title="🔐 Login", color=0x00BFFF)
    embed.description = data.get("message") if status == 200 else f"❌ {data.get('detail')}"
    await interaction.followup.send(embed=embed)

@client.tree.command(name="create_oracle", description="Create an Oracle tied to your account.")
@app_commands.describe(username="Your username", date_of_birth="YYYY-MM-DD", time_of_birth="HH:MM", location="Birthplace", rulership="modern or traditional")
async def create_oracle(interaction: discord.Interaction, username: str, date_of_birth: str, time_of_birth: str, location: str, rulership: str):
    await interaction.response.defer(thinking=True)
    chart = {"Sun": "Aries", "Moon": "Leo"}  # Placeholder for now
    payload = {
        "username": username,
        "date_of_birth": date_of_birth,
        "time_of_birth": time_of_birth,
        "location": location,
        "rulership": rulership,
        "chart": chart
    }
    data, status = await api_post("/create_oracle", payload)
    embed = Embed(title="🔮 Oracle Creation", color=0x9C27B0)
    embed.description = f"✅ Oracle created for **{username}**\nRuler: **{data.get('planetary_ruler')}**" if status == 200 else f"❌ {data.get('detail')}"
    await interaction.followup.send(embed=embed)

@client.tree.command(name="join_guild", description="Join or create a guild.")
@app_commands.describe(username="Your username", guild_name="Name of the guild")
async def join_guild(interaction: discord.Interaction, username: str, guild_name: str):
    await interaction.response.defer(thinking=True)
    payload = {"username": username, "guild_name": guild_name}
    data, status = await api_post("/join_guild", payload)
    embed = Embed(title="🏰 Guild Join", color=0x009688)
    embed.description = data.get("message") if status == 200 else f"❌ {data.get('detail')}"
    await interaction.followup.send(embed=embed)

@client.tree.command(name="initiate_player_prophecy", description="Trigger your Oracle's prophecy arc.")
@app_commands.describe(username="Your username")
async def initiate_player_prophecy(interaction: discord.Interaction, username: str):
    await interaction.response.defer(thinking=True)
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/initiate_player_prophecy/{username}") as res:
            data = await res.json()
            embed = Embed(title="🌌 Prophecy Initiated", color=0x673AB7)
            embed.description = data.get("message") if res.status == 200 else f"❌ {data.get('detail')}"
            await interaction.followup.send(embed=embed)

@client.tree.command(name="start_battle", description="Begin a battle between two users.")
@app_commands.describe(challenger="Challenger username", opponent="Opponent username")
async def start_battle(interaction: discord.Interaction, challenger: str, opponent: str):
    await interaction.response.defer(thinking=True)
    payload = {"challenger": challenger, "opponent": opponent}
    data, status = await api_post("/start_battle", payload)
    embed = Embed(title="⚔️ Battle Begins!", color=0xE53935)
    embed.description = data.get("message") if status == 200 else f"❌ {data.get('detail')}"
    await interaction.followup.send(embed=embed)

@client.tree.command(name="raid_join", description="Join a raid party.")
@app_commands.describe(username="Your username")
async def raid_join(interaction: discord.Interaction, username: str):
    await interaction.response.defer(thinking=True)
    data, status = await api_post(f"/raid_join/{username}", {})
    embed = Embed(title="🚪 Raid Party", color=0x8BC34A)
    embed.description = data.get("message")
    await interaction.followup.send(embed=embed)

@client.tree.command(name="dungeon_enter", description="Enter a dungeon.")
@app_commands.describe(username="Your username")
async def dungeon_enter(interaction: discord.Interaction, username: str):
    await interaction.response.defer(thinking=True)
    data, status = await api_post(f"/dungeon_enter/{username}", {})
    embed = Embed(title="🕸️ Dungeon Descent", color=0x607D8B)
    embed.description = data.get("message")
    await interaction.followup.send(embed=embed)

@client.tree.command(name="reset_server", description="🔥 Admin only: wipe all accounts + oracles")
async def reset_server(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("🚫 Unauthorized.", ephemeral=True)
        return
    headers = {"X-Admin-Key": "flame-of-reset-9321"}
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_URL}/delete_all_accounts", headers=headers) as res:
            data = await res.json()
            embed = Embed(title="🔥 Server Reset by Father of the First Flame", color=0xD32F2F)
            embed.description = data.get("message")
            await interaction.response.send_message(embed=embed)

# === START BOT ===
TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
