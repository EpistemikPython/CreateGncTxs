
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
__updated__ = "2019-01-06 09:10"

from sys import argv, exit
import os.path as osp
import json
from Configuration import *


def parse_json_main():
    if len(argv) < 2:
        print("NOT ENOUGH parameters!")
        print("usage: python {0} <json file>".format(argv[0]))
        exit()

    json_file = argv[1]
    if not osp.isfile(json_file):
        print("File path '{}' does not exist. Exiting...".format(json_file))
        exit()

    with open(json_file, 'r') as fp:
        tx_list = json.load(fp)

    print("len(tx_list) = {}".format(len(tx_list)))
    for item in tx_list:
        print(item[FUND_CMPY])

    # print list
    print("tx_list = {}".format(json.dumps(tx_list, indent=4)))

    print("\n >>> PROGRAM ENDED.")


if __name__ == '__main__':
    parse_json_main()
