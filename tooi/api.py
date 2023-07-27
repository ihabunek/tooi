from tooi import Context


async def timeline(ctx: Context):
    response = await ctx.client.get("/api/v1/timelines/home/")
    response.raise_for_status()
    return response
