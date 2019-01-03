
# createGnucashTxs.py -- parse a Monarch record, possibly from a json file, 
#                        create Gnucash transactions from the data 
#                        and write to a Gnucash file
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
__updated__ = "2019-01-03 13:19"

from sys import argv, exit
import os
import re
import copy
import json
from gnucash import Session, Transaction, Split, Account, GncNumeric, GncCommodity, ACCT_TYPE_BANK, GUID
from gnucash.gnucash_core_c import guid_new_return, guid_to_string, CREC
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
    
def createGncTxs(monRec, gncFile, mode):
    '''
       Take the information from a transaction record and produce Gnucash transactions to write to a gnucash file
    '''
#     print("monRec = {}".format(monRec))

    # set the regex values needed for matches
    reGROSS  = re.compile("^(\(?)\$([0-9,]{1,6})\.([0-9]{2})\)?.*")
    reUNITS  = re.compile("^(\-?)([0-9]{1,5})\.([0-9]{4}).*")
    reDATE   = re.compile("^([0-9]{2})/([0-9]{2})/([0-9]{4}).*")
    reSWITCH = re.compile("^(" + SWITCH + ")\-([InOut]{2,3}).*")
    reINTX   = re.compile("^(" + INTX + ")\-([InOut]{2,3}).*")
    
    def prepareAccounts(planType):
        print("\n\nPlan type = '{}'".format(planType))
        
        revPath = copy.copy(ACCT_PATHS[REVENUE])
#         print("revPath = '{}'".format(str(revPath)))
        revPath.append(planType)
