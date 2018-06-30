# -*- coding:utf-8 -*-
import os
import re
import json
import aiohttp
import aiofiles
import traceback

from .utils import readexactly


class DownloadWrapper(object):

    def __init__(self, download_method, downloader):
        self.default_engine_cls = DownloaderEngine
        self.download_method = download_method
        self.downloader = downloader

    async def close(self):
        pass

    async def __call__(self, *args, **kwargs):
        if self.download_method:
            return await self.download_method(self.downloader, *args, **kwargs)
        else:
            engine = self.default_engine_cls(self.downloader)
            try:
                return await engine.run(*args, **kwargs)
            finally:
                await engine.close()


async def download(self, url, filename, failed_times=0):
    """每次下载都重新开启一个新的session"""
    async with aiohttp.ClientSession(
            conn_timeout=10, read_timeout=3600) as session:
        return await _download(self, url, filename, failed_times, session)


async def co_session_download(self, url, filename, failed_times=0, sessions=[]):
    """所有请求使用同一个session，但需要增加将session的close方法传递给download函数"""
    if not sessions:
        sessions.append(aiohttp.ClientSession(
            conn_timeout=10, read_timeout=3600))
        co_session_download.close = sessions[0].close
    return await _download(self, url, filename, failed_times, sessions[0])


class DownloaderEngine(object):
    """
    支持断点续传
    """
    def __init__(self, downloader, conn_timeout=10, read_timeout=1800):
        self.session = aiohttp.ClientSession(
            conn_timeout=conn_timeout, read_timeout=read_timeout)
        self.downloader = downloader
        self.failed_times_max = 3
        self.tries = 0

    async def run(self, url, filename, failed_times=0):
        if failed_times > self.failed_times_max:
            self.downloader.logger.error(
                f"Abandon {filename} of {url} failed for {failed_times} times.")
            return
        received, total, f = 0, 0, None
        if os.path.exists(filename) and await self.conti_check(url):
            f = await aiofiles.open(filename, "ab")
            received = f.tell()

        while self.tries < 2:
            headers = self.downloader.headers.copy()
            try:
                while True:
                    headers["Range"] = f"bytes={received}-"
                    self.downloader.logger.debug(
                        f"{filename} got {received} bytes.")
                    resp = None
                    try:
                        resp = await self.session.request(
                            "GET", url, headers=headers, **self.get_proxy())
                        # 下载文件。
                        content_range = resp.headers['Content-Range']
                        total = int(re.search(r'/(\d+)', content_range).group(1))
                        total = total or content_range
                        if content_range and resp.status < 300:
                            f = f or await aiofiles.open(filename, "wb")
                            chunk = await readexactly(resp.content, 1024000)
                            while chunk:
                                received += len(chunk)
                                self.downloader.logger.debug(
                                    f"Download {filename}: {len(chunk)} from {url}"
                                    f", processing {round(received/total, 2)}. ")
                                await f.write(chunk)
                                chunk = await readexactly(resp.content, 1024000)
                            self.downloader.logger.info(
                                f"{filename} download finished. ")
                            break
                        else:
                            raise RuntimeError(f"Haven't got any data from {url}.")
                    except aiohttp.client_exceptions.ClientPayloadError:
                        self.downloader.logger.error(
                            f"{filename} download error, try to continue. ")
                    finally:
                        resp and resp.close()
                break
            except Exception as e:
                self.downloader.logger.error(f"{filename} got Error: {e}")
                self.tries += 1
        else:
            f and f.close()
            failed_times += 1
            self.downloader.logger.error(
                f"{filename} of {url} failed for {failed_times} times.")
            return json.dumps(
                {"url": url, "filename": filename, "failed_times": failed_times})

    def get_proxy(self):
        if self.tries % 2:
            return {
                "proxy": self.downloader.proxy,
                "proxy_auth": self.downloader.proxy_auth and
                              aiohttp.BasicAuth(*self.downloader.proxy_auth)
            }
        else:
            return {"proxy": None, "proxy_auth": None}

    async def conti_check(self, url):
        while True:
            try:
                headers = self.downloader.headers.copy()
                headers['Range'] = 'bytes=0-4'
                resp = await self.session.request(
                    "GET", url, headers=headers, **self.get_proxy())
                return bool(resp.headers.get('Content-Range'))
            except Exception as e:
                self.downloader.logger.error(f"Failed to check: {e}")
                if self.tries < 2:
                    self.tries += 1
                else:
                    raise e

    async def close(self):
        return await self.session.close()


async def _safe_download(self, url, filename, failed_times, session):
    """
        支持断点续传的下载
        :param self:
        :param url:
        :param filename:
        :param failed_times:
        :param session:
        :return:
        """
    failed_times_max = 3
    if failed_times > failed_times_max:
        self.logger.error(
            f"Abandon {filename} of {url} failed for {failed_times_max} times. ")
        return
    p = None
    # 出现异常后最多尝试2次，其中一次使用代理。
    recv = 0
    total = 0
    f = None
    if os.path.exists(filename):
        f = await aiofiles.open(filename, "ab")
        recv = f.tell()
    for i in range(2):
        headers = self.headers.copy()
        headers["range"] = f"bytes={recv}-"
        try:
            if p and self.proxy_auth:
                proxy_auth = aiohttp.BasicAuth(*self.proxy_auth)
            else:
                proxy_auth = None
            while True:
                headers["range"] = f"bytes={recv}-"
                print(f"{filename} recv {recv}")
                resp = None
                try:
                    resp = await session.request(
                        "GET", url,
                        headers=headers,
                        proxy=p,
                        proxy_auth=proxy_auth)
                    # 下载文件。
                    total = total or int(resp.headers.get("Content-Length", 0))
                    if int(resp.headers.get("Content-Length", 0)) and resp.status < 300:
                        f = f or await aiofiles.open(filename, "wb")
                        chunk = await readexactly(resp.content, 1024000)
                        while chunk:
                            recv += len(chunk)
                            self.logger.debug(
                                f"Download {filename}: {len(chunk)} from {url}"
                                f", processing {round(recv/total, 2)}. ")
                            await f.write(chunk)
                            chunk = await readexactly(resp.content, 1024000)
                        self.logger.info("Download finished. ")
                        break
                    else:
                        raise RuntimeError(f"Haven't got any data from {url}. ")
                except aiohttp.client_exceptions.ClientPayloadError:

                    self.logger.error(f"{filename} download error, try to continue. ")
                    resp and resp.close()
            break
        except Exception as e:
            self.logger.error(f"Error: {e}")
            p = self.proxy
    else:
        f and f.close()
        failed_times += 1
        if os.path.exists(filename):
            os.unlink(filename)
        self.logger.error(
            f"{filename} of {url} failed for {failed_times} times. push back.")
        return json.dumps({"url": url,
                    "filename": filename,
                    "failed_times": failed_times})


async def _download(self, url, filename, failed_times, session):
    """
    下载任务
    :param self:
    :param url:
    :param filename:
    :param failed_times:
    :param session:
    :return:
    """
    failed_times_max = 3
    if failed_times > failed_times_max:
        self.logger.error(
            f"Abandon {filename} of {url} failed for {failed_times_max} times. ")
        return
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
        failed_times += 1
        if os.path.exists(filename):
            os.unlink(filename)
        return json.dumps({"url": url,
                           "filename": filename,
                           "failed_times": failed_times})
