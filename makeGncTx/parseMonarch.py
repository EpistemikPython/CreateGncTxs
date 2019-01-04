
# parseMonarch.py -- parse a Monarch text file to a Monarch record 
#                    and save as a json file
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
__updated__ = "2019-01-03 17:26"

from sys import argv, exit
import os
import re
import copy
import json
import datetime
from Configuration import *

now = str(datetime.datetime.now())

def parseMonarchReport(file, mode):
    '''
    ?? look for 'CLIENT TRANSACTIONS' = start of transactions
    loop:
        check for 'Plan Type:'
            next line is either 'OPEN...', 'TFSA...' or 'RRSP...'
            use that as the key for the record
        check for $INVESTMENT_COMPANY/$MF_NAME-... :
            use $MF_NAME as the Fund Code in the tx
        look for date: MM/DD/YYYY = 'Trade Date'
            then parse:
                2 lines = 'Description'  : Text
                  line  = 'Gross'        : Currency float
                  line  = 'Net'          : Currency float
                  line  = 'Units'        : float
                  line  = 'Price'        : Currency float
                  line  = 'Unit Balance' : float
    '''
    print("parseMonarchReport({})\n".format(file))
    print("Runtime = " + now)
    
    if mode.lower() == "prod":
        record = copy.deepcopy(Tx_Record)
    else:
        # use a short example record
        record = { OWNER:"OWNER_MARK" ,
        PL_OPEN : [
        {"Trade Date": "10/26/2018", "Gross": "$34.53", "Description": "Reinvested:Distribution/Interest:", "Price": "$8.9732", "Unit Balance": "694.4350", "Units": "3.8480", "Net": "$34.53", "Fund Code": "CIG 11461"},
        {"Trade Date": "11/23/2018", "Gross": "$34.73", "Description": "Reinvested:Distribution/Interest:", "Price": "$8.9957", "Unit Balance": "698.2960", "Units": "3.8610", "Net": "$34.73", "Fund Code": "CIG 11461"},
        {"Trade Date": "10/26/2018", "Gross": "$5.30", "Description": "Reinvested:Distribution/Interest:", "Price": "$8.9732", "Unit Balance": "106.6770", "Units": "0.5910", "Net": "$5.30", "Fund Code": "CIG 11111"},
        {"Trade Date": "11/23/2018", "Gross": "$5.33", "Description": "Reinvested:Distribution/Interest:", "Price": "$8.9957", "Unit Balance": "107.2700", "Units": "0.5930", "Net": "$5.33", "Fund Code": "CIG 11111"}
        ] ,
        PL_TFSA : [
        {"Trade Date": "10/30/2018", "Gross": "$4.93", "Description": "Reinvested:Distribution/Interest:", "Price": "$8.4422", "Unit Balance": "308.6739", "Units": "0.5840", "Net": "$4.93", "Fund Code": "TML 674"},
        {"Trade Date": "11/29/2018", "Gross": "$4.94", "Description": "Reinvested:Distribution/Interest:", "Price": "$8.5672", "Unit Balance": "309.2505", "Units": "0.5766", "Net": "$4.94", "Fund Code": "TML 674"},
        {"Trade Date": "10/30/2018", "Gross": "$7.87", "Description": "Reinvested:Distribution/Interest:", "Price": "$8.4422", "Unit Balance": "492.7939", "Units": "0.9322", "Net": "$7.87", "Fund Code": "TML 704"},
        {"Trade Date": "11/29/2018", "Gross": "$7.88", "Description": "Reinvested:Distribution/Interest:", "Price": "$8.5672", "Unit Balance": "493.7137", "Units": "0.9198", "Net": "$7.88", "Fund Code": "TML 704"}
        ] ,
        PL_RRSP : [
        {"Trade Date": "10/19/2018", "Gross": "$26.28", "Description": "Reinvested:Distribution/Interest:", "Price": "$4.2733", "Unit Balance": "1910.3030", "Units": "6.1490", "Net": "$26.28", "Fund Code": "MFC 856"},
        {"Trade Date": "11/23/2018", "Gross": "$33.43", "Description": "Reinvested:Distribution/Interest:", "Price": "$4.1890", "Unit Balance": "1918.2830", "Units": "7.9800", "Net": "$33.43", "Fund Code": "MFC 856"},
        {"Trade Date": "10/19/2018", "Gross": "$20.49", "Description": "Reinvested:Distribution/Interest:", "Price": "$10.1337", "Unit Balance": "1386.5420", "Units": "2.0220", "Net": "$20.49", "Fund Code": "MFC 6129"},
        {"Trade Date": "11/23/2018", "Gross": "$22.88", "Description": "Reinvested:Distribution/Interest:", "Price": "$10.1511", "Unit Balance": "1388.7960", "Units": "2.2540", "Net": "$22.88", "Fund Code": "MFC 6129"}
        ]
        }
    
    # re searches
    reOWN = re.compile(".*({}).*".format(OWNER))
    rePLN = re.compile(r'([OPENTFSAR]{4})(\s?.*)')
    reFND = re.compile(".*([A-Z]{3})\s?([0-9]{3,5}).*")
    reDTE = re.compile(".*([0-9]{2}/[0-9]{2}/[0-9]{4}).*")
    
    curr_tx = {}
    bag = list()
    bag_name = ""
    fund_name = ""
    own_line = 0
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
                print("Current bag_name is: '{}'".format(bag_name))
                bag = record[bag_name]
                print("Current bag is: {}\n".format(str(bag)))
                mon_state = FIND_FUND
                # if state is RRSP or TFSA and Owner not found yet
                if bag_name != "OPEN" and record[OWNER] == "":
                    mon_state = FIND_OWNER
                continue
            
            # for RRSP and TFSA need to find owner after finding plan type 
            if mon_state == FIND_OWNER:
