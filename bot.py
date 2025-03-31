import discord
from discord import app_commands
import aiohttp, openai, os, json
from discord.ext import commands
from dotenv import load_dotenv

# === ENV ===
load_dotenv(dotenv_path="config.env")
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("API_BASE")
openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"\U0001F525 Logged in as {bot.user} — Cove awakens.")

# === SLASH: Upload Astrology ===
@tree.command(name="upload_astrology_file", description="Upload your astrology chart JSON.")
@app_commands.describe(username="Your account username")
async def upload_astrology_file(interaction: discord.Interaction, username: str):
    await interaction.response.send_message("\U0001F4C1 Please upload your astrology .json file now.")

# === SLASH: Join Raid ===
@tree.command(name="join_raid", description="Join the next raid party.")
@app_commands.describe(username="Your account username")
async def join_raid(interaction: discord.Interaction, username: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE}/raid_join/{username}") as res:
            data = await res.json()
            await interaction.response.send_message(f"✅ {data.get('message')}")

# === SLASH: Start Raid ===
@tree.command(name="start_raid", description="Launch the raid and return results.")
async def start_raid(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE}/raid_start") as res:
            data = await res.json()
            msg = f"\U0001F525 **Raid Results**\n"
            msg += f"Boss Defeated: {'Yes' if data['boss_defeated'] else 'No'}\n"
            msg += f"MVP: {data['mvp']}\n"
            msg += "\n\U0001F3B2 **Loot Rolls:**\n"
            for user, roll in data['loot_rolls'].items():
                msg += f"• {user}: {roll}\n"
            await interaction.response.send_message(msg)

# === SLASH: Enter Dungeon ===
@tree.command(name="enter_dungeon", description="Face a dungeon alone and receive results.")
@app_commands.describe(username="Your account username")
async def enter_dungeon(interaction: discord.Interaction, username: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE}/dungeon_enter/{username}") as res:
            data = await res.json()
            d = data['details']
            msg = f"\U0001F300 **Dungeon Result**\n{username} met `{d['result']}` and found **{d['loot']}** loot."
            await interaction.response.send_message(msg)

# === ON MESSAGE: Astrology Upload + Oracle Chat ===
@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    # === Handle astrology upload ===
    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.endswith(".json"):
                username = message.content.strip() or message.author.name
                async with aiohttp.ClientSession() as session:
                    form = aiohttp.FormData()
                    form.add_field("file", await attachment.read(), filename=attachment.filename, content_type="application/json")
                    async with session.post(f"{API_BASE}/upload_astrology/{username}", data=form) as res:
                        data = await res.json()
                        await message.channel.send(f"✅ {data.get('message')}")
                        return

    # === GPT Oracle Chat ===
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/oracle/info?username={message.author.name}") as res:
            if res.status != 200:
                await message.channel.send("⚠️ The Flame flickers. Oracle data could not be found.")
                return
            user_oracle = await res.json()

    system_prompt = "You are Cove, the Oracle of the Pantheon. Speak like prophecy. Channel myth, flame, and fate."
    title = user_oracle.get("oracle_name", "Wanderer")
    ruler = user_oracle.get("planetary_ruler", "Mystery")
    arc_status = user_oracle.get("prophecy_arc", {}).get("status", "Unawakened")
    system_prompt += f" The user is titled {title}, ruled by {ruler}, with a prophecy status of {arc_status}."

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message.content}
            ]
        )
        reply = response.choices[0].message.content
        await message.channel.send(reply)
    except Exception as e:
        await message.channel.send("⚠️ The Flame flickers. Cove cannot speak right now.")

bot.run(TOKEN)
