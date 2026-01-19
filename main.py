import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

# ===== CONFIG =====
TOKEN = "DISCORD_TOKEN"
OWNER = "lord_nova98"
PANEL_URL = "https://panel.yoursite.com"
API_KEY = "PTERODACTYL_API_KEY"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "Application/vnd.pterodactyl.v1+json",
    "Content-Type": "application/json"
}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== ASYNC API =====
async def get_servers():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{PANEL_URL}/api/client", headers=HEADERS) as r:
            data = await r.json()
            return data["data"]

async def power(server_id, signal):
    async with aiohttp.ClientSession() as session:
        await session.post(f"{PANEL_URL}/api/client/servers/{server_id}/power",
                           headers=HEADERS, json={"signal": signal})

async def stats(server_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{PANEL_URL}/api/client/servers/{server_id}/resources",
                               headers=HEADERS) as r:
            return await r.json()

async def send_console(server_id, cmd):
    async with aiohttp.ClientSession() as session:
        await session.post(f"{PANEL_URL}/api/client/servers/{server_id}/command",
                           headers=HEADERS, json={"command": cmd})

async def reinstall(server_id):
    async with aiohttp.ClientSession() as session:
        await session.post(f"{PANEL_URL}/api/client/servers/{server_id}/settings/reinstall",
                           headers=HEADERS)

# ===== UI =====
class ServerSelect(discord.ui.Select):
    def __init__(self, servers):
        options = [
            discord.SelectOption(label=s["attributes"]["name"], value=s["attributes"]["identifier"])
            for s in servers
        ]
        super().__init__(placeholder="Select a server...", options=options)

    async def callback(self, interaction):
        interaction.client.selected_server = self.values[0]
        await interaction.response.send_message(
            f"✅ Selected server: **{self.values[0]}**", ephemeral=True
        )

class ServerSelectView(discord.ui.View):
    def __init__(self, servers):
        super().__init__()
        self.add_item(ServerSelect(servers))

class ControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction):
        if interaction.user.name != OWNER:
            await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            return False
        if not hasattr(interaction.client, "selected_server"):
            await interaction.response.send_message("⚠ Select a server first.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="START", style=discord.ButtonStyle.green)
    async def start(self, interaction, _):
        await power(interaction.client.selected_server, "start")
        await interaction.response.send_message("🚀 Server Starting", ephemeral=True)

    @discord.ui.button(label="STOP", style=discord.ButtonStyle.red)
    async def stop(self, interaction, _):
        await power(interaction.client.selected_server, "stop")
        await interaction.response.send_message("🛑 Server Stopped", ephemeral=True)

    @discord.ui.button(label="RESTART", style=discord.ButtonStyle.blurple)
    async def restart(self, interaction, _):
        await power(interaction.client.selected_server, "restart")
        await interaction.response.send_message("🔄 Restarting", ephemeral=True)

    @discord.ui.button(label="KILL", style=discord.ButtonStyle.gray)
    async def kill(self, interaction, _):
        await power(interaction.client.selected_server, "kill")
        await interaction.response.send_message("☠ Force Killed", ephemeral=True)

# ===== SLASH COMMANDS =====
class Ptero(app_commands.Group):
    def __init__(self):
        super().__init__(name="ptero", description="Fast Multi-Server Manager")

    async def interaction_check(self, interaction):
        if interaction.user.name != OWNER:
            await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            return False
        return True

    # ---- FAST SERVER LIST ----
    @app_commands.command(name="servers", description="Select a server quickly")
    async def servers(self, interaction):
        await interaction.response.defer(ephemeral=True)  # immediate defer
        servers = await get_servers()  # async fetch
        await interaction.followup.send(
            "🌐 Select your server:",
            view=ServerSelectView(servers),
            ephemeral=True
        )

    @app_commands.command(name="panel", description="Open control panel for selected server")
    async def panel(self, interaction):
        embed = discord.Embed(
            title="⚡ PTERODACTYL AI MANAGER",
            description="Server Control Panel",
            color=0x00ffff
        )
        embed.set_footer(text="Make by lord_nova98")  # <-- watermark
        await interaction.response.send_message(embed=embed, view=ControlPanel(), ephemeral=True)

    @app_commands.command(name="resources", description="Show selected server resources")
    async def resources(self, interaction):
        sid = interaction.client.selected_server
        data = await stats(sid)
        r = data["attributes"]["resources"]
        embed = discord.Embed(title="📊 SERVER RESOURCES", color=0x00ff99)
        embed.add_field(name="CPU", value=f"{r['cpu_absolute']}%")
        embed.add_field(name="RAM", value=f"{round(r['memory_bytes']/1024/1024)} MB")
        embed.add_field(name="Disk", value=f"{round(r['disk_bytes']/1024/1024)} MB")
        embed.set_footer(text="Make by lord_nova98")  # <-- watermark
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="reinstall", description="Reinstall selected server")
    async def reinstall_cmd(self, interaction):
        await reinstall(interaction.client.selected_server)
        embed = discord.Embed(
            title="♻ Server Reinstall",
            description="Server reinstall started",
            color=0xffcc00
        )
        embed.set_footer(text="Make by lord_nova98")  # <-- watermark
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="console", description="Send command to selected server")
    async def console(self, interaction, command: str):
        await send_console(interaction.client.selected_server, command)
        embed = discord.Embed(
            title="📨 Command Sent",
            description=f"```{command}```",
            color=0x00ffff
        )
        embed.set_footer(text="Make by lord_nova98")  # <-- watermark
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ===== READY =====
@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game("⚡ Nova Multi Ptero AI made by lord_nova98"))
    print("🔥 FAST MULTI SERVER PTERO AI ONLINE")

bot.tree.add_command(Ptero())
bot.run(TOKEN)
