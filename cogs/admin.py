import discord
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", help="Deletes a specified number of messages from the current channel.")
    async def purge(self, ctx, limit: int):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You need to be an administrator to use this command.", delete_after=5)
            return

        if limit < 1:
            await ctx.send("Please specify a number greater than 0.", delete_after=5)
            return

        try:
            await ctx.message.delete()
            deleted = await ctx.channel.purge(limit=limit)
            await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages in this channel.", delete_after=5)
        except discord.HTTPException as e:
            await ctx.send(f"Failed to delete messages: {e}", delete_after=5)

async def setup(bot):
    await bot.add_cog(Admin(bot))
