# -*- coding:utf-8 -*-
import aiofiles
import warnings


__all__ = ["FileSource", "RedisSource"]


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
        pass

    async def __anext__(self):
        return NotImplemented


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

    @staticmethod
    def enrich_parser(sub_parser):
        sub_parser.add_argument("-rh", "--redis-host", default="0.0.0.0")
        sub_parser.add_argument("-rp", "--redis-port", default=6379)
        sub_parser.add_argument("-rk", "--redis-key", default="download_meta")


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
        sub_parser.add_argument("--path", required=True)