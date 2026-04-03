import discord
from discord.ext import commands
import asyncio
import re
from dotenv import load_dotenv
import os
from flask import Flask
import threading
import os
import psutil
import time
import platform
import sys
import datetime

# Flask app for Railway's health checks
flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    return "Bot is running!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))

# Start Flask in a background thread
threading.Thread(target=run_flask, daemon=True).start()

# ---------------- LOAD ENV ----------------
load_dotenv()  # Loads .env file
TOKEN = os.getenv("TOKEN")  # Reads TOKEN from .env

if not TOKEN:
    raise ValueError("❌ TOKEN not found in .env file")

# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)
start_time=time.time()
# ---------------- READY EVENT ----------------
@bot.event
async def on_ready():
    print(f"[INFO] Logged in as {bot.user}")
    print(f"[INFO] Bot ID: {bot.user.id}")
    print("[INFO] Bot is ready\n")

# ---------------- PING ----------------
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! 🏓 {latency}ms")

# ---------------- CHANNEL COMMAND GROUP ----------------
@bot.group(invoke_without_command=True)
async def ch(ctx):
    await ctx.send(
        "Commands:\n"
        "`!ch create :CATEGORY: channel1,channel2`\n"
        "`!ch edit :CATEGORY: channel1,channel2`\n"
        "`!ch add :CATEGORY: channel1,channel2`"
    )

# ---------------- CREATE CATEGORY + CHANNELS ----------------
@ch.command()
@commands.has_permissions(manage_channels=True)
async def create(ctx, *, args):
    match = re.match(r":(.+?):\s*(.+)", args)
    if not match:
        return await ctx.send("❌ Format:\n`!ch create :CATEGORY: channel1,channel2`")
    category_name = match.group(1).strip()
    channel_list = [c.strip() for c in match.group(2).split(",") if c.strip()]
    if len(channel_list) > 50:
        return await ctx.send("❌ Maximum **50 channels** allowed.")
    category = await ctx.guild.create_category(category_name)
    for name in channel_list:
        await ctx.guild.create_text_channel(name, category=category)
    await ctx.send(f"✅ Created **{category_name}** with {len(channel_list)} channels.")

# ---------------- EDIT CHANNELS ----------------
@ch.command()
@commands.has_permissions(manage_channels=True)
async def edit(ctx, *, args):
    match = re.match(r":(.+?):\s*(.+)", args)
    if not match:
        return await ctx.send("❌ Format:\n`!ch edit :CATEGORY: channel1,channel2`")
    category_name = match.group(1).strip()
    channel_list = [c.strip() for c in match.group(2).split(",") if c.strip()]
    if len(channel_list) > 50:
        return await ctx.send("❌ Maximum **50 channels** allowed.")
    category = discord.utils.get(ctx.guild.categories, name=category_name)
    if not category:
        return await ctx.send("❌ Category not found.")
    for channel in category.channels:
        await channel.delete()
    for name in channel_list:
        await ctx.guild.create_text_channel(name, category=category)
    await ctx.send(f"✏️ Updated **{category_name}** with {len(channel_list)} channels.")

# ---------------- ADD CHANNELS ----------------
@ch.command()
@commands.has_permissions(manage_channels=True)
async def add(ctx, *, args):
    match = re.match(r":(.+?):\s*(.+)", args)
    if not match:
        return await ctx.send("❌ Format:\n`!ch add :CATEGORY: channel1,channel2`")
    category_name = match.group(1).strip()
    channel_list = [c.strip() for c in match.group(2).split(",") if c.strip()]
    if len(channel_list) > 50:
        return await ctx.send("❌ Maximum **50 channels** allowed.")
    category = discord.utils.get(ctx.guild.categories, name=category_name)
    if not category:
        return await ctx.send("❌ Category not found.")
    created = []
    for name in channel_list:
        channel = await ctx.guild.create_text_channel(name, category=category)
        created.append(channel.mention)
    await ctx.send(f"➕ Added **{len(created)} channels** to **{category_name}**")

# ---------------- ROLE COMMAND GROUP ----------------
@bot.group(invoke_without_command=True)
async def roles(ctx):
    await ctx.send("Commands:\n`!roles create role1,role2,role3`")

# ---------------- CREATE ROLES ----------------
@roles.command()
@commands.has_permissions(manage_roles=True)
async def create(ctx, *, role_names):
    role_list = [r.strip() for r in role_names.split(",") if r.strip()]
    if len(role_list) > 50:
        return await ctx.send("❌ Maximum **50 roles** allowed at once.")
    created = []
    for role_name in role_list:
        role = await ctx.guild.create_role(name=role_name)
        created.append(role.name)
    await ctx.send(f"✅ Created **{len(created)} roles**:\n" + "\n".join(created))


    @bot.command()
    @commands.has_permissions(manage_channels=True)
    async def ch(ctx, action: str, category_name: str):
        if action.lower() == "delete":
            category = discord.utils.get(ctx.guild.categories, name=category_name)

        if not category:
            await ctx.send("Category not found.")
            return

        # Delete all channels inside the category
        for channel in category.channels:
            await channel.delete()

        # Delete the category itself
        await category.delete()

        await ctx.send(f"Deleted category `{category_name}` and all its channels.")

# ---------------- RUN BOT ----------------
@bot.command(name='status')
async def status(ctx):
    """Shows detailed bot status"""

    # --- Latency ---
    latency = round(bot.latency * 1000)  # ms

    # --- Servers ---
    guild_count = len(bot.guilds)

    # --- Shards ---
    if bot.shard_count:
        shard_count = bot.shard_count
        shard_info = f"{shard_count} shards"
        if ctx.guild:
            shard_info += f" (this guild: shard {ctx.guild.shard_id})"
    else:
        shard_info = "No sharding"

    # --- Memory usage (RSS) ---
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024

    # --- CPU usage ---
    cpu_percent = process.cpu_percent(interval=0.1)

    # --- Uptime ---
    uptime_seconds = time.time() - start_time
    uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))

    # --- Versions ---
    python_version = platform.python_version()
    discord_py_version = discord.__version__

    # --- Build Embed ---
    embed = discord.Embed(
        title="🤖 Bot Status",
        color=discord.Color.green()
    )
    embed.add_field(name="⏱️ Latency", value=f"{latency} ms", inline=True)
    embed.add_field(name="🏰 Servers", value=f"{guild_count}", inline=True)
    embed.add_field(name="🗂️ Shards", value=shard_info, inline=True)
    embed.add_field(name="💾 Memory", value=f"{memory_mb:.2f} MB", inline=True)
    embed.add_field(name="⚙️ CPU", value=f"{cpu_percent:.1f}%", inline=True)
    embed.add_field(name="⏲️ Uptime", value=uptime_str, inline=True)
    embed.add_field(name="🐍 Python", value=python_version, inline=True)
    embed.add_field(name="📦 discord.py", value=discord_py_version, inline=True)

    await ctx.send(embed=embed)


bot.run(TOKEN)
