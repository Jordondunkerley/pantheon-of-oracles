import discord
from discord import app_commands, Embed
import aiohttp, openai, os, json
from discord.ext import commands
from dotenv import load_dotenv

# === LOAD ENV ===
from dotenv import load_dotenv
load_dotenv(dotenv_path=\"config.env\")
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

API_URL = "https://pantheon-of-oracles.onrender.com"
ADMIN_ID = 539260746471571476

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"🔥 Logged in as {bot.user} — Cove awakens.")

# === UPLOAD ASTROLOGY ===
@tree.command(name="upload_astrology_file", description="Upload your astrology chart JSON.")
@app_commands.describe(username="Your account username")
async def upload_astrology_file(interaction: discord.Interaction, username: str):
    await interaction.response.send_message("📁 Please upload your astrology .json file now.")

# === ON MESSAGE: CONVERSATION MODE ===
@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.endswith(".json"):
                # Send to backend
                username = message.content.strip() or message.author.name
                async with aiohttp.ClientSession() as session:
                    form = aiohttp.FormData()
                    form.add_field("file", await attachment.read(), filename=attachment.filename, content_type="application/json")
                    async with session.post(f"{API_URL}/upload_astrology/{username}", data=form) as res:
                        data = await res.json()
                        await message.channel.send(f"✅ {data.get('message')}")
                        return

    # GPT CONVERSATION VIA COVE
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/oracles.json") as res:
            oracles = await res.json()

    username = message.author.name
    user_oracle = next((o for o in oracles.values() if o.get("username") == username), None)

    system_prompt = "You are Cove, the dynamic Oracle of the Pantheon. Speak in mythic language and shift tone based on title, guild, and planetary ruler."
    if user_oracle:
        title = user_oracle.get("oracle_name", "Wanderer")
        ruler = user_oracle.get("planetary_ruler", "Mystery")
        status = user_oracle.get("prophecy_arc", {}).get("status", "Unawakened")
        system_prompt += f"\nThe user is titled {title}, ruled by {ruler}, and their prophecy is {status}."

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
