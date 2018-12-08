
# parseMonarch.py -- parse a Monarch text file 
#                    and create Gnucash transactions from the data
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
__updated__ = "2018-12-08 13:51"

import sys  
import os
import re
import copy
import json

CLIENT_TX = "CLIENT TRANSACTIONS"
PLAN_TYPE = "Plan Type"
AUTO_SYS  = "Automatic/Systematic"

PL_OPEN   = "OPEN"
PL_TFSA   = "TFSA"
PL_RRSP   = "RRSP"

FUND_CODE  = "Fund Code"
# re = ([0-9]{2}/[0-9]{2}/[0-9]{4})
TRADE_DATE = "Trade Date"
DESC       = "Description"
GROSS      = "Gross"
NET        = "Net"
UNITS      = "Units"
PRICE      = "Price"
UNIT_BAL   = "Unit Balance" 

# re = ([A-Z]{3}_[0-9]{3,5})
CIG_11461 = "CIG 11461"
CIG_11111 = "CIG 11111"
CIG_18140 = "CIG 18140"
TML_674   = "TML 674"
TML_704   = "TML 704"
TML_203   = "TML 203"
TML_519   = "TML 519"
TML_1017  = "TML 1017"
TML_1018  = "TML 1018"
MFC_856   = "MFC 856"
MFC_6129  = "MFC 6129"
MFC_6130  = "MFC 6130"
MFC_6138  = "MFC 6138"
MFC_302   = "MFC 302"
MFC_3232  = "MFC 3232"
MFC_3689  = "MFC 3689"
MFC_1960  = "MFC 1960"
DYN_029   = "DYN 029"
DYN_729   = "DYN 729"
DYN_1562  = "DYN 1562"
DYN_1560  = "DYN 1560"
MMF_44424 = "MMF 44424"
MMF_4524  = "MMF 4524"

FundsList = [ 
    CIG_11461, CIG_11111, CIG_18140, 
    TML_674, TML_704, TML_203, TML_519, TML_1017, TML_1018, 
    MFC_856, MFC_6129, MFC_6130, MFC_6138, MFC_302, MFC_3232, MFC_3689, MFC_1960, 
    DYN_029, DYN_729, DYN_1562, DYN_1560,
    MMF_44424, MMF_4524
]

# mon_open = list()
# mon_tfsa = list()
# mon_rrsp = list()
Monarch_record = {
    PL_OPEN : [] ,
    PL_TFSA : [] ,
    PL_RRSP : []
}

Monarch_tx = {
    FUND_CODE    : "" ,
    TRADE_DATE   : "" ,
    DESC         : "" ,
    GROSS        : "" ,
    NET          : "" ,
    UNITS        : "" ,
    PRICE        : "" ,
    UNIT_BAL     : "" 
}

# parsing states
STATE_SEARCH   = 0
FIND_PLAN_TYPE = STATE_SEARCH + 1
FIND_FUND      = FIND_PLAN_TYPE +1
FIND_NEXT_TX   = FIND_FUND + 1
FILL_CURR_TX   = FIND_NEXT_TX + 1

