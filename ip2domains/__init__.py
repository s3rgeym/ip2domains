#!/usr/bin/env python
"""Scans IP addresses and finds domains"""
import argparse
import ipaddress
import itertools
import json
import logging
import os
import re
import socket
import ssl
import sys
import tempfile
import typing
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from queue import Queue
from threading import Thread

try:
    from collections import Sequence
except ImportError:
    from typing import Sequence


RESET = "\x1b[m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
GREY = "\x1b[37m"

BANNER = r"""
 _       _____     _                       _
(_)     / __  \   | |                     (_)
 _ _ __ `' / /' __| | ___  _ __ ___   __ _ _ _ __  ___
| | '_ \  / /  / _` |/ _ \| '_ ` _ \ / _` | | '_ \/ __|
| | |_) ./ /__| (_| | (_) | | | | | | (_| | | | | \__ \
|_| .__/\_____/\__,_|\___/|_| |_| |_|\__,_|_|_| |_|___/
  | |
  |_|
"""

DOMAIN_NAME_RE = re.compile(
    r"(\*\.)?([-a-z0-9]+\.)+(?!(local(domain|host)?|default)?$)[a-z]{2,8}", re.I
)

print_err = partial(print, file=sys.stderr)


class ColorHandler(logging.StreamHandler):
    LOG_COLORS = {
        logging.DEBUG: CYAN,
        logging.INFO: GREEN,
        logging.WARNING: RED,
        logging.ERROR: RED,
        logging.CRITICAL: RED,
    }

    _fmt = logging.Formatter("[%(levelname).1s] %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        message = self._fmt.format(record)
        return f"{self.LOG_COLORS[record.levelno]}{message}{RESET}"


class NameSpace(argparse.Namespace):
    input: typing.TextIO
    output: typing.TextIO
    addresses: list[str]
    workers_num: int
    timeout: float
    verbosity: int
    banner: bool


def parse_args(
    argv: Sequence[str] | None,
) -> tuple[argparse.ArgumentParser, NameSpace]:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-a",
        "--addr",
        nargs="+",
        help="IP address, range START_IP-END_IP or CIDR",
        default=[],
    )
    parser.add_argument(
        "-i",
        "--input",
        type=argparse.FileType(),
        default="-",
        help="input file containing list of ip addresses each on a new line",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w"),
        default="-",
        help="output file",
    )
    parser.add_argument(
        "-w",
        "--workers",
        dest="workers_num",
        type=int,
        default=50,
        help="maximum number of worker threads",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=2,
        help="timeout in seconds",
    )
    parser.add_argument(
        "--banner",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="show banner",
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help="be more verbose",
    )
    return parser, parser.parse_args(argv, NameSpace())


def fetch_cert_info(ip: str, timeout: float) -> dict:
    try:
        cert_data = ssl.get_server_certificate((ip, 443), timeout=timeout)
    except (socket.timeout, socket.error):
        # logging.warning("socket error: %s", ip)
        return {}
    with tempfile.NamedTemporaryFile("w+", delete=False) as temp:
        temp.write(cert_data)
        cert_file = temp.name
    try:
        return ssl._ssl._test_decode_cert(cert_file)
    finally:
        os.unlink(cert_file)


def extract_cert_domains(
    ip: str,
    timeout: float,
    result_queue: Queue,
) -> None:
    if not (cert_dict := fetch_cert_info(ip, timeout)):
        return
    logging.debug("SSL cert found at %s: %r", ip, cert_dict)
    subject = dict(x[0] for x in cert_dict.get("subject", []))
    domains = []
    if common_name := subject.get("commonName"):
        domains.append(common_name)
    # https://en.wikipedia.org/wiki/Subject_Alternative_Name
    domains.extend(
        v for k, v in cert_dict.get("subjectAltName", []) if k == "DNS"
    )
    domains = set(filter(DOMAIN_NAME_RE.fullmatch, domains))
    if domains:
        result_queue.put({"ip": ip, "domains": list(domains)})


def get_networks(
    addresses: list[str],
) -> typing.Iterable[IPv4Network | IPv6Network]:
    for addr in addresses:
        try:
            startip, endip = map(ipaddress.ip_address, addr.split("-"))
            yield from ipaddress.summarize_address_range(startip, endip)
        except ValueError:
            yield ipaddress.ip_network(addr)


def write_output(output: typing.TextIO, result_queue: Queue) -> None:
    while True:
        try:
            res = result_queue.get()
            if res is None:
                break
            json.dump(
                res,
                output,
                ensure_ascii=False,
            )
            output.write(os.linesep)
            output.flush()
        finally:
            result_queue.task_done()


def main(argv: Sequence[str] | None = None) -> int | None:
    _, args = parse_args(argv)

    if args.banner:
        print_err(BANNER)

    log_level = max(
        logging.DEBUG, logging.WARNING - args.verbosity * logging.DEBUG
    )
    logging.basicConfig(level=log_level, handlers=[ColorHandler()])

    addresses = args.addr.copy()

    if not args.input.isatty():
        addresses.extend(filter(None, map(str.strip, args.input)))

    # logging.debug(addresses)
    result_queue = Queue()
    output_thread = Thread(
        target=write_output, args=(args.output, result_queue)
    )
    output_thread.start()

    with ThreadPoolExecutor(args.workers_num) as pool:
        futs = [
            pool.submit(extract_cert_domains, ip, args.timeout, result_queue)
            for ip in map(
                str, itertools.chain.from_iterable(get_networks(addresses))
            )
        ]

    for fut in as_completed(futs):
        try:
            fut.result()
        except BaseException as ex:
            logging.warning(ex)
        finally:
            fut.cancel()

    result_queue.put_nowait(None)
    output_thread.join()

    logging.info("Finished!")  # MGIMO


if __name__ == "__main__":
    sys.exit(main())
