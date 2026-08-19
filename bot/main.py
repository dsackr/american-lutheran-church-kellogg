import os
import io
import difflib
import logging
import asyncio
import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, ButtonStyle

from bot.config import (
    DISCORD_BOT_TOKEN,
    AUTHORIZED_USER_IDS,
    HERMES_MODEL,
    REPO_PATH,
    CLOUD_RUN_SERVICE,
)
from bot.agent import HermesWebmasterAgent
from bot.tools import (
    read_website_file,
    apply_file_modification,
    save_uploaded_asset,
    deploy_cloud_run,
    list_website_files,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ALC_WebmasterBot")

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
agent = HermesWebmasterAgent()


def is_authorized(user_id: int) -> bool:
    if not AUTHORIZED_USER_IDS:
        return True
    return user_id in AUTHORIZED_USER_IDS


class ConfirmDeployView(ui.View):
    def __init__(self, filename: str, updated_content: str, summary: str, requester_id: int):
        super().__init__(timeout=600)
        self.filename = filename
        self.updated_content = updated_content
        self.summary = summary
        self.requester_id = requester_id

    @ui.button(label="Approve & Deploy Live", style=ButtonStyle.success, emoji="🚀")
    async def approve_callback(self, interaction: Interaction, button: ui.Button):
        if not is_authorized(interaction.user.id):
            await interaction.response.send_message("❌ You are not authorized to approve deployments.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        status_msg = await interaction.followup.send("⚙️ Applying changes and deploying to Google Cloud Run... (takes ~30-45s)")

        # 1. Apply file modification
        success, diff, err = apply_file_modification(self.filename, self.updated_content)
        if not success:
            await status_msg.edit(content=f"❌ Failed to write file: {err}")
            return

        # 2. Trigger Cloud Run deploy
        deploy_ok, deploy_msg = deploy_cloud_run()
        if deploy_ok:
            embed = discord.Embed(
                title="✅ Website Update Successfully Published!",
                description=f"**File Updated:** `{self.filename}`\n**Summary:** {self.summary}\n\n🌐 **Live URL:** https://americanlutheranchurchkellogg.com",
                color=discord.Color.green(),
            )
            embed.set_footer(text="American Lutheran Church • Kellogg, ID • Serverless GCP")
            await status_msg.edit(content=None, embed=embed)
        else:
            await status_msg.edit(content=f"⚠️ Files updated, but deployment failed:\n```{deploy_msg[:1500]}```")

    @ui.button(label="Reject & Cancel", style=ButtonStyle.danger, emoji="❌")
    async def reject_callback(self, interaction: Interaction, button: ui.Button):
        if not is_authorized(interaction.user.id):
            await interaction.response.send_message("❌ You are not authorized to cancel.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="🛑 Proposal was cancelled. No changes were applied.", embed=None, view=self)


@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} application commands.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Check if bot is mentioned or DM
    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions

    if not (is_dm or is_mentioned):
        await bot.process_commands(message)
        return

    if not is_authorized(message.author.id):
        await message.reply("🔒 Sorry, you are not authorized to make website updates for American Lutheran Church.")
        return

    # Strip mention from prompt
    prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()

    # Handle image attachment if present
    asset_path = None
    if message.attachments:
        att = message.attachments[0]
        if any(att.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
            img_bytes = await att.read()
            ok, saved_rel_path = save_uploaded_asset(img_bytes, att.filename)
            if ok:
                asset_path = saved_rel_path

    async with message.channel.typing():
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, agent.process_request, prompt, asset_path)

    if res["type"] == "reply":
        await message.reply(res["text"])
        return

    if res["type"] == "proposal":
        fname = res["filename"]
        summary = res["summary"]
        new_content = res["updated_content"]

        # Generate preview diff
        old_content = read_website_file(fname) or ""
        diff_lines = list(
            difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{fname}",
                tofile=f"b/{fname}",
                n=2,
            )
        )
        diff_text = "".join(diff_lines)

        embed = discord.Embed(
            title=f"📝 Proposed Website Update: {fname}",
            description=f"**Pastor's / Staff Request:** {prompt}\n\n**Hermes Agent Summary:**\n{summary}",
            color=discord.Color.gold(),
        )

        if diff_text:
            snippet = diff_text[:1200]
            embed.add_field(name="Code Diff Preview", value=f"```diff\n{snippet}\n```", inline=False)

        view = ConfirmDeployView(
            filename=fname,
            updated_content=new_content,
            summary=summary,
            requester_id=message.author.id,
        )

        await message.reply(
            content="Please review the proposed change below. Click **Approve & Deploy Live** to publish immediately to Google Cloud Run.",
            embed=embed,
            view=view,
        )


@bot.tree.command(name="status", description="Check live status of the church website and Cloud Run deployment.")
async def status_command(interaction: Interaction):
    embed = discord.Embed(
        title="⛪ American Lutheran Church — Web Status",
        color=discord.Color.blue(),
    )
    embed.add_field(name="Primary Domain", value="[americanlutheranchurchkellogg.com](https://americanlutheranchurchkellogg.com)", inline=True)
    embed.add_field(name="Short Domain", value="[alckellogg.com](https://alckellogg.com) (Redirects)", inline=True)
    embed.add_field(name="Cloud Run Service", value=f"`{CLOUD_RUN_SERVICE}`", inline=True)
    embed.add_field(name="Hermes Model", value=f"`{HERMES_MODEL}`", inline=False)
    embed.set_footer(text="Kellogg, ID • Powered by Google Cloud & Hermes")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="pages", description="List editable website pages and templates.")
async def pages_command(interaction: Interaction):
    files = list_website_files()
    files_list = "\n".join(f"• `{f}`" for f in files)
    embed = discord.Embed(
        title="📄 Editable Website Files",
        description=files_list or "No editable files found.",
        color=discord.Color.teal(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN is not set in environment or .env file.")
        exit(1)
    bot.run(DISCORD_BOT_TOKEN)
