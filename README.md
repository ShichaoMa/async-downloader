### 异步多协程下载器
```
usage: a-download [-h] {file,redis,cmdline} ...

Async downloader

positional arguments:
  {file,redis,cmdline}  Source.
    file                file source
    redis               redis source
    cmdline             command line source

optional arguments:
  -h, --help            show this help message and exit.
Command 'file'
usage: a-download file [-h] --workers WORKERS [--download DOWNLOAD]
                       [--proxy PROXY] [--idle] --path PATH

Command 'redis'
usage: a-download redis [-h] --workers WORKERS [--download DOWNLOAD]
                        [--proxy PROXY] [--idle] [-rh REDIS_HOST]
                        [-rp REDIS_PORT] [-rk REDIS_KEY]

Command 'cmdline'
usage: a-download cmdline [-h] --workers WORKERS [--download DOWNLOAD]
                          [--proxy PROXY] [--idle] --filename FILENAME --url
                          URL
```

可以在当前目录下创建一个名为sources的模块，程序会获取其中所有sources类，作为下载文件元信息来源。
参见RedisSource和FileSource等实现

可以指定一个download函数，如function[模块].download[函数]，提供自定义下载行为。
download函数必须是一个异步函数参数列表为url, filename, proxy, chunk_size