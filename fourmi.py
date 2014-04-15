#!/usr/bin/env python
"""
Fourmi, an web scraper build to search specific information for a given compound (and it's pseudonyms).

Usage:
    fourmi search <compound>
    fourmi [options] search <compound>
    fourmi -h | --help
    fourmi --version

Options:
    -h --help                       Show this screen.
    --version                       Show version.
    --verbose                       Verbose logging output.
    --log=<file>                    Save log to an file.
    -o <file> --output=<file>       Output file [default: result.*format*]
    -f <format> --format=<format>   Output formats (supported: csv, json, jsonlines, xml) [default: jsonlines]
"""

import os
import inspect

from twisted.internet import reactor
from scrapy.crawler import Crawler
from scrapy import log, signals
from scrapy.utils.project import get_project_settings
import docopt

from FourmiCrawler.parsers.parser import Parser
from FourmiCrawler.spider import FourmiSpider


def load_parsers(rel_dir="FourmiCrawler/parsers"):
    path = os.path.dirname(os.path.abspath(__file__))
    path += "/" + rel_dir
    parsers = []
    known_parser = set()

    for py in [f[:-3] for f in os.listdir(path) if f.endswith('.py') and f != '__init__.py']:
        mod = __import__('.'.join([rel_dir.replace("/", "."), py]), fromlist=[py])
        classes = [getattr(mod, x) for x in dir(mod) if inspect.isclass(getattr(mod, x))]
        for cls in classes:
            if issubclass(cls, Parser) and cls not in known_parser:
                parsers.append(cls())  # [review] - Would we ever need arguments for the parsers?
                known_parser.add(cls)
    return parsers


def setup_crawler(searchable, settings):
    spider = FourmiSpider(compound=searchable)
    spider.add_parsers(load_parsers())
    crawler = Crawler(settings)
    crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
    crawler.configure()
    crawler.crawl(spider)
    crawler.start()


def scrapy_settings_manipulation(arguments):
    settings = get_project_settings()

    if arguments["--output"] != 'result.*format*':
        settings.overrides["FEED_URI"] = arguments["--output"]
    elif arguments["--format"] == "jsonlines":
        settings.overrides["FEED_URI"] = "results.json"
    elif arguments["--format"] is not None:
        settings.overrides["FEED_URI"] = "results." + arguments["--format"]

    if arguments["--format"] is not None:
        settings.overrides["FEED_FORMAT"] = arguments["--format"]

    return settings


def start_log(arguments):
    if arguments["--log"] is not None:
        if arguments["--verbose"]:
            log.start(logfile=arguments["--log"], logstdout=False, loglevel=log.DEBUG)
        else:
            log.start(logfile=arguments["--log"], logstdout=True, loglevel=log.WARNING)
    else:
        if arguments["--verbose"]:
            log.start(logstdout=False, loglevel=log.DEBUG)
        else:
            log.start(logstdout=True, loglevel=log.WARNING)


if __name__ == '__main__':
    arguments = docopt.docopt(__doc__, version='Fourmi - V0.1.0')
    start_log(arguments)
    settings = scrapy_settings_manipulation(arguments)
    setup_crawler([arguments["<compound>"]], settings)
    reactor.run()
