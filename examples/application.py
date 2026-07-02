import asyncio
import sys

sys.path.insert(0, '..')

import bonzo.smtp


class Handler(bonzo.smtp.RequestHandler):

    async def data(self):
        print(self.request)


async def main():
    application = bonzo.smtp.Application(Handler)
    application.listen(2525)
    await asyncio.Event().wait()


if __name__ == '__main__':
    asyncio.run(main())
