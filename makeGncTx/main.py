
# main.py -- parse a Monarch text file
#            and create Gnucash transactions from the data
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

__created__ = "2018-12-02 07:13"
__updated__ = "2019-01-11 12:36"

import os.path as osp
from sys import argv, exit
from parseMonarch import parse_monarch_report
from createGnucashTxs import create_gnc_txs
from Configuration import *


def main():
    if len(argv) < 4:
        print_error("NOT ENOUGH parameters!")
        print_info("usage: python {0} <monarch file> <gnucash file> <mode: prod|test>".format(argv[0]), color=YELLOW)
        print_info("Example: {0} '{1}' '{2}' 'test'".format(argv[0], "txtFromPdf/Monarch-Mark-all.txt", TEST1_GNC), color=CYAN)
        exit(4)

    mon_file = argv[1]
    if not osp.isfile(mon_file):
        print_error("File path '{}' does not exist. Exiting...".format(mon_file))
        exit(1)

    gnc_file = argv[2]
    if not osp.isfile(gnc_file):
        print_error("File path '{}' does not exist. Exiting...".format(gnc_file))
        exit(2)

    mode = argv[3]

    # parse an external Monarch report file
    tx_colxn = parse_monarch_report(mon_file, mode)

    # create gnucash transactions and write to the desired Gnucash file
    create_gnc_txs(tx_colxn, gnc_file, mode)

    print_info("\n >>> PROGRAM ENDED.", color=GREEN)


if __name__ == '__main__':
    main()
