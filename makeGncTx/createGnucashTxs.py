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


# noinspection PyPep8,PyUnboundLocalVariable,PyUnresolvedReferences
def create_gnc_txs(tx_colxn, gnc_file, mode):
    """
    Take the information from a transaction collection and produce Gnucash transactions to write to a Gnucash file
    """
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
                extract_gnc_info(mtx, plan_type, rev_acct, ast_parent)
    # end INNER prepare_accounts()

    # noinspection PyUnboundLocalVariable
    def extract_gnc_info(mtx, plan_type, rev_acct, ast_parent):
        """
        Asset accounts: use the proper path to find the parent then search for the Fund Code in the descendants
        Revenue accounts: pick the proper account based on owner and plan type
        gross_curr: re match to Gross then concatenate the two match groups
        date: re match to get day, month and year then re-assemble to form Gnc date
        Units: re match and concatenate the two groups on either side of decimal point
        Description: use DESC and Fund Code
        Notes: use 'Unit Balance' and UNIT_BAL
        """
        def get_monarch_info():
            print_info('get_monarch_info()', MAGENTA)

            # set the regex values needed for matches
            re_gross = re.compile("^(\(?)\$([0-9,]{1,6})\.([0-9]{2})\)?.*")
            re_units = re.compile("^(-?)([0-9]{1,5})\.([0-9]{4}).*")
            re_switch = re.compile("^(" + SWITCH + ")-([InOut]{2,3}).*")
            re_intrf = re.compile("^(" + INTRF + ")-([InOut]{2,3}).*")

            init_tx = copy.deepcopy(Gnucash_Tx)

            init_tx[FUND_CMPY] = mtx[FUND_CMPY]
            init_tx[DESC] = mtx[DESC]

            print_info("trade date = '{}'".format(mtx[TRADE_DATE]))
            trade_date = mtx[TRADE_DATE].split('/')
            init_tx[TRADE_DAY] = int(trade_date[1])
            init_tx[TRADE_MTH] = int(trade_date[0])
            init_tx[TRADE_YR]  = int(trade_date[2])
            print_info("trade day/month/year = '{}/{}/{}'".format(init_tx[TRADE_DAY],init_tx[TRADE_MTH],init_tx[TRADE_YR]))

            # check if we have a switch/transfer
            switch = True if (re.match(re_switch, mtx[DESC]) or re.match(re_intrf, mtx[DESC])) else False
            init_tx[SWITCH] = switch
            print_info("{} Have a Switch.".format('DO NOT' if not switch else ''), BLUE)

            # get the asset account name
            ast_acct_name = mtx[FUND_CMPY] + " " + mtx[FUND_CODE]
            print_info("ast_acct_name = '{}'".format(ast_acct_name))

            asset_parent = ast_parent
            # special locations for Trust Revenue and Asset accounts
            if ast_acct_name == TRUST_AST_ACCT:
                asset_parent = root.lookup_by_name(TRUST)
                print_info("ast_parent = '{}'".format(ast_parent.GetName()))
                rev_acct = root.lookup_by_name(TRUST_REV_ACCT)
                print_info("rev_acct = '{}'".format(rev_acct.GetName()))

            # get the asset account
            asset_acct = asset_parent.lookup_by_name(ast_acct_name)
            if asset_acct is None:
                raise Exception("Could NOT find acct '{}' under parent '{}'".format(ast_acct_name, ast_parent.GetName()))
            else:
                print_info("asset_acct = '{}'".format(asset_acct.GetName()), color=CYAN)

            # get the dollar value of the tx
            re_match = re.match(re_gross, mtx[GROSS])
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
                raise Exception("PROBLEM!! re_gross DID NOT match with value '{}'!".format(mtx[GROSS]))

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

            # assemble the Description string
            descr = str(COMPANY_NAME[init_tx[FUND_CMPY]] + ": " + init_tx[DESC] + " " + ast_acct_name)
            print_info("descr = '{}'".format(descr))

            # notes field
            notes = str(ast_acct_name + " balance = " + mtx[UNIT_BAL])
            print_info("notes = '{}'".format(notes))

            # fill in the fields for the switch tx
            init_tx[NOTES] = notes
            init_tx[ACCT]  = asset_acct
            init_tx[GROSS] = gross_curr
            init_tx[UNITS] = units

            # check the type of tx -- a Distribution OR the first or second item of a switch/transfer pair
            pair_tx = None
            have_pair = False
            if switch:
                print_info("Tx is a Switch to OTHER Monarch account.", BLUE)
                # look for switches in same plan type, company, date and opposite gross value
                for itx in gnc_collection[plan_type]:
                    if itx[FUND_CMPY] == init_tx[FUND_CMPY] and itx[GROSS] == gross_opp \
                            and itx[TRADE_DAY] == init_tx[TRADE_DAY] and itx[TRADE_MTH] == init_tx[TRADE_MTH] :
                        # ALREADY HAVE THE FIRST ITEM OF THE PAIR
                        have_pair = True
                        pair_tx = itx
                        print_info('Found the MATCH of a pair...', YELLOW)
                        break

                if not have_pair:
                    # store the tx until we find the matching tx
                    gnc_collection[plan_type].append(init_tx)
                    print_info('Found the FIRST of a pair...\n', YELLOW)

            return init_tx, pair_tx
        # END INNER get_monarch_info()

        def make_gnc_price_and_save():
            print_info('make_gnc_price_and_save()', MAGENTA)
            pr_date = dt(tx1[TRADE_YR], tx1[TRADE_MTH], tx1[TRADE_DAY])
            datestring = pr_date.strftime("%Y-%m-%d")

            int_price = int((tx1[GROSS] * 100) / (tx1[UNITS] / 10000))
            val = GncNumeric(int_price, 10000)
            print_info("Adding: {}[{}] @ ${}".format(tx1[ACCT].GetName(), datestring, val))

            pr1 = GncPrice(book)
            pr1.begin_edit()
            pr1.set_time64(pr_date)
            comm = tx1[ACCT].GetCommodity()
            print_info("Commodity = '{}:{}'".format(comm.get_namespace(), comm.get_printname()))
            pr1.set_commodity(comm)

            pr1.set_currency(CAD)
            pr1.set_value(val)
            pr1.set_source_string("user:price")
            pr1.set_typestr('nav')
            pr1.commit_edit()

            if tx1[SWITCH]:
                # get the price for the paired Tx
                int_price = int((tx2[GROSS] * 100) / (tx2[UNITS] / 10000))
                val = GncNumeric(int_price, 10000)
                print_info("Adding: {}[{}] @ ${}".format(tx2[ACCT].GetName(), datestring, val))

                pr2 = GncPrice(book)
                pr2.begin_edit()
                pr2.set_time64(pr_date)
                comm = tx2[ACCT].GetCommodity()
                print_info("Commodity = '{}:{}'".format(comm.get_namespace(), comm.get_printname()))
                pr2.set_commodity(comm)

                pr2.set_currency(CAD)
                pr2.set_value(val)
                pr2.set_source_string("user:price")
                pr2.set_typestr('nav')
                pr2.commit_edit()
            if mode == "PROD":
                print_info("Mode = '{}': Commit Price DB changes.\n".format(mode), GREEN)
                pdb.add_price(pr1)
                if tx1[SWITCH]:
                    pdb.add_price(pr2)
            else:
                print_info("Mode = '{}': ABANDON Price DB changes!\n".format(mode), RED)
        # END INNER make_gnc_price_and_save()

        def make_gnc_tx_and_save():
            print_info('make_gnc_tx_and_save()', MAGENTA)
            # create a gnucash Tx
            gtx = Transaction(book)
            # gets a guid on construction

            gtx.BeginEdit()

            gtx.SetCurrency(CAD)
            gtx.SetDate(tx1[TRADE_DAY], tx1[TRADE_MTH], tx1[TRADE_YR])
            print_info("gtx date = '{}'".format(gtx.GetDate()))
            gtx.SetDescription(tx1[DESC])

            # create the ASSET split for the Tx
            spl_ast = Split(book)
            spl_ast.SetParent(gtx)
            # set the account, value, and units of the Asset split
            spl_ast.SetAccount(tx1[ACCT])
            spl_ast.SetValue(GncNumeric(tx1[GROSS], 100))
            spl_ast.SetAmount(GncNumeric(tx1[UNITS], 10000))

            if tx1[SWITCH]:
                # create the second ASSET split for the Tx
                spl_ast2 = Split(book)
                spl_ast2.SetParent(gtx)
                # set the Account, Value, and Units of the second ASSET split
                spl_ast2.SetAccount(tx2[ACCT])
                spl_ast2.SetValue(GncNumeric(tx2[GROSS], 100))
                spl_ast2.SetAmount(GncNumeric(tx2[UNITS], 10000))
                # set Actions for the splits
                spl_ast2.SetAction("Buy" if tx1[UNITS] < 0 else "Sell")
                spl_ast.SetAction("Buy" if tx1[UNITS] > 0 else "Sell")
                # combine Notes for the Tx and set Memos for the splits
                gtx.SetNotes(tx1[NOTES] + " | " + tx2[NOTES])
                spl_ast.SetMemo(tx1[NOTES])
                spl_ast2.SetMemo(tx2[NOTES])
            else:
                # a Distribution, so the second split is for a REVENUE account
                spl_rev = Split(book)
                spl_rev.SetParent(gtx)
                # set the Account, Value and Reconciled of the REVENUE split
                spl_rev.SetAccount(rev_acct)
                rev_gross = tx1[GROSS] * -1
                print_info("rev gross = '{}'".format(rev_gross))
                spl_rev.SetValue(GncNumeric(rev_gross, 100))
                spl_rev.SetReconcile(CREC)
                # set Notes for the Tx and Action for the ASSET split
                gtx.SetNotes(tx1[NOTES])
                spl_ast.SetAction(DIST)

            # ROLL BACK if something went wrong and the two splits DO NOT balance
            if not gtx.GetImbalanceValue().zero_p():
                print_error("gtx Imbalance = '{}'!! Roll back transaction changes!".format(gtx.GetImbalanceValue().to_string()))
                gtx.RollbackEdit()
                return

            if mode == "PROD":
                print_info("Mode = '{}': Commit transaction changes.\n".format(mode))
                gtx.CommitEdit()
            else:
                print_info("Mode = '{}': Roll back transaction changes!\n".format(mode))
                gtx.RollbackEdit()
        # END INNER make_gnc_tx_and_save()

        try:
            print_info('extract_gnc_info(): START LOOP', MAGENTA)

            # get the additional required information from the Monarch json
            tx1, tx2 = get_monarch_info()

            # just return if we need the matching tx and don't have it yet
            if tx1[SWITCH] and tx2 is None:
                return

            # =================================================================================================
            # MOVE TO A SEPARATE FUNCTION TO CREATE PRICES TO ADD TO THE PRICE DB
            make_gnc_price_and_save()

            # =================================================================================================
            # MOVE TO A SEPARATE FUNCTION TO CREATE A GNC TX
            make_gnc_tx_and_save()

        except Exception as ie:
            print_error("extract_gnc_info() EXCEPTION!! '{}'\n".format(str(ie)))
    # end INNER extract_gnc_info()

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
