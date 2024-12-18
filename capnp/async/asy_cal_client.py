import asyncio
import capnp
import argparse

import calculator_capnp  # type:ignore


def parse_args():
    parser = argparse.ArgumentParser(usage="host:port")
    parser.add_argument("host")

    return parser.parse_args()


async def main(connection):
    client = capnp.TwoPartyClient(connection)
    calculator = client.bootstrap().cast_as(calculator_capnp.Calculator)

    ### Expression literal
    result_promise = await calculator.evaluate({"literal": 123}).value.read()
    print(result_promise.value)

    ### Expression call
    add = calculator.getOperator("add").func
    subtract = calculator.getOperator("subtract").func
    print("subtract: ", subtract, type(subtract))
    # result = await calculator.evaluate(
    #     {
    #         "call": {
    #             "function": add,
    #             "params": [
    #                 {"literal": 45},
    #                 {
    #                     "call": {
    #                         "function": subtract,
    #                         "params": [{"literal": 123}, {"literal": 67}],
    #                     }
    #                 },
    #             ],
    #         }
    #     }
    # ).value.read()
    # print(result.value)

    # request = calculator.evaluate_request()
    # subtract_call = request.expression.init("call")
    # subtract_call.function = subtract
    # subtract_params = subtract_call.init("params", 2)
    # subtract_params[1].literal = 67
    # add_call = subtract_params[0].init("call")
    # add_call.function = add
    # add_params = add_call.init("params", 2)
    # add_params[0].literal = 123
    # add_params[1].literal = 45
    # promise = request.send().value.read()
    # response = await promise
    # print(response.value)

    ### Expression previousResult  pipelining
    # add = calculator.getOperator("add").func
    # multiply = calculator.getOperator("multiply").func
    # mul_result = calculator.evaluate(
    #     {
    #         "call": {
    #             "function": multiply,
    #             "params": [
    #                 {"literal": 4},
    #                 {"literal": 6},
    #             ],
    #         },
    #     }
    # ).value  # (await expression.previousResult.read()).value

    # add_call = calculator.evaluate(
    #     {
    #         "call": {
    #             "function": add,
    #             "params": [{"previousResult": mul_result}, {"literal": 3}],
    #         }
    #     }
    # ).value

    # print((await add_call.read()).value)

    ### Function define
    # #   f(x, y) = x * 100 + y
    # #   g(x) = f(x, x + 1) * 2;
    # #   f(12, 34)
    # #   g(21)
    # add = calculator.getOperator("add").func
    # multiply = calculator.getOperator("multiply").func

    # f = calculator.defFunction(
    #     2,
    #     {
    #         "call": {
    #             "function": add,
    #             "params": [
    #                 {"parameter": 1},
    #                 {
    #                     "call": {
    #                         "function": multiply,
    #                         "params": [
    #                             {"literal": 100},
    #                             {"parameter": 0},
    #                         ],  # parameter - params[expression.parameter]
    #                     }
    #                 },
    #             ],
    #         }
    #     },
    # ).func
    # print("f:", f, type(f))

    # g = calculator.defFunction(
    #     1,
    #     {
    #         "call": {
    #             "function": multiply,
    #             "params": [
    #                 {"literal": 2},
    #                 {
    #                     "call": {
    #                         "function": f,
    #                         "params": [
    #                             {"parameter": 0},
    #                             {
    #                                 "call": {
    #                                     "function": add,
    #                                     "params": [{"parameter": 0}, {"literal": 1}],
    #                                 }
    #                             },
    #                         ],
    #                     }
    #                 },
    #             ],
    #         }
    #     },
    # ).func
    # print(
    #     (
    #         await calculator.evaluate(
    #             {"call": {"function": f, "params": [{"literal": 12}, {"literal": 34}]}}
    #         ).value.read()
    #     ).value
    # )
    # print(
    #     (
    #         await calculator.evaluate(
    #             {"call": {"function": g, "params": [{"literal": 21}]}}
    #         ).value.read()
    #     ).value
    # )

    pf = PowerFunction()
    print("pf: ", pf, type(pf))
    pow_call_back = calculator.evaluate(
        {
            "call": {
                "function": pf,
                "params": [
                    {"literal": 2},
                    {
                        "call": {
                            "function": add,
                            "params": [{"literal": 4}, {"literal": 5}],
                        }
                    },
                ],
            }
        }
    ).value.read()
    print(await pow_call_back)


class PowerFunction(calculator_capnp.Calculator.Function.Server):
    async def call(self, params, **kwargs):
        return pow(params[0], params[1])


async def cmd_main(host):
    host, port = host.split(":")
    await main(await capnp.AsyncIoStream.create_connection(host=host, port=port))


if __name__ == "__main__":
    asyncio.run(capnp.run(cmd_main(parse_args().host)))