#                 print("FIND_OWNER line {} = {}".format(ct, line))
                if own_line == 0:
                    re_match = re.match(reOWN, line)
                    if re_match:
                        own_line += 1
                else:
                    owner_name = line.strip()
                    print("Current owner_name is: '{}'".format(owner_name))
                    record[OWNER] = owner_name
                    own_line = 0
                    mon_state = FIND_FUND
                continue
            
            if mon_state <= FIND_FUND:
                re_match = re.match(reFND, line)
                if re_match:
#                     print("FIND_FUND line {} = {}".format(ct, line.strip()))
#                     print(re_match.groups())
                    fund_company = re_match.group(1)
                    fund_code = re_match.group(2)
                    fund_name = fund_company + " " + fund_code
                    print("\n\tCurrent fund_name is: {}".format(fund_name))
                    mon_state = FIND_NEXT_TX
                    continue

            if mon_state <= FIND_NEXT_TX:
                re_match = re.match(reDTE, line)
                if re_match:
#                     print("FIND_NEXT_TX line {} = {}".format(ct, line.strip()))
#                     print(re_match.groups())
                    tx_date = re_match.group(1)
                    print("\n\tCurrent tx_date is: '{}'".format(tx_date))
                    curr_tx = copy.deepcopy(Monarch_Tx)
                    curr_tx[FUND_CMPY] = fund_company
                    curr_tx[FUND_CODE] = fund_code
                    curr_tx[TRADE_DATE] = tx_date
                    mon_state = FILL_CURR_TX
                    continue

            if mon_state == FILL_CURR_TX:
#                 print("FILL_CURR_TX line {} = {}".format(ct, line.strip()))
                tx_line += 1
                entry = line.strip()
                if tx_line < 3:
                    if entry == AUTO_SYS or entry == INTX_IN:
                        # back up by one as have one MORE line of DESCRIPTION for AUTO_SYS and INT_TFI cases
                        tx_line -= 1
                    elif entry == SW_IN or entry == SW_OUT or entry == FEE:
                        # move forward by one because one FEWER line of DESCRIPTION for these cases
                        tx_line += 1
                    # TODO: match number to proceed to looking for GROSS?
                    curr_tx[DESC] += (entry + ":")
                    print("curr_tx[DESC] is: '{}'".format(curr_tx[DESC]))
                    continue
                if tx_line == 3:
                    curr_tx[GROSS] = (entry)
                    print("curr_tx[GROSS] is: '{}'".format(curr_tx[GROSS]))
                if tx_line == 4:
                    curr_tx[NET] = (entry)
                    if curr_tx[NET] != curr_tx[GROSS]:
                        print("curr_tx[NET] is: '{}'".format(curr_tx[NET]))
                        print("\n>>> PROBLEM!!! GROSS and NET do NOT match!!!\n")
                        continue 
                if tx_line == 5:
                    curr_tx[UNITS] = (entry)
                    print("curr_tx[UNITS] is: '{}'".format(curr_tx[UNITS]))
                if tx_line == 6:
                    curr_tx[PRICE] = (entry)
                    print("curr_tx[PRICE] is: '{}'".format(curr_tx[PRICE]))
                if tx_line == 7:
                    curr_tx[UNIT_BAL] = (entry)
                    print("curr_tx[UNIT_BAL] is: '{}'".format(curr_tx[UNIT_BAL]))
                    bag.append(curr_tx)
                    mon_state = STATE_SEARCH
                    tx_line = 0
    
    print("\n\tlen(Monarch record[{}]) = {}".format(PL_OPEN, len(record[PL_OPEN])))
#     print("\tMonarch record[{}] = {}".format(PL_OPEN, json.dumps(record[PL_OPEN], indent=4)))
    
    print("\n\tMonarch record[{}] = {}".format(OWNER, record[OWNER]))
    print("\n\tlen(Monarch record[{}]) = {}".format(PL_TFSA, len(record[PL_TFSA])))
#     print("\tMonarch record[{}] = {}".format(PL_TFSA, json.dumps(record[PL_TFSA], indent=4)))
    
    print("\n\tlen(Monarch record[{}]) = {}".format(PL_RRSP, len(record[PL_RRSP])))
#     print("\tMonarch record[{}] = {}".format(PL_RRSP, json.dumps(record[PL_RRSP], indent=4)))
    
    return record

def parseMonarchMain():
    if len(argv) < 3:
        print("NOT ENOUGH parameters!")
        print("usage: python {0} <monarch file> <mode: prod|test>".format(argv[0]))
        print("Example: {0} '{1}' 'test'".format(argv[0], "in/Monarch-Mark-all.txt"))
        exit()
    
    monFile = argv[1]
    if not os.path.isfile(monFile):
        print("File path '{}' does not exist. Exiting...".format(monFile))
        exit()
    
    mode = argv[2]
    
    # parse an external Monarch report file
    record = parseMonarchReport(monFile, mode)
    
    homeDir = '/home/marksa/dev/git/Python/pyTry/makeGncTx/'
    # print record as json file
    # pluck basename from monFile to use for saved json file
    (path, fname) = os.path.split(monFile)
    (basename, ext) = os.path.splitext(fname)
    outFile = homeDir + basename + "." + now.replace(" ", "_") + ".json"
#    fp = open('/home/marksa/dev/Python/makeGncTx/MonRec.json', 'w')
    fp = open(outFile, 'w')
    json.dump(record, fp, indent=4)
    
    print("\n >>> PROGRAM ENDED.")

if __name__ == '__main__':  
   parseMonarchMain()
