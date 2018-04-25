# -*- coding:utf-8 -*-
import json
import aiofiles
import warnings


__all__ = ["FileSource", "RedisSource", "CmdlineSource"]


class Source(object):
    """
    source 基类
    """

    def __aiter__(self):
        """
        返回一个可以使用async for进行迭代的异步可迭代对象。
        :return:
        """
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        进行资源关闭时使用
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        pass

    async def __anext__(self):
        """
        返回'{"url": "", "filename": ""}'
        :return:
        """
        return NotImplemented

    async def push_back(self, data):
        """
        下载失败后的回收下载任务的机制
        :param data:
        :return:
        """
        pass

    @staticmethod
    def enrich_parser(sub_parser):
        """
        需要专属命令行参数时需要实现
        :param sub_parser:
        :return:
        """
        pass


class RedisSource(Source):
    """
    redis source
    """

    def __init__(self, redis_host, redis_port, redis_key, **kwargs):
        try:
            from custom_redis.client import Redis
        except ImportError:
            try:
                from redis import Redis
            except ImportError:
                warnings.warn(
                    "RedisSource depends on redis, try: pip install redis. ")
                exit(1)
        self.redis_key = redis_key
        self.redis_conn = Redis(redis_host, redis_port)

    async def __anext__(self):
        """
        异步迭代器需要实现这个方法，这是一个异步方法，最终返回一个迭代值。
        :return:
        """
        return self.redis_conn.lpop(self.redis_key)

    async def push_back(self, data):
        self.redis_conn.rpush(self.redis_key, data)

    @staticmethod
    def enrich_parser(sub_parser):
        sub_parser.add_argument("-rh", "--redis-host", default="0.0.0.0")
        sub_parser.add_argument("-rp", "--redis-port", default=6379)
        sub_parser.add_argument("-rk", "--redis-key", default="download_meta")
        sub_parser.add_argument("--idle", action="store_true", help="Idle... ")


class FileSource(Source):
    """
    file source
    """

    def __init__(self, path, **kwargs):
        self.path = path

    async def __aenter__(self):
        self.file = await aiofiles.open(self.path)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.file.close()

    async def __anext__(self):
        return await self.file.readline()

    @staticmethod
    def enrich_parser(sub_parser):
        sub_parser.add_argument(
            "--path", required=True, help="Path of file which store "
                                          "download meta in json lines. ")


class CmdlineSource(Source):
    """
    command line source
    """
    def __init__(self, filename, url, **kwargs):
        self.filename = filename
        self.url = url
        self.fired = False

    async def __anext__(self):
        if not self.fired:
            self.fired = True
            return json.dumps({"url": self.url, "filename": self.filename})

    @staticmethod
    def enrich_parser(sub_parser):
        sub_parser.add_argument(
            "--filename", required=True, help="Filename to save file. ")
        sub_parser.add_argument("--url", required=True, help="Download url. ")
