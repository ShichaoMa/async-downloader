from collections.abc import Coroutine

class A(object):

    def __init__(self):
        self.count = 0
        #self.coro = abc()
    #
    # def send(self, value):
    #     return self.coro.send(value)
    #
    # def throw(self, typ, val, tb):
    #     pass
    #
    # def close(self):
    #     pass

    def __iter__(self):
        return sleep(1).__await__()# This tells Task to wait for completion.

    __await__ = __iter__


import asyncio

async def sleep(delay):
    loop = asyncio.get_event_loop()
    future = loop.create_future()

    loop.call_later(delay,
                    asyncio.futures._set_result_unless_cancelled,
                    future, None)
    return (await future)


async def abc():

    await A()
    await sleep(1)
    return 111


loop = asyncio.get_event_loop()
task = loop.create_task(abc())
loop.run_until_complete(task)
print(task.result())