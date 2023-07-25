import httpx


async def timeline(client: httpx.AsyncClient):
    response = await client.get("/api/v1/timelines/home/")
    response.raise_for_status()
    return response
