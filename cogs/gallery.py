import discord, re, aiohttp, asyncio
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button

SCREENSHOTS_CHANNEL_ID = 1317331566472728586

VALID_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')

class Gallery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_image_valid(self, url: str) -> bool:
        """Check if the image URL is valid and downloadable"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as response:
                    if response.status == 200 and 'image' in response.headers.get('Content-Type', ''):
                        return True
        except Exception as e:
            print(f"Error validating image URL: {e}")
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages in the screenshots channel"""
        if message.author == self.bot.user:
            return

        if message.channel.id == SCREENSHOTS_CHANNEL_ID:
            embed = discord.Embed(title=None, description=None)
            tags = "None"

            if message.attachments:
                attachment = next(
                    (attachment for attachment in message.attachments if attachment.filename.endswith(VALID_IMAGE_EXTENSIONS)), 
                    None
                )
                if attachment:
                    embed.set_image(url=attachment.url)
                else:
                    await message.delete()
                    return
            elif re.match(r'https?://.*\.(jpg|jpeg|png|gif|bmp|tiff)$', message.content.lower()):
                image_url = message.content.strip()

                if not await self.is_image_valid(image_url):
                    invalid_msg = await message.channel.send(
                        f"Invalid image link: {image_url}. Please provide a valid image URL or upload an image.",
                        delete_after=5,
                    )
                    await invalid_msg.delete(delay=5)
                    return

                embed.set_image(url=image_url)
            else:
                invalid_msg = await message.channel.send(
                    f"Invalid image link: {message.content}. Please provide a valid image URL or upload an image.",
                    delete_after=5,
                )
                await invalid_msg.delete(delay=5)
                return

            embed.set_footer(text=f"Publisher: {message.author.id}")
            message_content = f"Publisher: {message.author.mention}"

            if tags != "None":
                message_content += f"\n**Tags:** {tags}"

            view = View()
            view.add_item(Button(label="Edit", style=discord.ButtonStyle.primary, custom_id="edit_image_button"))
            await message.channel.send(content=message_content, embed=embed, view=view)

            await message.delete()

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle interactions with buttons (Edit button)"""
        if interaction.data.get('custom_id') == 'edit_image_button':
            await self.handle_edit_button_click(interaction)

    async def handle_edit_button_click(self, interaction: discord.Interaction):
        """Handle the edit button interaction"""
        embed = interaction.message.embeds[0]
        footer_text = embed.footer.text if embed.footer else ""

        if not footer_text or "Publisher:" not in footer_text:
            await interaction.response.send_message(
                "This image doesn't have a valid publisher, so it can't be edited.",
                ephemeral=True,
            )
            return

        try:
            _, author_id_str = footer_text.split("Publisher: ")
            author_id = int(author_id_str.strip())
            if interaction.user.id != author_id:
                await interaction.response.send_message(
                    "You can only edit your own image.",
                    ephemeral=True,
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "Invalid footer format. The publisher information is missing or incorrect.",
                ephemeral=True,
            )
            return

        title = embed.title or ""
        description = embed.description or ""

        tags = None
        if interaction.message.content:
            match = re.search(r"\*\*Tags:\*\* (.+)", interaction.message.content)
            if match:
                tags = match.group(1)

        tags = tags or "None"

        class EditModal(Modal):
            def __init__(self, embed: discord.Embed):
                super().__init__(title="Edit Image Information")
                self._title = TextInput(label="Title", placeholder="Enter the title", default=title, required=False)
                self.description = TextInput(label="Description", placeholder="Enter the description", style=discord.TextStyle.paragraph, default=description, required=False)
                self.tags = TextInput(label="Tags", placeholder="Enter tags (mention users with @)", style=discord.TextStyle.paragraph, default=tags, required=False)
                self.embed = embed
                self.add_item(self._title)
                self.add_item(self.description)
                self.add_item(self.tags)

            async def on_submit(self, interaction: discord.Interaction):
                title = self._title.value or None
                description = self.description.value or None
                tags = self.tags.value or "None"

                if title:
                    self.embed.title = title
                if description:
                    self.embed.description = description

                if tags != "None":
                    tags = re.sub(r"@([a-zA-Z0-9_]+)", r"<@!\1>", tags)

                updated_message_content = f"Publisher: {interaction.user.mention}"
                if tags != "None":
                    updated_message_content += f"\n**Tags:** {tags}"

                await interaction.response.edit_message(embed=self.embed, content=updated_message_content)

        await interaction.response.send_modal(EditModal(embed))

    @commands.command(name="clean", help="Clean up all messages in the screenshots channel.")
    async def clean_up_channel(self, ctx):
        """Clean up messages in the screenshots channel"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You need to be an administrator to use this command.", delete_after=5)
            return

        channel = self.bot.get_channel(SCREENSHOTS_CHANNEL_ID)
        if channel:
            await ctx.send("Cleaning up channel...", delete_after=5)
            async for message in channel.history(limit=100):
                if message.author != self.bot.user:
                    await message.delete()
                    await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(Gallery(bot))
