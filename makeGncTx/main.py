
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
__updated__ = "2019-01-01 09:11"

import os.path as osp
from sys import argv, exit
from parseMonarch import parse_monarch_report
from createGnucashTxs import create_gnc_txs, PRAC1_GNC


def main():
    if len(argv) < 4:
        print("NOT ENOUGH parameters!")
        print("usage: python {0} <monarch file> <gnucash file> <mode: prod|test>".format(argv[0]))
        print("Example: {0} '{1}' '{2}' 'test'".format(argv[0], "txtFromPdf/Monarch-Mark-all.txt", PRAC1_GNC))
        exit(4)

    mon_file = argv[1]
    if not osp.isfile(mon_file):
        print("File path '{}' does not exist. Exiting...".format(mon_file))
        exit(1)

    gnc_file = argv[2]
    if not osp.isfile(gnc_file):
        print("File path '{}' does not exist. Exiting...".format(gnc_file))
        exit(2)

    mode = argv[3]

    # parse an external Monarch report file
    record = parse_monarch_report(mon_file, mode)

    # create gnucash transactions and write to the desired Gnucash file
    create_gnc_txs(record, gnc_file, mode)

    print("\n >>> PROGRAM ENDED.")


if __name__ == '__main__':
    main()
