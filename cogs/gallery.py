import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button
import aiohttp
import re
import io

SCREENSHOTS_CHANNEL_ID = 1317331566472728586
VALID_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')

class Gallery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_last_image = {}

    async def validate_image(self, url: str) -> bool:
        """Check if a URL points to a valid image."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as resp:
                    return resp.status == 200 and 'image' in resp.headers.get('Content-Type', '')
        except Exception:
            return False

    async def fetch_last_image(self, channel: discord.TextChannel, user: discord.User):
        """Find the last image message with a matching footer user ID."""
        async for msg in channel.history(limit=50):
            if msg.embeds:
                embed = msg.embeds[0]
                if embed.footer and embed.footer.text == str(user.id):
                    return msg
        return False

    async def create_embed(self, user: discord.User, title="", description=""):
        """Create an embed for image uploads."""
        embed = discord.Embed(title=title, description=description)
        embed.add_field(name="", value=user.mention, inline=False)
        embed.set_footer(text=str(user.id))
        return embed

    async def create_view(self):
        """Create a view with edit and delete buttons."""
        view = View()
        view.add_item(Button(label="Edit", style=discord.ButtonStyle.primary, custom_id="edit_image_button"))
        view.add_item(Button(label="Delete", style=discord.ButtonStyle.danger, custom_id="delete_image_button"))
        return view

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != SCREENSHOTS_CHANNEL_ID:
            return

        # Handle mentions to update a previous image
        if message.mentions:
            last_image = await self.fetch_last_image(message.channel, message.author)
            if last_image and last_image.embeds:
                embed = last_image.embeds[0]
                embed.set_field_at(0, name="", value=" ".join(m.mention for m in message.mentions), inline=False)
                await last_image.edit(embed=embed)
                await message.delete()
                return

        # Handle image uploads or links
        image_url = None
        if message.attachments:
            attachment = next((a for a in message.attachments if a.filename.endswith(VALID_IMAGE_EXTENSIONS)), None)
            if attachment:
                file = discord.File(io.BytesIO(await attachment.read()), filename=attachment.filename)
            else:
                await message.delete()
                return
        elif re.match(r'https?://.*\.(jpg|jpeg|png|gif|bmp|tiff)$', message.content.lower()):
            image_url = message.content.strip()
            if not await self.validate_image(image_url):
                await message.delete()
                return
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    file = discord.File(io.BytesIO(await resp.read()), filename=image_url.split("/")[-1])
        else:
            return

        embed = await self.create_embed(message.author)
        view = await self.create_view()
        sent_msg = await message.channel.send(file=file, embed=embed, view=view)
        self.user_last_image[message.author.id] = sent_msg
        await message.delete()

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.data.get('custom_id') == "edit_image_button":
            await self.handle_edit(interaction)
        elif interaction.data.get('custom_id') == "delete_image_button":
            await self.handle_delete(interaction)

    async def handle_edit(self, interaction: discord.Interaction):
        """Handle the edit button interaction."""
        embed = interaction.message.embeds[0]
        if str(interaction.user.id) != embed.footer.text:
            await interaction.response.send_message("You can only edit your own images.", ephemeral=True)
            return

        class EditModal(Modal):
            def __init__(self, embed):
                super().__init__(title="Edit Image Details")
                self.embed = embed
                self._title = TextInput(label="Title", default=embed.title or "", required=False)
                self.description = TextInput(label="Description", default=embed.description or "", required=False, style=discord.TextStyle.paragraph)
                self.add_item(self._title)
                self.add_item(self.description)

            async def on_submit(self, interaction: discord.Interaction):
                self.embed.title = self._title.value
                self.embed.description = self.description.value
                await interaction.response.edit_message(embed=self.embed)

        await interaction.response.send_modal(EditModal(embed))

    async def handle_delete(self, interaction: discord.Interaction):
        """Handle the delete button interaction."""
        if str(interaction.user.id) != interaction.message.embeds[0].footer.text:
            await interaction.response.send_message("You can only delete your own images.", ephemeral=True)
            return
        await interaction.message.delete()
        await interaction.response.send_message("Image deleted.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Gallery(bot))
