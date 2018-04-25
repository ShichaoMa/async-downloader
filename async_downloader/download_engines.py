# -*- coding:utf-8 -*-
import os
import json
import aiohttp
import aiofiles
import traceback

from collections.abc import Coroutine
from .utils import readexactly


class DownloadEngine(Coroutine):

    def __init__(self):
        self.session = aiohttp.ClientSession(conn_timeout=10, read_timeout=None)
        self.close_session = self.session.close()

    def send(self, value):
        return self.close_session.send(value)

    def throw(self, typ, val, tb):
        return self.close_session.throw(typ, val, tb)

    def close(self):
        return self.close_session.close()

    def __iter__(self):
        """
        __iter__和__await__要求返回可迭代对象。
        :return:
        """
        return self.close_session.__await__()

    __await__ = __iter__

    async def __call__(self, instance, url, filename):
        """
        下载任务
        :param url:
        :param filename:
        :return:
        """
        p = None
        # 出现异常后一共最多尝试2次，其中一次使用代理。
        for i in range(2):
            try:
                if p and instance.proxy_auth:
                    proxy_auth = aiohttp.BasicAuth(*instance.proxy_auth)
                else:
                    proxy_auth = None
                async with self.session.request(
                        "GET", url,
                        headers=instance.headers,
                        proxy=p,
                        proxy_auth=proxy_auth) as resp:
                    # 下载文件。
                    total = int(resp.headers.get("Content-Length", 0))
                    # 小于100k的都不要
                    if total > 100000:
                        recv = 0
                        async with aiofiles.open(filename, "wb") as f:
                            chunk = await readexactly(resp.content, 1024000)
                            while chunk:
                                recv += len(chunk)
                                instance.logger.debug(
                                    f"Download {filename}: {len(chunk)} from {url}"
                                    f", processing {round(recv/total, 2)}. ")
                                await f.write(chunk)
                                chunk = await readexactly(resp.content, 1024000)
                        instance.logger.info("Download finished. ")

                    else:
                        raise RuntimeError(f"Haven't got any data from {url}. ")
                break
            except Exception:
                instance.logger.error("Error: " + "".join(traceback.format_exc()))
                p = instance.proxy
        else:
            if os.path.exists(filename):
                os.unlink(filename)
            return json.dumps({"url": url, "filename": filename})
