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
__updated__ = "2019-01-11 12:55"

from sys import argv, exit
import os.path as osp
import re
import copy
import json
from gnucash import Session, Transaction, Split, GncNumeric
from gnucash.gnucash_core_c import CREC
from Configuration import *


def account_from_path(top_account, account_path, original_path=None):
    if original_path is None:
        original_path = account_path
    account, account_path = account_path[0], account_path[1:]

    account = top_account.lookup_by_name(account)
    if account is None:
        raise Exception("path " + str(original_path) + " could NOT be found")
    if len(account_path) > 0:
        return account_from_path(account, account_path, original_path)
    else:
        return account


def show_account(root, path):
    acct = account_from_path(root, path)
    acct_name = acct.GetName()
    print("account = " + acct_name)
    descendants = acct.get_descendants()
    if len(descendants) == 0:
        print("{} has NO Descendants!".format(acct_name))
    else:
        print("Descendants of {}:".format(acct_name))
        for subAcct in descendants:
            print("{}".format(subAcct.GetName()))


def create_gnc_txs(mon_rec, gnc_file, mode):
    """
    Take the information from a transaction collection and produce Gnucash transactions to write to a Gnucash file
    """
    # set the regex values needed for matches
    reGROSS  = re.compile("^(\(?)\$([0-9,]{1,6})\.([0-9]{2})\)?.*")
    reUNITS  = re.compile("^(\-?)([0-9]{1,5})\.([0-9]{4}).*")
    reDATE   = re.compile("^([0-9]{2})/([0-9]{2})/([0-9]{4}).*")
    reSWITCH = re.compile("^(" + SWITCH + ")\-([InOut]{2,3}).*")
    reINTX   = re.compile("^(" + INTRF + ")\-([InOut]{2,3}).*")

    def prepare_accounts(plan_type):
        print("\n\nPlan type = '{}'".format(plan_type))

        rev_path = copy.copy(ACCT_PATHS[REVENUE])
        # print("rev_path = '{}'".format(str(rev_path)))
        rev_path.append(plan_type)
        # print("rev_path = '{}'".format(str(rev_path)))
        ast_parent_path = copy.copy(ACCT_PATHS[ASSET])
        ast_parent_path.append(plan_type)

        if plan_type != PL_OPEN:
            pl_owner = mon_rec[OWNER]
            if pl_owner == '':
                raise Exception(
                    "PROBLEM!! Trying to process plan type '{}' but NO Owner value found in Record!!".format(plan_type))
            rev_path.append(ACCT_PATHS[pl_owner])
            ast_parent_path.append(ACCT_PATHS[pl_owner])

        print("rev_path = '{}'".format(str(rev_path)))
        rev_acct = account_from_path(root, rev_path)
        print("rev_acct = '{}'".format(rev_acct.GetName()))

        print("ast_parent_path = '{}'".format(str(ast_parent_path)))
        ast_parent = account_from_path(root, ast_parent_path)
        print("ast_parent = '{}'".format(ast_parent.GetName()))

        for mtx in mon_rec[plan_type]:
            create_gnc_tx(mtx, plan_type, rev_acct, ast_parent)
    # end INNER prepare_accounts()

    def create_gnc_tx(mtx, plan_type, rev_acct, ast_parent):
        """
           Asset accounts: use the proper path to find the parent then search for the Fund Code in the descendants
           Revenue accounts: pick the proper account based on owner and plan type
           gross_curr: re match to Gross then concatenate the two match groups
           date: re match to get day, month and year then re-assemble to form Gnc date
           Units: re match and concatenate the two groups on either side of decimal point
           Description: use DESC and Fund Code
           Notes: use 'Unit Balance' and UNIT_BAL
        """
        transfer = False
        try:
            # see note in create_gnc_txs_main() regarding json.load()
            fund_company = str(mtx[FUND_CMPY])
            desc = str(mtx[DESC])
            trade_date = str(mtx[TRADE_DATE])

            # check if we have a switch/transfer
            re_mat_switch = re.match(reSWITCH, desc)
            re_mat_intx = re.match(reINTX, desc)
            if re_mat_switch or re_mat_intx:
                transfer = True

            # get the asset account name
            ast_acct_name = fund_company + " " + mtx[FUND_CODE]
            print("ast_acct_name = '{}'".format(ast_acct_name))
            print("type(ast_acct_name) = '{}'".format(type(ast_acct_name)))
            ast_acct_str = str(ast_acct_name)
            print("ast_acct_str = '{}'".format(ast_acct_str))
            print("type(ast_acct_str) = '{}'".format(type(ast_acct_str)))

            # special locations for Trust Revenue and Asset accounts
            if ast_acct_name == TRUST_AST_ACCT:
                ast_parent = root.lookup_by_name(TRUST)
                print("\n ast_parent = '{}'".format(ast_parent.GetName()))
                rev_acct = root.lookup_by_name(TRUST_REV_ACCT)
                print("\n rev_acct = '{}'".format(rev_acct.GetName()))

            # get the asset account
            ast_acct = ast_parent.lookup_by_name(ast_acct_str)
            if ast_acct is None:
                raise Exception("Could NOT find acct '{}' under parent '{}'".format(ast_acct_name, ast_parent.GetName()))
            else:
                print_info("\n ast_acct = '{}'".format(ast_acct.GetName()), color=CYAN)

            # get the dollar value of the tx
            re_match = re.match(reGROSS, mtx[GROSS])
            if re_match:
                print(re_match.groups())
                str_gross_curr = re_match.group(2) + re_match.group(3)
                # remove possible comma
                gross_curr = int(str_gross_curr.replace(',', ''))
                # if match group 1 is not empty, amount is negative
                if re_match.group(1) != '':
                    gross_curr *= -1
                print("gross_curr = '{}'".format(gross_curr))
                gross_opp = gross_curr * -1
                print("gross_opp = '{}'".format(gross_opp))
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
            re_match = re.match(reDATE, trade_date)
            if re_match:
                print(re_match.groups())
                trade_mth = int(re_match.group(1))
                print("trade_mth = '{}'".format(trade_mth))
                trade_day = int(re_match.group(2))
                print("trade_day = '{}'".format(trade_day))
                trade_yr = int(re_match.group(3))
                print("trade_yr = '{}'".format(trade_yr))
            else:
                raise Exception("PROBLEM!! reTRADE_DATE DID NOT match with value '{}'!".format(trade_date))

            # assemble the Description string
            descr = str(COMPANY_NAME[fund_company] + ": " + desc + " " + ast_acct_name)
            print("descr = '{}'".format(descr))

            # notes field
            notes = str(ast_acct_name + " balance = " + mtx[UNIT_BAL])
            print("notes = '{}'".format(notes))

            # check the type of tx -- a Distribution OR the first or second item of a switch/transfer pair
            have_pair = False
            if transfer:
                print("transfer")
                # look for switches in same plan type, company, date and opposite gross value
                for itx in gnc_collection[plan_type]:
                    if itx[FUND_CMPY] == fund_company and itx[TRADE_DATE] == trade_date and itx[GROSS] == gross_opp:
                        # already have the first item of the pair
                        have_pair = True
                        pair_tx = itx
                        break

                if not have_pair:
                    # create a new switch
                    pair_tx = copy.deepcopy(Tx_Record)
                    # fill in the fields for the switch tx
                    pair_tx[FUND_CMPY] = fund_company
                    pair_tx[TRADE_DATE] = trade_date
                    pair_tx[NOTES] = notes
                    pair_tx[ACCT] = ast_acct
                    pair_tx[GROSS] = gross_curr
                    pair_tx[UNITS] = units
                    # add to the record then return
                    gnc_collection[plan_type].append(pair_tx)
                    return

            # =================================================================================================
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
            spl_ast = Split(book)
            spl_ast.SetParent(gtx)
            # set the account, value, and units of the Asset split
            spl_ast.SetAccount(ast_acct)
            spl_ast.SetValue(GncNumeric(gross_curr, 100))
            spl_ast.SetAmount(GncNumeric(units, 10000))

            if transfer:
                # create the second ASSET split for the Tx
                spl_ast2 = Split(book)
                spl_ast2.SetParent(gtx)
                # set the Account, Value, and Units of the second ASSET split
                spl_ast2.SetAccount(pair_tx[ACCT])
                spl_ast2.SetValue(GncNumeric(pair_tx[GROSS], 100))
                spl_ast2.SetAmount(GncNumeric(pair_tx[UNITS], 10000))
                # set Actions for the splits
                spl_ast2.SetAction("Buy" if units < 0 else "Sell")
                spl_ast.SetAction("Buy" if units > 0 else "Sell")
                # combine Notes for the Tx and set Memos for the splits
                gtx.SetNotes(notes + " | " + pair_tx[NOTES])
                spl_ast.SetMemo(notes)
                spl_ast2.SetMemo(pair_tx[NOTES])
            else:
                # a Distribution, so second split is for a REVENUE account
                spl_rev = Split(book)
                spl_rev.SetParent(gtx)
                # set the Account, Value and Reconciled of the REVENUE split
                spl_rev.SetAccount(rev_acct)
                spl_rev.SetValue(GncNumeric(gross_opp, 100))
                spl_rev.SetReconcile(CREC)
                # set Notes for the Tx and Action for the ASSET split
                gtx.SetNotes(notes)
                spl_ast.SetAction(DIST)

            # ROLL BACK if something went wrong and the two splits DO NOT balance
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

        except Exception as ie:
            print_error("createGncTx() EXCEPTION!! '{}'\n".format(str(ie)))
    # end INNER create_gnc_tx()

    # gnc_file = PRAC2_GNC
    print("\n gncFile = '{}'".format(gnc_file))

    try:
        session = Session(gnc_file)
        book = session.book

        root = book.get_root_account()
        root.get_instance()

        commod_tab = book.get_table()
        session.save()  # really needed?

        CAD = commod_tab.lookup("ISO4217", "CAD")

        # EXPERIMENT
        if mode.lower() == 'prod':

            gnc_collection = copy.deepcopy(Tx_Collection)

            prepare_accounts(PL_OPEN)

            prepare_accounts(PL_TFSA)

            prepare_accounts(PL_RRSP)

            if mode == "PROD":
                print_info("Mode = '{}': Save session.".format(mode), color=GREEN)
                session.save()

        else:
            # just show the account paths
            rev_path = copy.copy(ACCT_PATHS[REVENUE])
            rev_path.append(PL_OPEN)
            show_account(root, rev_path)
            ast_path = copy.copy(ACCT_PATHS[ASSET])
            ast_path.append(PL_OPEN)
            show_account(root, ast_path)

            rev_path.pop()
            rev_path.append(PL_TFSA)
            show_account(root, rev_path)
            ast_path.pop()
            ast_path.append(PL_TFSA)
            show_account(root, ast_path)

            rev_path.pop()
            rev_path.append(PL_RRSP)
            show_account(root, rev_path)
            ast_path.pop()
            ast_path.append(PL_RRSP)
            show_account(root, ast_path)

        session.end()

    except Exception as e:
        print_error("create_gnc_txs() EXCEPTION!! '{}'".format(str(e)))
        if "session" in locals():
            session.end()
        raise
# end create_gnc_txs()


def create_gnc_txs_main():
    usage = "usage: python {0} <monarch json file> <gnucash file> <mode: prod|test>".format(argv[0])
    if len(argv) < 4:
        print_error("NOT ENOUGH parameters!")
        print_info(usage, color=YELLOW)
        exit()

    mon_file = argv[1]
    if not osp.isfile(mon_file):
        print_error("File path '{}' does not exist. Exiting...".format(mon_file))
        print_info(usage, color=YELLOW)
        exit()

    # get Monarch record from the Monarch json file
    with open(mon_file, 'r') as fp:
        # PROBLEM: with Python2, the text in the record will be <type unicode> instead of <type string>
        # and cause an exception if passed to any of the gnucash functions expecting a <const char*>
        # -- easiest solution seems to be to just cast any of this text to str() on definition...
        record = json.load(fp)

    gnc_file = argv[2]
    if not osp.isfile(gnc_file):
        print_error("File path '{}' does not exist. Exiting...".format(gnc_file))
        exit()

    mode = argv[3]

    create_gnc_txs(record, gnc_file, mode)

    print_info("\n >>> PROGRAM ENDED.", color=MAGENTA)


if __name__ == '__main__':
    create_gnc_txs_main()
