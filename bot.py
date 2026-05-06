import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

RESP_STAFF_ID = 1501273305175294213
RESP_SUPPORT_ID = 1501574741750710302

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

candidatures = {}
ticket_role = None

# =========================================================
# READY
# =========================================================
@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")

# =========================================================
# CONFIG ROLE TICKETS
# =========================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def setticketrole(ctx, role: discord.Role):
    global ticket_role
    ticket_role = role.id
    await ctx.send(f"✅ rôle tickets configuré : {role.name}")

def is_ticket_staff(member):
    return ticket_role and any(r.id == ticket_role for r in member.roles)

# =========================================================
# 📌 NOUVELLE COMMANDE TICKETS
# =========================================================
@bot.command()
async def ticket(ctx):
    embed = discord.Embed(
        title="🎫 SUPPORT NOVA ACADEMIA",
        description="""
Choisis une raison :

❓ Question / Aide  
🚨 Report joueur  
🛡️ Report staff  
📌 Autre
        """,
        color=discord.Color.blurple()
    )

    await ctx.send(embed=embed, view=TicketView())

# =========================================================
# 🎫 MENU TICKET
# =========================================================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.select(
        placeholder="Faire un choix",
        options=[
            discord.SelectOption(label="Question / Aide", value="help"),
            discord.SelectOption(label="Report joueur", value="report_player"),
            discord.SelectOption(label="Report staff", value="report_staff"),
            discord.SelectOption(label="Autre", value="other"),
        ]
    )
    async def callback(self, interaction, select):

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="tickets")

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category
        )

        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await channel.set_permissions(guild.default_role, read_messages=False)

        await channel.send("🎫 ticket ouvert", view=TicketControlView())

        await interaction.response.send_message("✔ ticket créé", ephemeral=True)

# =========================================================
# 🎛️ PANEL TICKET INTERNE
# =========================================================
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green)
    async def claim(self, interaction, button):

        if not is_ticket_staff(interaction.user):
            return await interaction.response.send_message("❌ interdit", ephemeral=True)

        await interaction.channel.send(f"🟢 claim par {interaction.user.mention}")

    @discord.ui.button(label="Add", style=discord.ButtonStyle.blurple)
    async def add(self, interaction, button):

        if not is_ticket_staff(interaction.user):
            return await interaction.response.send_message("❌ interdit", ephemeral=True)

        await interaction.response.send_message("➕ mentionne un utilisateur", ephemeral=True)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, interaction, button):

        await generate_pdf(interaction.channel.name, "ticket fermé")
        await interaction.channel.delete()

# =========================================================
# 📄 PDF
# =========================================================
def generate_pdf(name, content):
    filename = f"{name}.pdf"
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    story = [
        Paragraph(name, styles["Title"]),
        Spacer(1, 12),
        Paragraph(content, styles["Normal"])
    ]

    doc.build(story)
    return filename

# =========================================================
# 👮 STAFF PANEL
# =========================================================
@bot.command()
async def staff(ctx):

    embed = discord.Embed(
        title="👮 Recrutement Modérateur",
        description="""
📌 CONDITIONS :

- 15 ans minimum  
- Micro fonctionnel  
- PC obligatoire  
- 1h/jour minimum  
- Bonne orthographe  
- 1000 minutes in-game  
- Sérieux et mature  
- Gestion du RP et conflits  
        """,
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed, view=ApplyView("staff"))

# =========================================================
# 🧑‍💻 SUPPORT PANEL
# =========================================================
@bot.command()
async def support(ctx):

    embed = discord.Embed(
        title="🧑‍💻 Recrutement Support",
        description="""
📌 CONDITIONS :

- 15 ans minimum  
- Micro fonctionnel  
- 1h/jour minimum  
- Bonne orthographe  
- Patient et neutre  
- Aide claire aux joueurs  
        """,
        color=discord.Color.green()
    )

    await ctx.send(embed=embed, view=ApplyView("support"))

# =========================================================
# BOUTON CANDIDATURE
# =========================================================
class ApplyView(discord.ui.View):
    def __init__(self, type_):
        super().__init__()
        self.type_ = type_

    @discord.ui.button(label="Candidater", style=discord.ButtonStyle.green)
    async def apply(self, interaction, button):
        await start_candidature(interaction.user, self.type_)
        await interaction.response.send_message("📩 regarde tes DM", ephemeral=True)

# =========================================================
# CANDIDATURE
# =========================================================
async def start_candidature(user, type_):

    if type_ == "staff":
        questions = [
            "Pseudo Roblox ?",
            "Pseudo Discord ?",
            "ID Discord ?",
            "Âge ?",
            "Pourquoi modérateur ?",
            "Comment gérer un joueur qui casse le RP ?",
            "Comment gérer un conflit ?",
            "Comment rester calme ?",
            "Tes disponibilités ?"
        ]
        role_id = RESP_STAFF_ID

    else:
        questions = [
            "Pseudo Roblox ?",
            "Pseudo Discord ?",
            "ID Discord ?",
            "Âge ?",
            "Pourquoi support ?",
            "Comment gérer une insulte ?",
            "Comment aider un joueur ?",
            "Comment rester neutre ?",
            "Orthographe correcte ?",
            "Disponibilités ?"
        ]
        role_id = RESP_SUPPORT_ID

    candidatures[user.id] = {
        "type": type_,
        "step": 0,
        "q": questions,
        "a": [],
        "role_id": role_id
    }

    await user.send("📩 Début candidature")
    await user.send(questions[0])

# =========================================================
# DM SYSTEM
# =========================================================
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):

        if message.author.id in candidatures:

            data = candidatures[message.author.id]

            data["a"].append(message.content)
            data["step"] += 1

            if data["step"] < len(data["q"]):
                await message.channel.send(data["q"][data["step"]])

            else:
                await message.channel.send("✅ candidature envoyée")

                guild = bot.get_guild(GUILD_ID)
                role = guild.get_role(data["role_id"])

                content = "\n".join(
                    f"{q} : {a}"
                    for q, a in zip(data["q"], data["a"])
                )

                pdf = generate_pdf(f"{message.author}", content)
                file = discord.File(pdf)

                embed = discord.Embed(
                    title="📄 Nouvelle candidature",
                    description=f"Utilisateur : {message.author.mention}",
                    color=discord.Color.orange()
                )

                for member in role.members:
                    try:
                        await member.send(embed=embed, file=file)
                    except:
                        pass

                del candidatures[message.author.id]

    await bot.process_commands(message)

# =========================================================
# RUN
# =========================================================
bot.run(TOKEN)