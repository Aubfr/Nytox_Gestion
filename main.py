from typing import Optional
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
import json

load_dotenv()
token = os.getenv("Token")

intents= discord.Intents.all()

bot = commands.Bot(command_prefix="+", intents=intents)

# CONFIG
GUILD_ID = 1403736718917501059  # ID serv
ROLE_ID = 1403813982707646554  # ID du rôle autorisé à gérer
DB_FILE = "cosmetics.json"

# Fonctions utilitaires
def load_data():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def has_role(member: discord.Member):
    return any(role.id == ROLE_ID for role in member.roles)











# /add
@bot.tree.command(name="add", description="Ajoute un cosmétique dans le stock / Add a cosmetic to the stock", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    nom="Nom du cosmétique / Cosmetic name",
    stock="Quantité en stock / Stock quantity",
    prix="Prix du cosmétique en € / Price in €",
    notif="Choisir le type de notification / Choose notification type",
    proof="Image de preuve (optionnel) / Proof image (optional)"
)
@app_commands.choices(notif=[
    app_commands.Choice(name="Pas de notification / No notification", value="none"),
    app_commands.Choice(name="@everyone", value="everyone"),
    app_commands.Choice(name="@here", value="here")
])
async def add(
    interaction: discord.Interaction,
    nom: str,
    stock: int,
    prix: float,
    notif: app_commands.Choice[str],
    proof: discord.Attachment = None
):
    if not has_role(interaction.user):
        await interaction.response.send_message("❌ Tu n'as pas la permission pour faire ça. / You do not have permission to do that.", ephemeral=True)
        return

    data = load_data()
    if nom not in data:
        data[nom] = {"stock": stock, "price": prix}
    else:
        data[nom]["stock"] = stock
        data[nom]["price"] = prix
    save_data(data)

    embed = discord.Embed(title="🛒 Restock effectué / Restock done", color=discord.Color.red())
    embed.add_field(name="Cosmétique", value=nom, inline=True)
    embed.add_field(name="Stock", value=str(stock), inline=True)
    embed.add_field(name="Prix", value=f"{prix} €", inline=True)

    embed.add_field(name="Cosmetic", value=nom, inline=True)
    embed.add_field(name="Stock", value=str(stock), inline=True)
    embed.add_field(name="Price", value=f"{prix} €", inline=True)

    embed.set_footer(text=f"Ajouté par {interaction.user.display_name} / Added by {interaction.user.display_name}")

    if proof:
        if proof.content_type and proof.content_type.startswith("image"):
            embed.set_image(url=proof.url)
        else:
            await interaction.response.send_message("❌ Le fichier fourni n'est pas une image valide. / The provided file is not a valid image.", ephemeral=True)
            return

    await interaction.response.send_message(embed=embed)

    if notif.value == "everyone":
        await interaction.channel.send(f"@everyone Nouveau stock pour **{nom}** : {stock} unités, prix : {prix}€. Allez vite faire un https://discord.com/channels/{GUILD_ID}/1403815844122726642 pour acheter !")
        await interaction.channel.send(f"New stock for **{nom}**: {stock} units, price: {prix}€. Check it out: https://discord.com/channels/{GUILD_ID}/1403815844122726642")
    elif notif.value == "here":
        await interaction.channel.send(f"@here Nouveau stock pour **{nom}** : {stock} unités, prix : {prix}€.")
        await interaction.channel.send(f"New stock for **{nom}**: {stock} units, price: {prix}€.")









# ─── Commande /setprice ───
@bot.tree.command(name="setprice", description="Définit le prix d'un cosmétique", guild=discord.Object(id=GUILD_ID))
async def setprice(interaction: discord.Interaction, nom: str, prix: float):
    if not has_role(interaction.user):
        await interaction.response.send_message("❌ Tu n'as pas la permission pour faire ça.", ephemeral=True)
        return

    data = load_data()
    if nom not in data:
        await interaction.response.send_message(f"❌ '{nom}' n'existe pas dans la base.", ephemeral=True)
        return

    data[nom]["price"] = prix
    save_data(data)

    embed = discord.Embed(title="💰 Prix modifié", color=discord.Color.red())
    embed.add_field(name="Cosmétique", value=nom, inline=True)
    embed.add_field(name="Nouveau prix", value=f"{prix}€", inline=True)
    embed.set_footer(text=f"Modifié par {interaction.user.display_name}")

    await interaction.response.send_message(embed=embed)










