import discord
from discord.ext import commands
import aiohttp

class Weather(commands.Cog):
    BASE_URL = "https://aviationweather.gov/api/data"

    def __init__(self, bot):
        self.bot = bot

    async def fetch_data(self, endpoint, params):
        """Fetch data from the Aviation Weather API."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_URL}/{endpoint}", params=params) as r:
                return await r.text() if r.status == 200 else None

    @commands.command()
    async def metar(self, ctx, icao: str):
        """Fetch METAR for a given ICAO code."""
        data = await self.fetch_data("metar", {"ids": icao.upper(), "format": "raw"})
        await ctx.send(f"**METAR for {icao.upper()}**:\n```{data.strip() if data else 'Not found.'}```")

    @commands.command()
    async def taf(self, ctx, icao: str):
        """Fetch TAF for a given ICAO code."""
        data = await self.fetch_data("taf", {"ids": icao.upper(), "format": "raw"})
        await ctx.send(f"**TAF for {icao.upper()}**:\n```{data.strip() if data else 'Not found.'}```")

    @commands.command()
    async def airport(self, ctx, icao: str):
        """Fetch airport information for a given ICAO code."""
        data = await self.fetch_data("airport", {"ids": icao.upper(), "format": "decoded"})
        await ctx.send(f"**Airport Info for {icao.upper()}**:\n```{data.strip() if data else 'Not found.'}```")

async def setup(bot):
    await bot.add_cog(Weather(bot))
