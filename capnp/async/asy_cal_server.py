import asyncio
import capnp
import argparse

import calculator_capnp  # type:ignore


def parse_args():
    parser = argparse.ArgumentParser(usage="address:port")
    parser.add_argument("address")

    return parser.parse_args()


async def evaluate_impl(expression, params=None):
    which = expression.which()
    print("evaluate_impl which: ", which)

    if which == "literal":
        return expression.literal
    elif which == "previousResult":
        return (await expression.previousResult.read()).value
    elif which == "parameter":
        assert expression.parameter < len(params)
        print("parameter: ", params, type(params))
        return params[expression.parameter]
    elif which == "call":
        call = expression.call  # capnp.lib.capnp._DynamicStructReader
        func = call.function  # <capnp.lib.capnp._DynamicCapabilityClient

        paramPromises = [
            evaluate_impl(param, params) for param in call.params
        ]  # coroutine list
        vals = await asyncio.gather(*paramPromises)  # literal (Float64) list
        print("vals: ", vals, type(vals))
        fc = func.call(vals)
        print("fc: ", fc, type(fc))
        result = await fc
        return result.value
    else:
        raise ValueError("Unknown expression type: " + which)


class ValueImpl(calculator_capnp.Calculator.Value.Server):
    def __init__(self, value):
        self.value = value

    async def read(self, **kwargs):
        return self.value


class FunctionImple(calculator_capnp.Calculator.Function.Server):
    def __init__(self, paramCount, body):  # body - capnp.lib.capnp._DynamicStructReader
        self.paramCount = paramCount
        self.body = body.as_builder()  # capnp.lib.capnp._DynamicStructBuilder

    async def call(self, params, **kwargs):
        assert len(params) == self.paramCount
        return await evaluate_impl(self.body, params)


class OperatorImpl(calculator_capnp.Calculator.Function.Server):
    def __init__(self, op):
        self.op = op

    async def call(self, params, **kwagrs):  # client getOperator await时才会调用
        assert len(params) == 2
        op = self.op

        if op == "add":
            return params[0] + params[1]
        elif op == "subtract":
            return params[0] - params[1]
        elif op == "multiply":
            return params[0] * params[1]
        elif op == "devide":
            return params[0] / params[1]
        else:
            raise ValueError("Unknown operator.")


class CalculatorImpl(calculator_capnp.Calculator.Server):
    async def evaluate(self, expression, **kwargs):
        return ValueImpl(await evaluate_impl(expression))

    async def defFunction(self, paramCount, body: Exception, **kwargs):
        return FunctionImple(paramCount, body)

    async def getOperator(self, op, **kwagrs):
        return OperatorImpl(op)


async def new_connection(stream):
    await capnp.TwoPartyServer(stream, bootstrap=CalculatorImpl()).on_disconnect()


async def main():
    host, port = parse_args().address.split(":")
    server = await capnp.AsyncIoStream.create_server(new_connection, host, port)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(capnp.run(main()))