#         print("revPath = '{}'".format(str(revPath)))
        astParentPath = copy.copy(ACCT_PATHS[ASSET])
        astParentPath.append(planType)
        
        if planType != PL_OPEN:
            plOwner = monRec[OWNER]
            if plOwner == '':
                raise Exception("PROBLEM!! Trying to process plan type '{}' but NO Owner value found in Record!!".format(planType))
            revPath.append(ACCT_PATHS[plOwner])
            astParentPath.append(ACCT_PATHS[plOwner])
        
        print("revPath = '{}'".format(str(revPath)))
        revAcct = account_from_path(root, revPath)
        print("revAcct = '{}'".format(revAcct.GetName()))
        
        print("astParentPath = '{}'".format(str(astParentPath)))
        astParent = account_from_path(root, astParentPath)
        print("astParent = '{}'".format(astParent.GetName()))
        
        for mtx in monRec[planType]:
            createGncTx(mtx, planType, revAcct, astParent)
    # end INNER prepareAccounts()
    
    def createGncTx(mtx, planType, revAcct, astParent):
        '''
           Asset accounts: use the proper path to find the parent then search for the Fund Code in the descendants
           Revenue accounts: pick the proper account based on owner and plan type
           grossCurr: re match to Gross then concatenate the two match groups
           date: re match to get day, month and year then re-assemble to form Gnc date
           Units: re match and concatenate the two groups on either side of decimal point
           Description: use DESC and Fund Code
           Notes: use 'Unit Balance' and UNIT_BAL
        '''
        transfer = False
        try:
            # check if we have a switch/transfer
            re_matSwitch = re.match(reSWITCH, mtx[DESC])
            re_matIntx = re.match(reINTX, mtx[DESC])
            if re_matSwitch or re_matIntx:
                transfer = True

            # get the asset account name
            astAcctName = mtx[FUND_CMPY] + " " + mtx[FUND_CODE]
            
            # special locations for Trust Revenue and Asset accounts
            if astAcctName == TRUST_AST_ACCT:
                astParent = root.lookup_by_name(TRUST)
                revAcct = root.lookup_by_name(TRUST_REV_ACCT)
            
            # get the asset account
            astAcct = astParent.lookup_by_name(astAcctName)
            if astAcct == None:
                raise Exception("Could NOT find acct '{}' under parent '{}'".format(astAcctName, astParent.GetName()))
            else:
                print("\n astAcct = '{}'".format(astAcct.GetName()))
            
            # get the dollar value of the tx
            re_match = re.match(reGROSS, mtx[GROSS])
            if re_match:
                print(re_match.groups())
                strGrossCurr = re_match.group(2) + re_match.group(3)
                # remove possible comma
                grossCurr = int(strGrossCurr.replace(',', ''))
                # if match group 1 is not empty, amount is negative
                if re_match.group(1) != '':
                    grossCurr *= -1
                print("grossCurr = '{}'".format(grossCurr))
                grossOpp = grossCurr * -1
                print("grossOpp = '{}'".format(grossOpp))
            else:
                raise Exception("PROBLEM!! reGROSS DID NOT match with value '{}'!".format(mtx[GROSS]))
            
            # get the units of the tx
            re_match = re.match(reUNITS, mtx[UNITS])
            if re_match:
                print(re_match.groups())
                units = int(re_match.group(2) + re_match.group(3)) 
                # if match group 1 is not empty, units is negative
                if re_match.group(1) != '':
                    units *= -1
                print("units = '{}'".format(units))
            else:
                raise Exception("PROBLEM!! reUNITS DID NOT match with value '{}'!".format(mtx[UNITS]))
            
            # get the date items
            re_match = re.match(reDATE, mtx[TRADE_DATE])
            if re_match:
                print(re_match.groups())
                trade_mth = int(re_match.group(1)) 
                print("trade_mth = '{}'".format(trade_mth))
                trade_day = int(re_match.group(2)) 
                print("trade_day = '{}'".format(trade_day))
                trade_yr  = int(re_match.group(3))
                print("trade_yr = '{}'".format(trade_yr))
            else:
                raise Exception("PROBLEM!! reTRADE_DATE DID NOT match with value '{}'!".format(mtx[TRADE_DATE]))
            
            # assemble the Description string
            descr = CMPY_FULL_NAME[mtx[FUND_CMPY]] + ": " + mtx[DESC] + " " + astAcctName
            print("descr = '{}'".format(descr))
            
            # notes field
            notes = astAcctName + " balance = " + mtx[UNIT_BAL]
            print("notes = '{}'".format(notes))
            
            # check the type of tx -- a Distribution OR the first or second item of a switch/transfer pair
            havePair = False
            if transfer:
                print("transfer")
                # look for switches in same plan type, company, date and opposite gross value
                for itx in gncRec[planType]:
                    if itx[FUND_CMPY] == mtx[FUND_CMPY] and itx[TRADE_DATE] == mtx[TRADE_DATE] and itx[GROSS] == grossOpp:
                        # already have the first item of the pair
                        havePair = True
                        pair_tx = itx
                        break
                
                if not havePair:
                    # create a new switch
                    pair_tx = copy.deepcopy(Tx_Switch)
                    # fill in the fields for the switch tx
                    pair_tx[FUND_CMPY] = mtx[FUND_CMPY]
                    pair_tx[TRADE_DATE] = mtx[TRADE_DATE]
                    pair_tx[NOTES] = notes
                    pair_tx[ACCT] = astAcct
                    pair_tx[GROSS] = grossCurr
                    pair_tx[UNITS] = units
                    # add to the record then return
                    gncRec[planType].append(pair_tx)
                    return
            
            #=================================================================================================
            # create a gnucash Tx
            gtx = Transaction(book)
            # gets a guid on construction
            print("gtx guid = '{}'".format(gtx.GetGUID().to_string()))
            
            gtx.BeginEdit()
            
            gtx.SetCurrency(CAD)
            gtx.SetDate(trade_day, trade_mth, trade_yr)
            print("gtx date = '{}'".format(gtx.GetDate()))
            gtx.SetDescription(descr)
            
            # create the ASSET split for the Tx
            splAst = Split(book)
            splAst.SetParent(gtx)
            # set the account, value, and units of the Asset split
            splAst.SetAccount(astAcct)
            splAst.SetValue(GncNumeric(grossCurr, 100))
            splAst.SetAmount(GncNumeric(units, 10000))
            
            if transfer:
                # create the second ASSET split for the Tx
                splAst2 = Split(book)
                splAst2.SetParent(gtx)
                # set the account, value, and units of the second Asset split
                splAst2.SetAccount(pair_tx[ACCT])
                splAst2.SetValue(GncNumeric(pair_tx[GROSS], 100))
                splAst2.SetAmount(GncNumeric(pair_tx[UNITS], 10000))
                # set actions for the splits
                splAst2.SetAction("Buy" if units < 0 else "Sell")
                splAst.SetAction("Buy" if units > 0 else "Sell")
                # combined Description for the Tx and set memos for the splits
                gtx.SetNotes(notes + " | " + pair_tx[NOTES])
                splAst.SetMemo(notes)
                splAst2.SetMemo(pair_tx[NOTES])
            else:
                gtx.SetNotes(notes)
                splAst.SetAction(DIST)
                # create the REVENUE split for the Tx
                splRev = Split(book)
                splRev.SetParent(gtx)
                # set the account, value and Reconciled of the Revenue split
                splRev.SetAccount(revAcct)
                splRev.SetValue(GncNumeric(grossOpp, 100))
                splRev.SetReconcile(CREC)
            
            # roll back if something went wrong and the two splits DO NOT balance
            if not gtx.GetImbalanceValue().zero_p():
                print("gtx imbalance = '{}'!! Roll back transaction changes!".format(gtx.GetImbalanceValue().to_string()))
                gtx.RollbackEdit()
                return
            
            if mode == "PROD":
                print("Mode = '{}': Commit transaction changes.".format(mode))
                gtx.CommitEdit()
                session.save()
            else:
                print("Mode = '{}': Roll back transaction changes!\n".format(mode))
                gtx.RollbackEdit()
                
        except Exception as e:
            print("createGncTx() EXCEPTION!! '{}'\n".format(str(e)))
    # end INNER createGncTx()
    
