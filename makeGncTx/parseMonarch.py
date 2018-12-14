
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
__updated__ = "2018-12-14 18:31"

from sys import argv, exit
import os
import re
import copy
import json
from gnucash import Session, Transaction, Split, Account, GncNumeric, GncCommodity, ACCT_TYPE_BANK, GUID
from gnucash.gnucash_core_c import guid_new_return, guid_to_string
from Configuration import *

def account_from_path(top_account, account_path, original_path=None):
    # mhs | debug
#     print( "top_account = %s, account_path = %s, original_path = %s" % (top_account.GetName(), account_path, original_path) )
    if original_path == None:
        original_path = account_path
    account, account_path = account_path[0], account_path[1:]
    # mhs | debug
#     print( "account = %s; account_path = %s" % (account, account_path) )
    
    account = top_account.lookup_by_name(account)
    # mhs | debug
#     print( "account = " + account.GetName() )
    if account == None:
        raise Exception("path " + str(original_path) + " could NOT be found")
    if len(account_path) > 0 :
        return account_from_path(account, account_path, original_path)
    else:
        return account
    
def showAccount(root, path):
    acct = account_from_path(root, path)
    acct_name = acct.GetName()
    print( "account = " + acct_name )
    descendants = acct.get_descendants()
    if len(descendants) == 0:
        print( "{} has NO Descendants!".format(acct_name) )
    else:
        print( "Descendants of {}:".format(acct_name) )
        for subAcct in descendants:
            print( "{}".format(subAcct.GetName()) )
    
def parseMonarchReport(file, record):
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
    
    # re searches
    reCTX = re.compile(".*{}.*".format(CLIENT_TX))
    rePLT = re.compile(".*{}.*".format(PLAN_TYPE))
    reOWN = re.compile(".*({}).*".format(OWNER))
    rePLN = re.compile(r'([OPENTFSAR]{4})(\s?.*)')
    reFND = re.compile(".*([A-Z]{3}\s?[0-9]{3,5}).*")
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
                print("Current bag_name is: {}".format(bag_name))
                bag = record[bag_name]
                print("Current bag is: {}\n".format(str(bag)))
                mon_state = FIND_FUND
                # if state is RRSP or TFSA and Owner not found yet
                if bag_name != "OPEN" and record[OWNER] == "":
                    mon_state = FIND_OWNER
                continue
            
            # for RRSP and TFSA need to find owner after finding plan type 
            if mon_state == FIND_OWNER:
                print("FIND_OWNER line {} = {}".format(ct, line))
                if own_line == 0:
                    re_match = re.match(reOWN, line)
                    if re_match:
                        own_line += 1
                else:
                    owner_name = line.strip()
                    print("Current owner_name is: {}".format(owner_name))
                    record[OWNER] = owner_name
                    own_line = 0
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
                if tx_line == 3:
                    curr_tx[GROSS] += (entry)
                    print("curr_tx[GROSS] is: {}".format(curr_tx[GROSS]))
                if tx_line == 4:
                    curr_tx[NET] += (entry)
                    print("curr_tx[NET] is: {}".format(curr_tx[NET]))
                if tx_line == 5:
                    curr_tx[UNITS] += (entry)
                    print("curr_tx[UNITS] is: {}".format(curr_tx[UNITS]))
                if tx_line == 6:
                    curr_tx[PRICE] += (entry)
                    print("curr_tx[PRICE] is: {}".format(curr_tx[PRICE]))
                if tx_line == 7:
                    curr_tx[UNIT_BAL] += (entry)
                    print("curr_tx[UNIT_BAL] is: {}".format(curr_tx[UNIT_BAL]))
                    bag.append(curr_tx)
                    mon_state = STATE_SEARCH
                    tx_line = 0

def createGnuTxs(record, mode):
#     print("record = {}".format(record))
    
