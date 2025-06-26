
import discord
from discord.ext import commands
import os
import random

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ROLES = ["tank", "heal", "boondps", "dps"]
SPECIAL_ROLES = ["hk", "tower", "1-3", "2-4", "s1", "s2", "s3", "s4", "mortier"]
player_roles = {}

def format_roles(data):
    return "\n".join([f"**{user}** : {', '.join(roles)}" for user, roles in data.items()]) or "Aucun joueur enregistré."

@bot.command(name="register")
async def register(ctx, *roles):
    user = str(ctx.author)
    normalized_roles = [r.lower() for r in roles]
    player_roles[user] = normalized_roles
    await ctx.send(f"{ctx.author.mention} rôles enregistrés : {', '.join(normalized_roles)}")

@bot.command(name="liste")
async def liste(ctx):
    await ctx.send("**Rôles enregistrés :**\n" + format_roles(player_roles))

@bot.command(name="generate")
async def generate(ctx):
    required_roles = {"tank": 1, "heal": 1, "boondps": 2, "dps": 6}
    special_by_boss = {
        "Boss 1": ["hk"],
        "Boss 2": ["1-3", "2-4"],
        "Boss 3": ["tower", "tower"],
        "Boss 4": ["s1", "s2", "s3", "s4"],
        "Mortier": ["mortier"],
    }

    available_players = list(player_roles.items())
    random.shuffle(available_players)

    assigned = {}
    used = set()

    for role, count in required_roles.items():
        assigned[role] = []
        for user, roles in available_players:
            if user not in used and role in roles:
                assigned[role].append(user)
                used.add(user)
                if len(assigned[role]) >= count:
                    break

    all_assigned = sum([assigned[r] for r in ["tank", "heal", "boondps"]], [])
    remaining_dps_needed = 10 - len(all_assigned)
    dps_pool = [user for user, roles in available_players if user not in used and "dps" in roles]
    assigned["dps"] = random.sample(dps_pool, min(len(dps_pool), remaining_dps_needed))
    used.update(assigned["dps"])

    special_assignments = {}
    dps_candidates = {user: roles for user, roles in player_roles.items() if "dps" in roles}
    already_assigned = set()
    for boss, specials in special_by_boss.items():
        special_assignments[boss] = []
        for spec in specials:
            possible = [p for p in dps_candidates if p not in already_assigned and spec in dps_candidates[p]]
            if possible:
                chosen = random.choice(possible)
                special_assignments[boss].append((spec, chosen))
                already_assigned.add(chosen)

    def fmt(lst): return "\n".join(f"- {r}" for r in lst) or "Aucun"

    embed = discord.Embed(title="📋 Composition de Raid GW2", color=0x00ff00)
    for role in ["tank", "heal", "boondps", "dps"]:
        embed.add_field(name=role.capitalize(), value=fmt(assigned.get(role, [])), inline=False)
    for boss, specs in special_assignments.items():
        lines = "\n".join(f"{r.upper()} → {p}" for r, p in specs)
        embed.add_field(name=f"🔹 {boss}", value=lines or "Aucun", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="helpbot")
async def helpbot(ctx):
    embed = discord.Embed(title="📖 Commandes du RaidBot", color=0x3498db)
    embed.add_field(name="!register tank dps s2 ...", value="Enregistre tes rôles (classiques + spéciaux).", inline=False)
    embed.add_field(name="!liste", value="Affiche tous les rôles enregistrés.", inline=False)
    embed.add_field(name="!generate", value="Génère automatiquement un groupe de 10 joueurs avec les rôles optimisés.", inline=False)
    await ctx.send(embed=embed)

bot.run(os.environ["DISCORD_TOKEN"])
