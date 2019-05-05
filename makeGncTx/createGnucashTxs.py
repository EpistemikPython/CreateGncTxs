#
# createGnucashTxs.py -- parse a Monarch record, possibly from a json file,
#                        create Gnucash transactions from the data and write to a Gnucash file
#
# Copyright (c) 2018,2019 Mark Sattolo <epistemik@gmail.com>
#
# @author Mark Sattolo <epistemik@gmail.com>
# @version Python 3.6
# @created 2018
# @updated 2019-05-05

import copy
import json
import os.path as osp
import re
from datetime import datetime as dt
from sys import argv
from gnucash import Session, Transaction, Split, GncNumeric, GncPrice
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
    print_info("account = " + acct_name)
    descendants = acct.get_descendants()
    if len(descendants) == 0:
        print_info("{} has NO Descendants!".format(acct_name))
    else:
        print_info("Descendants of {}:".format(acct_name))
        # for subAcct in descendants:
            # print_info("{}".format(subAcct.GetName()))


# noinspection PyPep8,PyUnboundLocalVariable
def create_gnc_txs(tx_colxn, gnc_file, mode):
    """
    Take the information from a transaction collection and produce Gnucash transactions to write to a Gnucash file
    """
    # set the regex values needed for matches
    re_gross  = re.compile("^(\(?)\$([0-9,]{1,6})\.([0-9]{2})\)?.*")
    re_units  = re.compile("^(-?)([0-9]{1,5})\.([0-9]{4}).*")
    re_date   = re.compile("^([0-9]{2})/([0-9]{2})/([0-9]{4}).*")
    re_switch = re.compile("^(" + SWITCH + ")-([InOut]{2,3}).*")
    re_intrf  = re.compile("^(" + INTRF + ")-([InOut]{2,3}).*")

    # noinspection PyShadowingNames
    def prepare_accounts(plan_type):
        if plan_type in tx_colxn:
            print_info("\n\nPlan type = '{}'".format(plan_type))

            rev_path = copy.copy(ACCT_PATHS[REVENUE])
            # print_info("rev_path = '{}'".format(str(rev_path)))
            rev_path.append(plan_type)
            # print_info("rev_path = '{}'".format(str(rev_path)))
            ast_parent_path = copy.copy(ACCT_PATHS[ASSET])
            ast_parent_path.append(plan_type)

            if plan_type != PL_OPEN:
                pl_owner = tx_colxn[OWNER]
                if pl_owner == '':
                    raise Exception(
                        "PROBLEM!! Trying to process plan type '{}' but NO Owner value found in Tx Collection!!".format(plan_type))
                rev_path.append(ACCT_PATHS[pl_owner])
                ast_parent_path.append(ACCT_PATHS[pl_owner])

            print_info("rev_path = '{}'".format(str(rev_path)))
            rev_acct = account_from_path(root, rev_path)
            print_info("rev_acct = '{}'".format(rev_acct.GetName()))

            print_info("ast_parent_path = '{}'".format(str(ast_parent_path)))
            ast_parent = account_from_path(root, ast_parent_path)
            print_info("ast_parent = '{}'".format(ast_parent.GetName()))

            for mtx in tx_colxn[plan_type]:
                create_gnc_tx(mtx, plan_type, rev_acct, ast_parent)
    # end INNER prepare_accounts()

    # noinspection PyUnboundLocalVariable
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
            fund_company = mtx[FUND_CMPY]
            desc = mtx[DESC]
            trade_date = mtx[TRADE_DATE]
            gross_value = mtx[GROSS]

            # check if we have a switch/transfer
            if re.match(re_switch, desc) or re.match(re_intrf, desc):
                transfer = True

            # get the asset account name
            ast_acct_name = fund_company + " " + mtx[FUND_CODE]
            print_info("ast_acct_name = '{}'".format(ast_acct_name))
            print_info("type(ast_acct_name) = '{}'".format(type(ast_acct_name)))
            ast_acct_str = str(ast_acct_name)
            print_info("ast_acct_str = '{}'".format(ast_acct_str))
            print_info("type(ast_acct_str) = '{}'".format(type(ast_acct_str)))

            # special locations for Trust Revenue and Asset accounts
            if ast_acct_name == TRUST_AST_ACCT:
                ast_parent = root.lookup_by_name(TRUST)
                print_info("ast_parent = '{}'".format(ast_parent.GetName()))
                rev_acct = root.lookup_by_name(TRUST_REV_ACCT)
                print_info("rev_acct = '{}'".format(rev_acct.GetName()))

            # get the asset account
            ast_acct = ast_parent.lookup_by_name(ast_acct_str)
            if ast_acct is None:
                raise Exception("Could NOT find acct '{}' under parent '{}'".format(ast_acct_name, ast_parent.GetName()))
            else:
                print_info("ast_acct = '{}'".format(ast_acct.GetName()), color=CYAN)

            # get the dollar value of the tx
            # print_info('flag1')
            re_match = re.match(re_gross, gross_value)
            # print_info('flag2')
            if re_match:
                # print(re_match.groups())
                str_gross_curr = re_match.group(2) + re_match.group(3)
                # remove possible comma
                gross_curr = int(str_gross_curr.replace(',', ''))
                # if match group 1 is not empty, amount is negative
                if re_match.group(1) != '':
                    gross_curr *= -1
                print_info("gross_curr = '{}'".format(gross_curr))
                gross_opp = gross_curr * -1
                print_info("gross_opp = '{}'".format(gross_opp))
            else:
                raise Exception("PROBLEM!! re_gross DID NOT match with value '{}'!".format(gross_value))

            # get the units of the tx
            re_match = re.match(re_units, mtx[UNITS])
            if re_match:
                # print(re_match.groups())
                units = int(re_match.group(2) + re_match.group(3))
                # if match group 1 is not empty, units is negative
                if re_match.group(1) != '':
                    units *= -1
                print_info("units = '{}'".format(units))
            else:
                raise Exception("PROBLEM!! re_units DID NOT match with value '{}'!".format(mtx[UNITS]))

            # get the date items
            re_match = re.match(re_date, trade_date)
            if re_match:
                # print(re_match.groups())
                trade_mth = int(re_match.group(1))
                print_info("trade_mth = '{}'".format(trade_mth))
                trade_day = int(re_match.group(2))
                print_info("trade_day = '{}'".format(trade_day))
                trade_yr = int(re_match.group(3))
                print_info("trade_yr = '{}'".format(trade_yr))
            else:
                raise Exception("PROBLEM!! reTRADE_DATE DID NOT match with value '{}'!".format(trade_date))

            # assemble the Description string
            descr = str(COMPANY_NAME[fund_company] + ": " + desc + " " + ast_acct_name)
            print_info("descr = '{}'".format(descr))

            # notes field
            notes = str(ast_acct_name + " balance = " + mtx[UNIT_BAL])
            print_info("notes = '{}'".format(notes))

            # check the type of tx -- a Distribution OR the first or second item of a switch/transfer pair
            have_pair = False
            if transfer:
                print_info("transfer")
                # look for switches in same plan type, company, date and opposite gross value
                for itx in gnc_collection[plan_type]:
                    if itx[FUND_CMPY] == fund_company and itx[TRADE_DATE] == trade_date and itx[GROSS] == gross_opp:
                        # already have the first item of the pair
                        have_pair = True
                        pair_tx = itx
                        break

                if not have_pair:
                    # create a new switch tx
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
                    print_info('')
                    return

            # =================================================================================================
            # MOVE TO A SEPARATE FUNCTION TO CREATE PRICES TO ADD TO THE PRICE DB

            pr_date = dt(trade_yr, trade_mth, trade_day)
            datestring = pr_date.strftime("%Y-%m-%d")

            int_price = int((gross_curr*100) / (units/10000))
            val = GncNumeric(int_price, 10000)
            print_info("Adding: {}[{}] @ ${}".format(ast_acct_name, datestring, val))

            pr1 = GncPrice(book)
            pr1.begin_edit()
            pr1.set_time64(pr_date)
            comm = ast_acct.GetCommodity()
            print_info("Commodity = '{}:{}'".format(comm.get_namespace(), comm.get_printname()))
            pr1.set_commodity(comm)

            pr1.set_currency(CAD)
            pr1.set_value(val)
            pr1.set_source_string("user:price")
            pr1.set_typestr('nav')
            pr1.commit_edit()

            if transfer:
                # get the price for the paired Tx
                int_price = int((pair_tx[GROSS] * 100) / (pair_tx[UNITS] / 10000))
                val = GncNumeric(int_price, 10000)
                print_info("Adding: {}[{}] @ ${}".format(pair_tx[ACCT].GetName(), datestring, val))

                pr2 = GncPrice(book)
                pr2.begin_edit()
                pr2.set_time64(pr_date)
                comm = pair_tx[ACCT].GetCommodity()
                print_info("Commodity = '{}:{}'".format(comm.get_namespace(), comm.get_printname()))
                pr2.set_commodity(comm)

                pr2.set_currency(CAD)
                pr2.set_value(val)
                pr2.set_source_string("user:price")
                pr2.set_typestr('nav')
                pr2.commit_edit()

            if mode == "PROD":
                print_info("Mode = '{}': Commit Price DB changes.\n".format(mode))
                pdb.add_price(pr1)
                if transfer:
                    pdb.add_price(pr2)
            else:
                print_info("Mode = '{}': ABANDON Price DB changes!\n".format(mode))

            # =================================================================================================
            # MOVE TO A SEPARATE FUNCTION TO CREATE A GNC TX

            # create a gnucash Tx
            gtx = Transaction(book)
            # gets a guid on construction
            print_info("gtx guid = '{}'".format(gtx.GetGUID().to_string()))

            gtx.BeginEdit()

            gtx.SetCurrency(CAD)
            gtx.SetDate(trade_day, trade_mth, trade_yr)
            print_info("gtx date = '{}'".format(gtx.GetDate()))
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
                print_error("gtx Imbalance = '{}'!! Roll back transaction changes!".format(gtx.GetImbalanceValue().to_string()))
                gtx.RollbackEdit()
                return

            if mode == "PROD":
                print_info("Mode = '{}': Commit transaction changes.\n".format(mode))
                gtx.CommitEdit()
                # NO >> session.save()
            else:
                print_info("Mode = '{}': Roll back transaction changes!\n".format(mode))
                gtx.RollbackEdit()

        except Exception as ie:
            print_error("create_gnc_tx() EXCEPTION!! '{}'\n".format(str(ie)))
    # end INNER create_gnc_tx()

    print_info("\ngncFile = '{}'".format(gnc_file))

    try:
        session = Session(gnc_file)
        book = session.book

        root = book.get_root_account()
        root.get_instance()

        pdb = book.get_price_db()
        pdb.begin_edit()

        commod_tab = book.get_table()
        # noinspection PyPep8Naming
        CAD = commod_tab.lookup("ISO4217", "CAD")

        if mode.lower() == 'prod':

            gnc_collection = copy.deepcopy(Tx_Collection)

            prepare_accounts(PL_OPEN)

            prepare_accounts(PL_TFSA)

            prepare_accounts(PL_RRSP)

            if mode == "PROD":
                print_info("Mode = '{}': Save session.".format(mode), GREEN)
                pdb.commit_edit()
                # only ONE session save for the entire run
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
        session.destroy()

    except Exception as e:
        print_error("create_gnc_txs() EXCEPTION!! '{}'".format(str(e)))
        if "session" in locals() and session is not None:
            session.end()
            session.destroy()
        raise
# end create_gnc_txs()


def create_gnc_txs_main():
    exe = argv[0].split('/')[-1]
    usage = "usage: python {} <monarch json file> <gnucash file> <mode: prod|test>".format(exe)
    if len(argv) < 4:
        print_error("NOT ENOUGH parameters!")
        print_info(usage, MAGENTA)
        exit()

    mon_file = argv[1]
    if not osp.isfile(mon_file):
        print_error("File path '{}' does not exist. Exiting...".format(mon_file))
        print_info(usage, GREEN)
        exit()

    # get Monarch transactions from the Monarch json file
    with open(mon_file, 'r') as fp:
        tx_collxn = json.load(fp)

    gnc_file = argv[2]
    if not osp.isfile(gnc_file):
        print_error("File path '{}' does not exist. Exiting...".format(gnc_file))
        exit()

    mode = argv[3]

    create_gnc_txs(tx_collxn, gnc_file, mode)

    print_info("\n >>> PROGRAM ENDED.", MAGENTA)


if __name__ == '__main__':
    create_gnc_txs_main()
