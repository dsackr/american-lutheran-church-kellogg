import os
import difflib
import logging
import asyncio
import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, ButtonStyle

from bot.config import (
    DISCORD_BOT_TOKEN,
    AUTHORIZED_USER_IDS,
    BOT_NAME,
    CHURCH_NAME,
    PRIMARY_DOMAIN,
    GITHUB_USERNAME,
    GITHUB_REPO,
    HERMES_MODEL,
)
from bot.agent import ALCSupportHermesAgent
from bot.github_client import ALCGitHubClient
from bot.tools import save_uploaded_asset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ALC_Support")

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!alc", intents=intents)
agent = ALCSupportHermesAgent()
gh_client = ALCGitHubClient()


def is_authorized(user_id: int) -> bool:
    if not AUTHORIZED_USER_IDS:
        return True
    return user_id in AUTHORIZED_USER_IDS


class ConfirmDeployView(ui.View):
    def __init__(self, filename: str, updated_content: str, summary: str, commit_msg: str, requester_id: int):
        super().__init__(timeout=600)
        self.filename = filename
        self.updated_content = updated_content
        self.summary = summary
        self.commit_msg = commit_msg
        self.requester_id = requester_id

    @ui.button(label="Approve & Push Live (via alckellogg)", style=ButtonStyle.success, emoji="🚀")
    async def approve_callback(self, interaction: Interaction, button: ui.Button):
        if not is_authorized(interaction.user.id):
            await interaction.response.send_message("❌ You are not authorized to approve deployments.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        status_msg = await interaction.followup.send("⚙️ Committing changes to GitHub as `alckellogg` and triggering automated Cloud Run CI/CD...")

        # 1. Commit directly to GitHub as alckellogg
        loop = asyncio.get_running_loop()
        success, msg, commit_url = await loop.run_in_executor(
            None,
            gh_client.commit_file_change,
            self.filename,
            self.updated_content,
            self.commit_msg,
        )

        if not success:
            await status_msg.edit(content=f"❌ Failed to commit to GitHub:\n`{msg}`")
            return

        embed = discord.Embed(
            title="🚀 Changes Committed to GitHub!",
            description=(
                f"**Committer:** `{GITHUB_USERNAME}`\n"
                f"**File:** `{self.filename}`\n"
                f"**Summary:** {self.summary}\n"
                f"**Commit:** [View Commit on GitHub]({commit_url})\n\n"
                f"⏳ **CI/CD Pipeline Running:** GitHub Actions is now building and deploying to Google Cloud Run (~45–60s)..."
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="American Lutheran Church • Automated CI/CD")
        await status_msg.edit(content=None, embed=embed)

        # 2. Poll for workflow completion
        for _ in range(15):
            await asyncio.sleep(6)
            run_info = await loop.run_in_executor(None, gh_client.get_latest_workflow_run)
            if run_info and run_info.get("conclusion") == "success":
                success_embed = discord.Embed(
                    title="✅ Website Update Successfully Published Live!",
                    description=(
                        f"**File:** `{self.filename}`\n"
                        f"**Summary:** {self.summary}\n\n"
                        f"🌐 **Live Website:** {PRIMARY_DOMAIN}\n"
                        f"🔗 **Commit:** [GitHub Commit]({commit_url})\n"
                        f"⚡ **Deployment Run:** [GitHub Actions Run]({run_info['html_url']})"
                    ),
                    color=discord.Color.green(),
                )
                success_embed.set_footer(text="American Lutheran Church • Serverless Google Cloud")
                await status_msg.edit(embed=success_embed)
                return
            elif run_info and run_info.get("conclusion") == "failure":
                await status_msg.edit(
                    content=f"⚠️ GitHub Actions deployment completed with error. [View Action Logs]({run_info['html_url']})"
                )
                return

        # Fallback if workflow takes longer than polling limit
        await status_msg.edit(
            content=f"✅ Changes committed! GitHub Actions pipeline is completing in background.\nLive URL: {PRIMARY_DOMAIN}"
        )

    @ui.button(label="Cancel / Reject", style=ButtonStyle.danger, emoji="❌")
    async def reject_callback(self, interaction: Interaction, button: ui.Button):
        if not is_authorized(interaction.user.id):
            await interaction.response.send_message("❌ You are not authorized to cancel.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content="🛑 Proposal cancelled. No changes were committed.",
            embed=None,
            view=self,
        )


@bot.event
async def on_ready():
    logger.info(f"{BOT_NAME} connected as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} application commands.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions

    if not (is_dm or is_mentioned):
        await bot.process_commands(message)
        return

    if not is_authorized(message.author.id):
        await message.reply(f"🔒 Access restricted. You are not on the authorized user list for {CHURCH_NAME}.")
        return

    prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()

    # Handle attached images
    asset_rel_path = None
    if message.attachments:
        att = message.attachments[0]
        if any(att.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
            img_bytes = await att.read()
            ok, saved_path = save_uploaded_asset(img_bytes, att.filename)
            if ok:
                asset_rel_path = saved_path
                # Also commit the image to GitHub
                gh_client.upload_image_asset(saved_path, img_bytes, f"upload {att.filename}")

    async with message.channel.typing():
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, agent.process_request, prompt, asset_rel_path)

    if res["type"] == "reply":
        await message.reply(res["text"])
        return

    if res["type"] == "proposal":
        fname = res["filename"]
        summary = res["summary"]
        commit_msg = res.get("commit_message", "update website content")
        new_content = res["updated_content"]

        old_content = gh_client.read_file(fname) or ""
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
            title=f"📝 Proposed Website Update: `{fname}`",
            description=f"**Pastor's / Staff Request:** {prompt}\n\n**{BOT_NAME} Summary:**\n{summary}",
            color=discord.Color.gold(),
        )

        if diff_text:
            snippet = diff_text[:1200]
            embed.add_field(name="Diff Preview", value=f"```diff\n{snippet}\n```", inline=False)

        embed.set_footer(text=f"Will commit to {GITHUB_REPO} as {GITHUB_USERNAME}")

        view = ConfirmDeployView(
            filename=fname,
            updated_content=new_content,
            summary=summary,
            commit_msg=commit_msg,
            requester_id=message.author.id,
        )

        await message.reply(
            content="Please review the proposed update below. Click **Approve & Push Live** to commit to GitHub and deploy to Cloud Run.",
            embed=embed,
            view=view,
        )


@bot.tree.command(name="status", description="Check live status of the website, GitHub repository, and CI/CD.")
async def status_command(interaction: Interaction):
    loop = asyncio.get_running_loop()
    run_info = await loop.run_in_executor(None, gh_client.get_latest_workflow_run)

    embed = discord.Embed(
        title=f"⛪ {CHURCH_NAME} — System Status",
        color=discord.Color.blue(),
    )
    embed.add_field(name="Live Website", value=f"[{PRIMARY_DOMAIN}]({PRIMARY_DOMAIN})", inline=False)
    embed.add_field(name="GitHub Repo", value=f"[{GITHUB_REPO}](https://github.com/{GITHUB_REPO})", inline=True)
    embed.add_field(name="Bot Committer", value=f"`{GITHUB_USERNAME}`", inline=True)
    embed.add_field(name="Hermes Model", value=f"`{HERMES_MODEL}`", inline=False)

    if run_info:
        status_text = f"{run_info.get('status')} ({run_info.get('conclusion') or 'in progress'})"
        embed.add_field(
            name="Latest CI/CD Deployment",
            value=f"[{run_info.get('name')}]({run_info.get('html_url')})\nStatus: `{status_text}`",
            inline=False,
        )

    embed.set_footer(text="Kellogg, Idaho • Powered by Google Cloud & Hermes")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="pages", description="List editable website files from the GitHub repository.")
async def pages_command(interaction: Interaction):
    loop = asyncio.get_running_loop()
    files = await loop.run_in_executor(None, gh_client.list_files)
    files_list = "\n".join(f"• `{f}`" for f in files)
    embed = discord.Embed(
        title="📄 Editable Website Files (GitHub)",
        description=files_list or "No files found.",
        color=discord.Color.teal(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("ERROR: DISCORD_BOT_TOKEN is not set in environment or .env file.")
        exit(1)
    bot.run(DISCORD_BOT_TOKEN)
