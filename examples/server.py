import asyncio
import sys

sys.path.insert(0, '..')

import bonzo.server


async def handle_request(request):
    print(request)
    await request.finish_async()


async def main():
    smtp_server = bonzo.server.SMTPServer(handle_request)
    smtp_server.listen(2525)
    await asyncio.Event().wait()


if __name__ == '__main__':
    asyncio.run(main())
