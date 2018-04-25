# -*- coding:utf-8 -*-
import os
import sys

from functools import wraps
from argparse import Action, _SubParsersAction


class ArgparseHelper(Action):
    """
        显示格式友好的帮助信息
    """

    def __init__(self,
                 option_strings,
                 dest="",
                 default="",
                 help=None):
        super(ArgparseHelper, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, _SubParsersAction)]
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                print("Command '{}'".format(choice))
                print(subparser.format_usage())

        parser.exit()


def load_function(function_str):
    """
    返回字符串表示的函数对象
    :param function_str: module1.module2.function
    :return: function
    """
    if not function_str:
        return
    mod_str, _sep, function_str = function_str.rpartition('.')
    return getattr(__import__(
        mod_str, fromlist=mod_str.split(".")[-1]), function_str)


def cache_property(func):
    """
    缓存属性，只计算一次
    :param func:
    :return:
    """
    @property
    @wraps(func)
    def wrapper(*args, **kwargs):
        if func.__name__ not in args[0].__dict__:
            args[0].__dict__[func.__name__] = func(*args, **kwargs)
        return args[0].__dict__[func.__name__]
    return wrapper


async def readexactly(steam, n):
    if steam._exception is not None:
        raise steam._exception

    blocks = []
    while n > 0:
        block = await steam.read(n)
        if not block:
            break
        blocks.append(block)
        n -= len(block)

    return b''.join(blocks)


def find_source():
    sys.path.insert(0, os.getcwd())
    try:
        source = __import__("sources")
        sources = dict()
        for k in dir(source):
            if k.endswith("Source") and k != "Source":
                sources[k] = getattr(source, k)
        return sources
    except ImportError:
        pass