#     if len(argv) < 6:    
#         print("NOT ENOUGH parameters!")
#         print("usage: createTx.py <gnucash file> <acct1> <acct2> <amount> <descr>")
#         print("example:")
#         print("[gnucash-env] [python] createTx.py 'HouseHold.gnucash' 'Dining' 'CIBC Visa' '1313' 'Test'|'Prod'")
#         exit()
    
    reAMOUNT = re.compile("^$([0-9]{1,4})\.([0-9]{2})")
    reDATE   = re.compile("^([0-9]{2})/([0-9]{2})/([0-9]{4})")
    
    gncFileName = PRACTICE_GNC
    print("gncFileName = {}".format(gncFileName))
    
    try:
        session = Session(gncFileName)
        book = session.book
        
        root = book.get_root_account()
        root.get_instance()
        
        commod_tab = book.get_table()
        session.save()
        
        CAD = commod_tab.lookup("ISO4217", "CAD")
        
        # EXPERIMENT
        if mode.lower() == 'prod':
            for tx in record[PL_OPEN]:
                print("{} Fund is '{}'".format(PL_OPEN, tx[FUND_CODE]))
                
            amount = int('1313')
            print("amount = {0}".format(amount))
            amount2 = amount * (-1)
            print("amount2 = {0}".format(amount2))
             
            acct1_name = 'Dining'
            acct2_name = 'CIBC Visa'
            acct1 = root.lookup_by_name(acct1_name)
            acct2 = root.lookup_by_name(acct2_name)
            print("acct1_name = {}".format(acct1_name))
             
            # create a new Tx
            tx = Transaction(book)
            # gets a guid on construction
            print("tx guid = {0}".format(tx.GetGUID().to_string()))
         
            tx.BeginEdit()
             
            # create two splits for the Tx
            s1 = Split(book)
            s1.SetParent(tx)
            # gets a guid on construction
            print("s1 guid = {0}".format(s1.GetGUID().to_string()))
            s2 = Split(book)
            s2.SetParent(tx)
            # gets a guid on construction
            print("s2 guid = {0}".format(s2.GetGUID().to_string()))
             
            tx.SetCurrency(CAD)
            tx.SetDate(13, 2, 2019)
            tx.SetDescription("Python Prod")
            tx.SetNotes("Python {0}".format(gncFileName))
        #     tx: set action ?
             
            # set the account and amount of split1
            s1.SetAccount(acct1)
            s1.SetValue(GncNumeric(amount, 100))
        #     s1.SetAmount(GncNumeric(amount, 100))
             
            # set the account and amount of split2
            s2.SetAccount(acct2)
            s2.SetValue(GncNumeric(amount2, 100))
        #     s2.SetAmount(GncNumeric(amount2, 100))
             
            print("Tx imbalance = {0}".format(tx.GetImbalanceValue().to_string()))
             
            if mode == "PROD":
                print("Mode = {}: Commit and save changes.".format(mode))
                tx.CommitEdit()
                session.save()
            else:
                print("Mode = {}: Roll back changes!".format(mode))
                tx.RollbackEdit()

        else:
            showAccount(root, Account_Paths[PL_OPEN][REVENUE])
            showAccount(root, Account_Paths[PL_OPEN][ASSET])
            
            showAccount(root, Account_Paths[PL_TFSA][REVENUE])
            showAccount(root, Account_Paths[PL_TFSA][ASSET])
            
            showAccount(root, Account_Paths[PL_RRSP][REVENUE])
            showAccount(root, Account_Paths[PL_RRSP][ASSET])
    
        session.end()
    #     session.destroy()
    except Exception as e:
        print("createGnuTxs() EXCEPTION!! '{}'".format(str(e)))
        if "session" in locals():
            session.end()
        raise
    
def main():
    if len(argv) < 3:
        print("NOT ENOUGH parameters!")
        print("usage: python {0} <book url> <mode: prod|test>".format(argv[0]))
        print("Example: {0} {1} 'test'".format(argv[0], PRACTICE_GNC))
        exit()
    
    filepath = argv[1]
    if not os.path.isfile(filepath):
        print("File path {} does not exist. Exiting...".format(filepath))
        exit()
    
    mode = argv[2]
    if mode.lower() == "prod":
        record = copy.deepcopy(Monarch_record)
        parseMonarchReport(filepath, record)
        
        print("\tMonarch record[{}] = {}".format(OWNER, record[OWNER]))
        print("\n\tlen(Monarch record[{}]) = {}".format(PL_OPEN, len(record[PL_OPEN])))
        print("\tMonarch record[{}] = {}".format(PL_OPEN, json.dumps(record[PL_OPEN], indent=4)))
    
        print("\n\tlen(Monarch record[{}]) = {}".format(PL_TFSA, len(record[PL_TFSA])))
        print("\tMonarch record[{}] = {}".format(PL_TFSA, json.dumps(record[PL_TFSA], indent=4)))
    
        print("\n\tlen(Monarch record[{}]) = {}".format(PL_RRSP, len(record[PL_RRSP])))
        print("\tMonarch record[{}] = {}".format(PL_RRSP, json.dumps(record[PL_RRSP], indent=4)))
    else:
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
    
    createGnuTxs(record, mode)
    
    print("\n >>> PROGRAM ENDED.")
    
if __name__ == '__main__':  
   main()
