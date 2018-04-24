"""
当异步生成器在一个协程中使用await gen.asend()获取值时，
如果此时在另一个协程中对其使用athrow，或asend，
并不能打断当前协程，而且会导致当前协程卡住永远无法返回。
原因不明。
"""
import sys
import json
import logging
import aiohttp
import asyncio
import aiofiles
import traceback
import async_timeout

from argparse import ArgumentParser

from .utils import *
from .sources import *

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'Accept-Encoding': 'deflate, gzip'
}


class AsyncDownloader(object):
    """
    异步多协程下载器
    """
    name = "downloader"

    def __init__(self):
        super(AsyncDownloader, self).__init__()
        self.sources = [globals()[k] for k in globals() if k.endswith("Source")]

        args = self.parse_args()
        self.workers = args.workers
        self.proxy = args.proxy
        self.generator = self.gen_task(
            globals()[args.source.capitalize() + "Source"](**vars(args)))

        if args.download:
            self.download = load_function(args.download)

    @cache_property
    def logger(self):
        logger = logging.getLogger(self.name)
        logger.setLevel(10)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        return logger

    def parse_args(self):
        base_parser = ArgumentParser(
            description=self.__class__.__doc__, add_help=False)
        base_parser.add_argument(
            "--workers", required=True, type=int, help="Worker count. ")
        base_parser.add_argument(
            "--download", help="Download method, async needed. ")
        base_parser.add_argument(
            "--proxy", default="http://127.0.0.1:8123", help="Proxy to use.")
        parser = ArgumentParser(description="Async downloader", add_help=False)
        parser.add_argument('-h', '--help', action=ArgparseHelper,
                            help='show this help message and exit. ')
        sub_parsers = parser.add_subparsers(dest="source", help="Source. ")

        for source in self.sources:
            name = source.__name__
            sub_parser = sub_parsers.add_parser(
                name.replace("Source", "").lower(),
                parents=[base_parser], help=name + ". ")
            source.enrich_parser(sub_parser)

        return parser.parse_args()

    def start(self):
        loop = asyncio.get_event_loop()
        task = loop.create_task(
            self.process(self.generator, self.workers, self.proxy, loop))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            # 发送一个False，使用异步生成器跳出循环
            stop_task = loop.create_task(self.generator.asend(False))
            loop.run_until_complete(asyncio.gather(task, stop_task))
            loop.close()

    async def download(self, url, filename, proxy, chunk_size=1024000):
        """
        下载任务
        :param url:
        :param filename:
        :param proxy:
        :param chunk_size:
        :return:
        """
        p, resp, session = None, None, None
        # 规定时间内打开session获取到response，否则超时，一共最多尝试2次，其中一次使用代理。
        for i in range(2):
            try:
                async with async_timeout.timeout(20):
                    session = aiohttp.request("get", url, headers=headers,
                                              proxy=p)
                    resp = await session.__aenter__()
                break
            except Exception:
                traceback.print_exc()
                p = proxy

        if resp:
            # 下载文件。
            total = int(resp.headers.get("Content-Length", 0))
            if total:
                try:
                    recv = 0
                    async with aiofiles.open(filename, "wb") as f:
                        chunk = await resp.content.read(chunk_size)
                        while chunk:
                            recv += len(chunk)
                            self.logger.debug(
                                f"Download {filename}: {len(chunk)} from {url}"
                                f", processing {round(recv/total, 2)}. ")
                            await f.write(chunk)
                            chunk = await resp.content.read(chunk_size)
                        self.logger.info("Download finished. ")
                finally:
                    # 关闭session。
                    await session.__aexit__(*sys.exc_info())
                    self.logger.debug("Coroutine closed. ")
            else:
                self.logger.info(f"Haven't got any data from {url}. ")
        else:
            self.logger.error("Error occurred.")

    async def gen_task(self, source):
        # 预激专用，预激操作不返回有用的数据。
        yield
        async with source as iterable:
            async for data in iterable:
                if data:
                    conti = yield json.loads(data)
                else:
                    conti = yield None
                if not conti:
                    break
        # 关闭时走到这，返回None
        yield
        yield "exit"

    async def process(self, generator, count, proxy, loop):
        self.logger.info("Start process tasks. ")
        # 预激
        await generator.asend(None)
        i = count
        tasks = []
        alive = True
        # 当没有关闭或者有任务时，会继续循环
        while alive or tasks:
            # 当任务未满且未关闭时，才会继续产生新任务
            while i > 0 and alive:
                data = await generator.asend(True)
                # 返回exit表示要退出了
                if data == "exit":
                    alive = False
                # 有data证明有下载任务
                elif data:
                    i -= 1
                    self.logger.debug(f"Start task {data['filename']}. ")
                    task = loop.create_task(self.download(proxy=proxy, **data))
                    tasks.append(task)
                # 否则休息一秒钟
                else:
                    self.logger.debug("Haven't got tasks. ")
                    await asyncio.sleep(1)
            # 清除完成的任务
            l = len(tasks) - 1
            while l >= 0:
                if tasks[l].done():
                    tasks.pop(l)
                    i += 1
                l -= 1
            # 任务队列是满的，休息一秒钟
            if not i:
                await asyncio.sleep(1)
            # 用来减缓任务队列有但不满且要关闭时产生的大量循环。
            await asyncio.sleep(.1)
        self.logger.info("Process stopped. ")
        await generator.aclose()


def main():
    globals().update(find_source() or {})
    AsyncDownloader().start()


if __name__ == "__main__":
    main()