# ─── Commande /list ───
@bot.tree.command(name="list", description="Affiche le catalogue / Show catalog", guild=discord.Object(id=GUILD_ID))
async def list_cosmetics(interaction: discord.Interaction):
    data = load_data()

    if not data:
        await interaction.response.send_message(
            "📭 Aucun cosmétique dans le catalogue / No cosmetics in the catalog.",
            ephemeral=True
        )
        return

    embed = discord.Embed(title="📦 Catalogue / Catalog", color=discord.Color.red())
    for name, info in data.items():
        # Format FR | EN
        line = f"Stock: {info['stock']} | Price: {info['price']}€ / Stock : {info['stock']} | Prix : {info['price']}€"
        embed.add_field(name=name, value=line, inline=False)

    await interaction.response.send_message(embed=embed)







@bot.event
async def on_message(message):
    # Empêche le bot de réagir à ses propres messages
    if message.author.bot:
        return

    # Vérifie si le message commence par +rep
    if message.content.startswith("+rep"):
        parts = message.content.split(" ", 2)  # Découpe en 3 parties max
        if len(parts) < 3:
            await message.channel.send("❌ Format : +rep @membre message")
            return

        # Récupération du membre mentionné
        if not message.mentions:
            await message.channel.send("❌ Tu dois mentionner un membre.")
            return
        member = message.mentions[0]

        # Récupération du texte après la mention
        msg_content = parts[2]

        # Envoi du DM
        try:
            await member.send(f"Tu as reçu un +rep de {message.author.mention} :\n\n{msg_content}")
        except discord.Forbidden:
            await message.channel.send(f"❌ Impossible d’envoyer un DM à {member.display_name}")
            return

        # Embed de confirmation
        embed = discord.Embed(title="👍 +rep envoyé", color=discord.Color.red())
        embed.add_field(name="Destinataire", value=member.mention, inline=True)
        embed.add_field(name="Message", value=msg_content, inline=False)
        embed.set_footer(text=f"Envoyé par {message.author.display_name}")
        await message.channel.send(embed=embed)

        # Réaction ✅ sur le message original
        await message.add_reaction("✅")

    # Nécessaire pour que les autres commandes continuent de fonctionner
    await bot.process_commands(message)

@bot.tree.command(name="remove", description="Retire un nombre de cosmétique du stock", guild=discord.Object(id=GUILD_ID))
async def remove(interaction: discord.Interaction, nom: str, quantite: int):
    if not has_role(interaction.user):
        await interaction.response.send_message("❌ Tu n'as pas la permission pour faire ça.", ephemeral=True)
        return

    data = load_data()
    if nom not in data:
        await interaction.response.send_message(f"❌ Le cosmétique '{nom}' n'existe pas dans la base.", ephemeral=True)
        return

    if quantite <= 0:
        await interaction.response.send_message("❌ La quantité doit être strictement positive.", ephemeral=True)
        return

    if data[nom]["stock"] < quantite:
        await interaction.response.send_message(f"❌ Stock insuffisant pour retirer {quantite} {nom}. Stock actuel : {data[nom]['stock']}.", ephemeral=True)
        return

    data[nom]["stock"] -= quantite

    # Supprime le cosmétique si stock à 0
    if data[nom]["stock"] == 0:
        del data[nom]

    save_data(data)

    embed = discord.Embed(title="🗑️ Stock retiré", color=discord.Color.red())
    embed.add_field(name="Cosmétique", value=nom, inline=True)
    embed.add_field(name="Quantité retirée", value=str(quantite), inline=True)
    embed.add_field(name="Stock restant", value=str(data.get(nom, {'stock': 0})['stock']), inline=True)
    embed.set_footer(text=f"Retiré par {interaction.user.display_name}")

    await interaction.response.send_message(embed=embed)



@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1403736719932526665)
    if channel:
        embed = discord.Embed(
            title="🎉 Bienvenue sur le serveur ! 🎉",
            description=f"Salut {member.mention}, heureux de t’avoir avec nous !",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text="Amuse-toi bien parmi nous 😄")
        
        await channel.send(embed=embed)



    
@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Slash commands synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur sync : {e}")

bot.run(token)