#     gncFileName = PRAC2_GNC
    print("\n gncFile = '{}'".format(gncFile))
    
    try:
        session = Session(gncFile)
        book = session.book
        
        root = book.get_root_account()
        root.get_instance()
        
        commod_tab = book.get_table()
        session.save() # really needed?
        
        CAD = commod_tab.lookup("ISO4217", "CAD")
        
        # EXPERIMENT
        if mode.lower() == 'prod':
            
            gncRec = copy.deepcopy(Tx_Record)
    
            prepareAccounts(PL_OPEN)
            
            prepareAccounts(PL_TFSA)
             
            prepareAccounts(PL_RRSP)
            
            if mode == "PROD":
                print("Mode = '{}': Save session.".format(mode))
                session.save()
        
        else:
            # just show the account paths
            revPath = copy.copy(ACCT_PATHS[REVENUE])
            revPath.append(PL_OPEN)
            showAccount(root, revPath)
            astPath = copy.copy(ACCT_PATHS[ASSET])
            astPath.append(PL_OPEN)
            showAccount(root, astPath)
            
            revPath.pop()
            revPath.append(PL_TFSA)
            showAccount(root, revPath)
            astPath.pop()
            astPath.append(PL_TFSA)
            showAccount(root, astPath)
            
            revPath.pop()
            revPath.append(PL_RRSP)
            showAccount(root, revPath)
            astPath.pop()
            astPath.append(PL_RRSP)
            showAccount(root, astPath)
        
        session.end()
    
    except Exception as e:
        print("createGncTxs() EXCEPTION!! '{}'".format(str(e)))
        if "session" in locals():
            session.end()
        raise
# end createGncTxs()
    
def createGncTxsMain():
    usage = "usage: python {0} <monarch file> <gnucash file> <mode: prod|test>".format(argv[0])
    if len(argv) < 4:
        print("NOT ENOUGH parameters!")
        print(usage)
        exit()
    
    monFile = argv[1]
    if not os.path.isfile(monFile):
        print("File path '{}' does not exist. Exiting...".format(monFile))
        print(usage)
        exit()

    # get Monarch record from the Monarch json file
#     record = ???()
    
    gncFile = argv[2]
    if not os.path.isfile(gncFile):
        print("File path '{}' does not exist. Exiting...".format(gncFile))
        exit()
    
    mode = argv[3]
    
    createGncTxs(record, gncFile, mode)
    
    print("\n >>> PROGRAM ENDED.")
    
if __name__ == '__main__':  
   createGncTxsMain()
