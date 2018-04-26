# -*- coding:utf-8 -*-
import os
import json
import aiohttp
import aiofiles
import traceback

from .utils import readexactly


class DownloadWrapper(object):

    def __init__(self, func, instance):
        self.download = func
        self.instance = instance

    async def close(self):
        if "close" in dir(self.download):
            await self.download.close()

    def __call__(self, *args, **kwargs):
        return self.download(self.instance, *args, **kwargs)


async def download(self, url, filename):
    """
    下载任务
    :param self:
    :param url:
    :param filename:
    :param sessions:
    :return:
    """
    async with aiohttp.ClientSession(conn_timeout=10, read_timeout=36000) as session:
        p = None
        # 出现异常后最多尝试2次，其中一次使用代理。
        for i in range(2):
            try:
                if p and self.proxy_auth:
                    proxy_auth = aiohttp.BasicAuth(*self.proxy_auth)
                else:
                    proxy_auth = None
                resp = await session.request(
                        "GET", url,
                        headers=self.headers,
                        proxy=p,
                        proxy_auth=proxy_auth)
                # 下载文件。
                total = int(resp.headers.get("Content-Length", 0))
                if total and resp.status < 300:
                    recv = 0
                    async with aiofiles.open(filename, "wb") as f:
                        chunk = await readexactly(resp.content, 1024000)
                        while chunk:
                            recv += len(chunk)
                            self.logger.debug(
                                f"Download {filename}: {len(chunk)} from {url}"
                                f", processing {round(recv/total, 2)}. ")
                            await f.write(chunk)
                            chunk = await readexactly(resp.content, 1024000)
                    self.logger.info("Download finished. ")

                else:
                    raise RuntimeError(f"Haven't got any data from {url}. ")
                break
            except Exception:
                self.logger.error("Error: " + "".join(traceback.format_exc()))
                p = self.proxy
        else:
            if os.path.exists(filename):
                os.unlink(filename)
            return json.dumps({"url": url, "filename": filename})
