
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
__updated__ = "2019-01-01 08:12"

from sys import argv, exit
import os
import re
import copy
import json
from gnucash import Session, Transaction, Split, Account, GncNumeric, GncCommodity, ACCT_TYPE_BANK, GUID
from gnucash.gnucash_core_c import guid_new_return, guid_to_string
from Configuration import *
from parseMonarch import *
from createGncTxs import *

def main():
    if len(argv) < 4:
        print("NOT ENOUGH parameters!")
        print("usage: python {0} <monarch file> <gnucash file> <mode: prod|test>".format(argv[0]))
        print("Example: {0} '{1}' '{2}' 'test'".format(argv[0], "txtFromPdf/Monarch-Mark-all.txt", PRAC1_GNC))
        exit()
    
    monFile = argv[1]
    if not os.path.isfile(monFile):
        print("File path '{}' does not exist. Exiting...".format(monFile))
        exit()
    
    gncFile = argv[2]
    if not os.path.isfile(gncFile):
        print("File path '{}' does not exist. Exiting...".format(gncFile))
        exit()
    
    mode = argv[3]
    
    # parse an external Monarch report file
    record = parseMonarchReport(monFile, mode)
    
    # create gnucash transactions and write to the desired Gnucash file
    createGnuTxs(record, gncFile, mode)
    
    print("\n >>> PROGRAM ENDED.")
    
if __name__ == '__main__':  
   main()
