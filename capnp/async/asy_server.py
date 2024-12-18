import argparse
import asyncio

import capnp
import thread_capnp


class ExampleImpl(thread_capnp.Example.Server):
    async def subscribeStatus(self, subscriber, **kwargs):
        await asyncio.sleep(0.02)
        await subscriber.status(True)
        print("subscribeStatus11")
        await self.subscribeStatus(subscriber)

    async def longRunning(self, **kwargs):
        print("longRuning11")
        await asyncio.sleep(0.1)


async def new_connection(stream):
    await capnp.TwoPartyServer(stream, bootstrap=ExampleImpl()).on_disconnect()


def parse_args():
    parser = argparse.ArgumentParser(usage="address:port")
    parser.add_argument("address", help="ADDRESS:PORT")

    return parser.parse_args()


async def main():
    host, port = parse_args().address.split(":")
    print(host, port)
    server = await capnp.AsyncIoStream.create_server(new_connection, host, port)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(capnp.run(main()))
