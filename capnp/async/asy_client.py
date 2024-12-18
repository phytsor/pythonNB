import asyncio
import argparse
import time
import capnp

import thread_capnp


def parse_args():
    parser = argparse.ArgumentParser(usage="address:port")
    parser.add_argument("host", help="ADDRESS:PORT")

    return parser.parse_args()


class StatusSubscriber(thread_capnp.Example.StatusSubscriber.Server):
    async def status(self, value, **kwargs):
        print("status: {}".format(time.time()), value)


async def main(host):
    host, port = host.split(":")
    connection = await capnp.AsyncIoStream.create_connection(host=host, port=port)
    client = capnp.TwoPartyClient(connection)
    cap = client.bootstrap().cast_as(thread_capnp.PP)

    task = asyncio.ensure_future(cap.subscribeStatus(StatusSubscriber()))

    print("main: {}".format(time.time()))
    await cap.longRunning()
    print("main: {}".format(time.time()))
    await cap.longRunning()

    task.cancel()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(capnp.run(main(args.host)))
    print("\nfirst one completed.\n")
    #asyncio.run(capnp.run(main(args.host)))
