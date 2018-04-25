from collections.abc import Coroutine

class A(object):

    def __init__(self):
        self.count = 0
        self.coro = abc()

    def send(self, value):
        return self.coro.send(value)

    def throw(self, typ, val, tb):
        pass

    def close(self):
        pass

    def __await__(self):
        return self.coro.__await__()


import asyncio
async def abc():
    await asyncio.sleep(2)
    return 111




loop = asyncio.get_event_loop()
task = loop.create_task(A())
loop.run_until_complete(task)
print(task.result())