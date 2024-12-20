import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone

class Clock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 123456789012345678  # Replace with your static channel ID
        self.update_clock.start()

    @tasks.loop(minutes=1)
    async def update_clock(self):
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            utc_time = datetime.now(timezone.utc).strftime("%H:%M UTC")
            await channel.edit(name=f"Time: {utc_time}")

    @update_clock.before_loop
    async def before_clock(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Clock(bot))