def parseFile(file):
    print("parseFile({})\n".format(file))
    # ?? look for 'CLIENT TRANSACTIONS' = start of transactions
    # loop:
    #     check for 'Plan Type:'
    #         next line is either 'OPEN...', 'TFSA...' or 'RRSP...'
    #         use that as the key for the record
    #     check for $INVESTMENT_COMPANY/$MF_NAME-... :
    #         use $MF_NAME as the Fund Code in the tx
    #     look for date: MM/DD/YYYY = 'Trade Date'
    #         then parse:
    #             2 lines = 'Description'  : Text
    #               line  = 'Gross'        : Currency float
    #               line  = 'Net'          : Currency float
    #               line  = 'Units'        : float
    #               line  = 'Price'        : Currency float
    #               line  = 'Unit Balance' : float

    reCTX = re.compile(".*{}.*".format(CLIENT_TX))
    rePLT = re.compile(".*{}.*".format(PLAN_TYPE))
    rePLN = re.compile(r'([OPENTFSAR]{4})(\s?.*)')
    reFND = re.compile(".*([A-Z]{3}\s?[0-9]{3,5}).*")
    reDTE = re.compile(".*([0-9]{2}/[0-9]{2}/[0-9]{4}).*")
    
    curr_tx = {}
    bag = list()
    bag_name = ""
    fund_name = ""
    tx_date = ""
    tx_line = 0
    mon_state = STATE_SEARCH
    with open(file) as fp:
        ct = 0
        for line in fp:
            ct += 1
            re_match = re.match(rePLN, line)
            if re_match:
                print(re_match.groups())
                bag_name = re_match.group(1)
                print("Current bag_name is: {}".format(bag_name))
                bag = Monarch_record[bag_name]
                print("Current bag is: {}\n".format(str(bag)))
                mon_state = FIND_FUND
                continue
            
            if mon_state <= FIND_FUND:
                re_match = re.match(reFND, line)
                if re_match:
                    print("FIND_FUND line {} = {}".format(ct, line))
                    print(re_match.groups())
                    fund_name = re_match.group(1)
                    print("Current fund_name is: {}".format(fund_name))
                    mon_state = FIND_NEXT_TX
                    continue

            if mon_state <= FIND_NEXT_TX:
                re_match = re.match(reDTE, line)
                if re_match:
                    print("FIND_NEXT_TX line {} = {}".format(ct, line))
                    print(re_match.groups())
                    tx_date = re_match.group(1)
                    print("Current tx_date is: {}".format(tx_date))
                    curr_tx = copy.deepcopy(Monarch_tx)
                    curr_tx[FUND_CODE] = fund_name
                    curr_tx[TRADE_DATE] = tx_date
                    mon_state = FILL_CURR_TX
                    continue

            if mon_state == FILL_CURR_TX:
                print("FILL_CURR_TX line {} = {}".format(ct, line))
                tx_line += 1
                entry = line.strip()
                if tx_line < 3:
                    if entry == AUTO_SYS:
                        # back up by one to have one more line of DESCRIPTION for AUTO_SYS case
                        tx_line -= 1
                        # TODO: match number to proceed to looking for GROSS?
                    curr_tx[DESC] += (entry + ":")
                    print("curr_tx[DESC] is: {}".format(curr_tx[DESC]))
                    continue
                if tx_line < 4:
                    curr_tx[GROSS] += (entry)
                    print("curr_tx[GROSS] is: {}".format(curr_tx[GROSS]))
                    continue
                if tx_line < 5:
                    curr_tx[NET] += (entry)
                    print("curr_tx[NET] is: {}".format(curr_tx[NET]))
                    continue
                if tx_line < 6:
                    curr_tx[UNITS] += (entry)
                    print("curr_tx[UNITS] is: {}".format(curr_tx[UNITS]))
                    continue
                if tx_line < 7:
                    curr_tx[PRICE] += (entry)
                    print("curr_tx[PRICE] is: {}".format(curr_tx[PRICE]))
                    continue
                if tx_line < 8:
                    curr_tx[UNIT_BAL] += (entry)
                    print("curr_tx[UNIT_BAL] is: {}".format(curr_tx[UNIT_BAL]))
                    bag.append(curr_tx)
                    mon_state = STATE_SEARCH
                    tx_line = 0

#             if re.match(reCTX, line):
#                 print("line {}: {}".format(ct, line))
#                 
#             if re.match(rePLT, line):
#                 print("line {}: {}".format(ct, line))
#                 mon_state = FIND_PLAN_TYPE

def createGnuTxs(record):
    print("record = {}".format(record))
    
def main():  
    filepath = sys.argv[1]
    
    if not os.path.isfile(filepath):
        print("File path {} does not exist. Exiting...".format(filepath))
        sys.exit()
    
    parseFile(filepath)
    
    print("\n\tlen(Monarch_record[{}]) = {}".format(PL_OPEN, len(Monarch_record[PL_OPEN])))
    print("\tMonarch_record[{}] = {}".format(PL_OPEN, json.dumps(Monarch_record[PL_OPEN], indent=4)))

    print("\n\tlen(Monarch_record[{}]) = {}".format(PL_TFSA, len(Monarch_record[PL_TFSA])))
    print("\tMonarch_record[{}] = {}".format(PL_TFSA, json.dumps(Monarch_record[PL_TFSA], indent=4)))

    print("\n\tlen(Monarch_record[{}]) = {}".format(PL_RRSP, len(Monarch_record[PL_RRSP])))
    print("\tMonarch_record[{}] = {}".format(PL_RRSP, json.dumps(Monarch_record[PL_RRSP], indent=4)))

    createGnuTxs(Monarch_record)
    
if __name__ == '__main__':  
   main()
