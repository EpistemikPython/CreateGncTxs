
# parseJson.py -- parse a Monarch json file to a list
#
# Copyright (c) 2018, 2019 Mark Sattolo <epistemik@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# @author Mark Sattolo <epistemik@gmail.com>

__created__ = "2019-01-03 07:59"
__updated__ = "2019-01-11 15:55"

from sys import argv, exit
import os.path as osp
import json
from Configuration import *


def parse_json_main():
    if len(argv) < 2:
        print_error("NOT ENOUGH parameters!")
        print_info("usage: python {0} <json file>".format(argv[0]), color=YELLOW)
        exit()

    json_file = argv[1]
    if not osp.isfile(json_file):
        print_error("File path '{}' does not exist. Exiting...".format(json_file))
        exit()

    with open(json_file, 'r') as fp:
        tx_list = json.load(fp)

    print_info("len(tx_list) = {}".format(len(tx_list)), color=CYAN)
    for item in tx_list:
        print_info(item[FUND_CMPY])

    # print list
    print_info("tx_list = {}".format(json.dumps(tx_list, indent=4)), color=MAGENTA)

    print_info("\n >>> PROGRAM ENDED.", color=GREEN)


if __name__ == '__main__':
    parse_json_main()
