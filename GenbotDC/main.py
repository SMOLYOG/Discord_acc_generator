import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import time
import random
import requests

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
COOLDOWN_FILE = "cooldowns.json"
ACCOUNTS_FOLDER = "accounts"


# Utility functions
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_cooldowns():
    if not os.path.exists(COOLDOWN_FILE):
        return {"users": {}, "seconds": 300}
    with open(COOLDOWN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cooldowns(data):
    with open(COOLDOWN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def has_role(user: discord.Member, role_name: str) -> bool:
    return any(role.name.lower() == role_name.lower() for role in user.roles)


if not os.path.exists(ACCOUNTS_FOLDER):
    os.makedirs(ACCOUNTS_FOLDER)


@bot.tree.command(name="add_list",
                  description="Add a new list from a GitHub link")
@app_commands.describe(name="List name", link="GitHub raw link with accounts")
async def add_list(interaction: discord.Interaction, name: str, link: str):
    if not has_role(interaction.user, "genadm"):
        await interaction.response.send_message(
            "Only genadm role can do that.", ephemeral=True)
        return

    data = load_data()
    if name in data:
        await interaction.response.send_message(
            f"List `{name}` already exists.", ephemeral=True)
        return

    data[name] = link
    save_data(data)

    try:
        r = requests.get(link)
        r.raise_for_status()
        with open(f"{ACCOUNTS_FOLDER}/{name}.txt", "w", encoding="utf-8") as f:
            f.write(r.text.strip())
    except Exception as e:
        data.pop(name, None)
        save_data(data)
        await interaction.response.send_message(f"Failed to sync: {e}",
                                                ephemeral=True)
        return

    embed = discord.Embed(
        title="List added ✅",
        description=f"List **{name}** is now available and synced.",
        color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="del_list", description="Remove a list")
@app_commands.describe(name="List name")
async def del_list(interaction: discord.Interaction, name: str):
    if not has_role(interaction.user, "genadm"):
        await interaction.response.send_message(
            "Only genadm role can do that.", ephemeral=True)
        return

    data = load_data()
    if name not in data:
        await interaction.response.send_message(
            f"No list named `{name}` found.", ephemeral=True)
        return

    data.pop(name)
    save_data(data)

    file_path = f"{ACCOUNTS_FOLDER}/{name}.txt"
    if os.path.exists(file_path):
        os.remove(file_path)

    embed = discord.Embed(title="List removed 🗑️",
                          description=f"List **{name}** has been deleted.",
                          color=discord.Color.red())
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="lists", description="See all available lists")
async def lists(interaction: discord.Interaction):
    data = load_data()
    if not data:
        await interaction.response.send_message(
            "No lists available right now.", ephemeral=True)
        return

    embed = discord.Embed(title="Available Lists 📋",
                          color=discord.Color.blurple())
    for name in data:
        file_path = f"{ACCOUNTS_FOLDER}/{name}.txt"
        count = 0
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                count = len(
                    [line for line in f.read().splitlines() if line.strip()])
        embed.add_field(name=name, value=f"{count} accounts", inline=True)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="gen", description="Get an account from a list")
@app_commands.describe(name="List name")
async def gen(interaction: discord.Interaction, name: str):
    user = interaction.user
    data = load_data()
    cooldowns = load_cooldowns()
    now = time.time()

    if not has_role(user, "gen") and not has_role(user, "genadm"):
        await interaction.response.send_message(
            "You need the gen or genadm role.", ephemeral=True)
        return

    if has_role(user, "gen") and not has_role(user, "genadm"):
        last_used = cooldowns["users"].get(str(user.id), 0)
        cooldown = cooldowns.get("seconds", 300)
        if now - last_used < cooldown:
            remaining = int(cooldown - (now - last_used))
            await interaction.response.send_message(
                f"Hold on! Wait **{remaining}s** before generating again.",
                ephemeral=True)
            return

    if name not in data:
        await interaction.response.send_message("That list doesn't exist.",
                                                ephemeral=True)
        return

    file_path = f"{ACCOUNTS_FOLDER}/{name}.txt"
    if not os.path.exists(file_path):
        await interaction.response.send_message(
            "Couldn't find local file. Try re-syncing.", ephemeral=True)
        return

    with open(file_path, "r", encoding="utf-8") as f:
        accounts = [
            line.strip() for line in f.read().splitlines() if line.strip()
        ]

    if not accounts:
        await interaction.response.send_message(
            "Looks like this list is empty.", ephemeral=True)
        return

    account = random.choice(accounts)
    accounts.remove(account)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(accounts))

    try:
        await user.send(f"Here's your **{name}** account:\n`{account}`")
        embed = discord.Embed(
            title="Check your DMs ✅",
            description=f"Account from **{name}** has been sent to you.",
            color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.Forbidden:
        embed = discord.Embed(
            title="DMs are closed ❌",
            description=
            "I couldn't DM you. Please check your privacy settings.",
            color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if has_role(user, "gen") and not has_role(user, "genadm"):
        cooldowns["users"][str(user.id)] = now
        save_cooldowns(cooldowns)


@bot.tree.command(name="stock",
                  description="Check how many accounts are left per list")
async def stock(interaction: discord.Interaction):
    data = load_data()
    if not data:
        await interaction.response.send_message("No lists found.",
                                                ephemeral=True)
        return

    embed = discord.Embed(title="Stock Check 📦", color=discord.Color.green())
    for name in data:
        file_path = f"{ACCOUNTS_FOLDER}/{name}.txt"
        count = 0
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                count = len(
                    [line for line in f.read().splitlines() if line.strip()])
        embed.add_field(name=name, value=f"{count}", inline=True)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="cooldown",
                  description="Set cooldown in seconds (admin only)")
@app_commands.describe(seconds="How long users have to wait between gens")
async def cooldown(interaction: discord.Interaction, seconds: int):
    if not has_role(interaction.user, "genadm"):
        await interaction.response.send_message(
            "Only genadm role can change cooldown.", ephemeral=True)
        return

    if seconds < 0 or seconds > 86400:
        await interaction.response.send_message(
            "Cooldown must be between 0 and 86400 seconds.", ephemeral=True)
        return

    cooldowns = load_cooldowns()
    cooldowns["seconds"] = seconds
    save_cooldowns(cooldowns)

    await interaction.response.send_message(
        f"Cooldown set to {seconds} seconds. ⏱️", ephemeral=True)


@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Command sync failed: {e}")


bot.run(
    "TOKEN_HERE")
