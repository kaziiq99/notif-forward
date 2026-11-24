import asyncio
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent, GiftEvent


async def main():
    USERNAME = "@playgamesua94"

    client = TikTokLiveClient(unique_id=USERNAME)

    @client.on(ConnectEvent)
    async def on_connect(event: ConnectEvent):
        print(f"[+] Connected: {USERNAME}")
        print(f"[+] Room ID: {client.room_id}")

    @client.on(CommentEvent)
    async def on_comment(event: CommentEvent):
        print(f"[chat] {event.user.nickname}: {event.comment}")

    @client.on(GiftEvent)
    async def on_gift(event: GiftEvent):
        print(f"[gift] {event.user.nickname}: {event.gift.name}")

    await client.connect()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
