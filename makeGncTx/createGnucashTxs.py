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


class ReportInfo:
    def __init__(self, own):
        self.owner = own,
        self.plans = {
            PL_OPEN : [],
            PL_TFSA : [],
            PL_RRSP : []
        }
    
    def get_owner(self):
        return self.owner


class MonarchRecord:
    def __init__(self, cy, fc, td, desc, gr, net, un, pr, ub, acc, nt):
        self.fund_company = cy,
        self.fund_code    = fc,
        self.trade_date   = td,
        self.description  = desc,
        self.gross_amount = gr,
        self.net_amount   = net,
        self.units        = un,
        self.price        = pr,
        self.unit_balance = ub,
        self.account      = acc,
        self.notes        = nt


class GnucashRecord:
    def __init__(self, cy, fc, td, tm, ty, sw, desc, gr, net, un, pr, ub, acc, nt):
        self.fund_company = cy,
        self.fund_code    = fc,
        self.trade_day    = td,
        self.trade_mth    = tm,
        self.trade_yr     = ty,
        self.switch       = sw,
        self.description  = desc,
        self.gross_amount = gr,
        self.net_amount   = net,
        self.units        = un,
        self.price        = pr,
        self.unit_balance = ub,
        self.account      = acc,
        self.notes        = nt


class GncUtilities:
    
    def account_from_path(self, top_account, account_path, original_path=None):
        if original_path is None:
            original_path = account_path
        account, account_path = account_path[0], account_path[1:]
    
        account = top_account.lookup_by_name(account)
        if account is None:
            raise Exception("path " + str(original_path) + " could NOT be found")
        if len(account_path) > 0:
            return self.account_from_path(account, account_path, original_path)
        else:
            return account
    
    def show_account(self, root, path):
        acct = self.account_from_path(root, path)
        acct_name = acct.GetName()
        print_info("account = " + acct_name)
        descendants = acct.get_descendants()
        if len(descendants) == 0:
            print_info("{} has NO Descendants!".format(acct_name))
        else:
            print_info("Descendants of {}:".format(acct_name))
            # for subAcct in descendants:
            # print_info("{}".format(subAcct.GetName()))


class GncTxCreator:

    def __init__(self, tx_collxn, gnc_f, md, pdb=None):
        self.tx_coll = tx_collxn
        self.gnc_file = gnc_f
        self.mode = md
        self.price_db = pdb
        
    gncu = GncUtilities()
    
    def set_pdb(self, pdb):
        self.price_db = pdb
    
    def get_monarch_info(self, mtx, plan_type, ast_parent):
        print_info('get_monarch_info()', MAGENTA)

        # set the regex values needed for matches
        re_gross = re.compile("^(\(?)\$([0-9,]{1,6})\.([0-9]{2})\)?.*")
        re_units = re.compile("^(-?)([0-9]{1,5})\.([0-9]{4}).*")
        re_switch = re.compile("^(" + SWITCH + ")-([InOut]{2,3}).*")
        re_intrf = re.compile("^(" + INTRF + ")-([InOut]{2,3}).*")

        init_tx = {}

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
        asset_acct_name = mtx[FUND_CMPY] + " " + mtx[FUND_CODE]
        print_info("asset_acct_name = '{}'".format(asset_acct_name))

        asset_parent = ast_parent
        # special locations for Trust Revenue and Asset accounts
        if asset_acct_name == TRUST_AST_ACCT:
            asset_parent = self.root.lookup_by_name(TRUST)
            print_info("asset_parent = '{}'".format(asset_parent.GetName()))
            rev_acct = self.root.lookup_by_name(TRUST_REV_ACCT)
            print_info("rev_acct = '{}'".format(rev_acct.GetName()))

        # get the asset account
        asset_acct = asset_parent.lookup_by_name(asset_acct_name)
        if asset_acct is None:
            raise Exception("Could NOT find acct '{}' under parent '{}'".format(asset_acct_name, asset_parent.GetName()))
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
        descr = "{}: {} {}".format(COMPANY_NAME[init_tx[FUND_CMPY]], init_tx[DESC], asset_acct_name)
        print_info("descr = '{}'".format(descr))

        # notes field
        notes = str(asset_acct_name + " balance = " + mtx[UNIT_BAL])
        print_info("notes = '{}'".format(notes))

        # fill in the fields for the switch tx
        init_tx[NOTES] = notes
        init_tx[ACCT]  = asset_acct
        init_tx[GROSS] = gross_curr
        init_tx[UNITS] = units

        pair_tx = None
        have_pair = False
        if switch:
            print_info("Tx is a Switch to OTHER Monarch account.", BLUE)
            # look for switches in same plan type, company, date and opposite gross value
            for itx in self.report_info.plans[plan_type]:
                if itx[FUND_CMPY] == init_tx[FUND_CMPY] and itx[GROSS] == gross_opp \
                        and itx[TRADE_DAY] == init_tx[TRADE_DAY] and itx[TRADE_MTH] == init_tx[TRADE_MTH] :
                    # ALREADY HAVE THE FIRST ITEM OF THE PAIR
                    have_pair = True
                    pair_tx = itx
                    print_info('Found the MATCH of a pair...', YELLOW)
                    break

            if not have_pair:
                # store the tx until we find the matching tx
                self.report_info.plans[plan_type].append(init_tx)
                print_info('Found the FIRST of a pair...\n', YELLOW)

        return init_tx, pair_tx

    def make_gnc_price_and_save(self, tx1, tx2):
        print_info('make_gnc_price_and_save()', MAGENTA)
        pr_date = dt(tx1[TRADE_YR], tx1[TRADE_MTH], tx1[TRADE_DAY])
        datestring = pr_date.strftime("%Y-%m-%d")

        int_price = int((tx1[GROSS] * 100) / (tx1[UNITS] / 10000))
        val = GncNumeric(int_price, 10000)
        print_info("Adding: {}[{}] @ ${}".format(tx1[ACCT].GetName(), datestring, val))

        pr1 = GncPrice(self.book)
        pr1.begin_edit()
        pr1.set_time64(pr_date)
        comm = tx1[ACCT].GetCommodity()
        print_info("Commodity = '{}:{}'".format(comm.get_namespace(), comm.get_printname()))
        pr1.set_commodity(comm)

        pr1.set_currency(self.CAD)
        pr1.set_value(val)
        pr1.set_source_string("user:price")
        pr1.set_typestr('nav')
        pr1.commit_edit()

        if tx1[SWITCH]:
            # get the price for the paired Tx
            int_price = int((tx2[GROSS] * 100) / (tx2[UNITS] / 10000))
            val = GncNumeric(int_price, 10000)
            print_info("Adding: {}[{}] @ ${}".format(tx2[ACCT].GetName(), datestring, val))

            pr2 = GncPrice(self.book)
            pr2.begin_edit()
            pr2.set_time64(pr_date)
            comm = tx2[ACCT].GetCommodity()
            print_info("Commodity = '{}:{}'".format(comm.get_namespace(), comm.get_printname()))
            pr2.set_commodity(comm)

            pr2.set_currency(self.CAD)
            pr2.set_value(val)
            pr2.set_source_string("user:price")
            pr2.set_typestr('nav')
            pr2.commit_edit()

        if self.mode == "PROD":
            print_info("Mode = '{}': Commit Price DB changes.\n".format(self.mode), GREEN)
            self.price_db.add_price(pr1)
            if tx1[SWITCH]:
                self.price_db.add_price(pr2)
        else:
            print_info("Mode = '{}': ABANDON Price DB changes!\n".format(self.mode), RED)

    def make_gnc_tx_and_save(self, tx1, tx2, rev_acct):
        print_info('make_gnc_tx_and_save()', MAGENTA)
        # create a gnucash Tx
        gtx = Transaction(self.book)
        # gets a guid on construction
    
        gtx.BeginEdit()
    
        gtx.SetCurrency(self.CAD)
        gtx.SetDate(tx1[TRADE_DAY], tx1[TRADE_MTH], tx1[TRADE_YR])
        print_info("gtx date = '{}'".format(gtx.GetDate()))
        gtx.SetDescription(tx1[DESC])
    
        # create the ASSET split for the Tx
        spl_ast = Split(self.book)
        spl_ast.SetParent(gtx)
        # set the account, value, and units of the Asset split
        spl_ast.SetAccount(tx1[ACCT])
        spl_ast.SetValue(GncNumeric(tx1[GROSS], 100))
        spl_ast.SetAmount(GncNumeric(tx1[UNITS], 10000))
    
        if tx1[SWITCH]:
            # create the second ASSET split for the Tx
            spl_ast2 = Split(self.book)
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
            spl_rev = Split(self.book)
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
    
        if self.mode == "PROD":
            print_info("Mode = '{}': Commit transaction changes.\n".format(self.mode))
            gtx.CommitEdit()
        else:
            print_info("Mode = '{}': Roll back transaction changes!\n".format(self.mode))
            gtx.RollbackEdit()
    
    def extract_gnc_info(self, mtx, plan_type, ast_parent, rev_acct):
        """
        Asset accounts: use the proper path to find the parent then search for the Fund Code in the descendants
        Revenue accounts: pick the proper account based on owner and plan type
        gross_curr: re match to Gross then concatenate the two match groups
        date: re match to get day, month and year then re-assemble to form Gnc date
        Units: re match and concatenate the two groups on either side of decimal point
        Description: use DESC and Fund Code
        Notes: use 'Unit Balance' and UNIT_BAL
        :param mtx:
        :param plan_type:
        :param rev_acct:
        :param ast_parent:
        :return: nil
        """
        try:
            print_info('extract_gnc_info()', MAGENTA)
    
            # get the additional required information from the Monarch json
            tx1, tx2 = self.get_monarch_info(mtx, plan_type, ast_parent)
    
            # just return if we need the matching tx and don't have it yet
            if tx1[SWITCH] and tx2 is None:
                return
    
            # =================================================================================================
            # MOVE TO A SEPARATE FUNCTION TO CREATE PRICES TO ADD TO THE PRICE DB
            self.make_gnc_price_and_save(tx1, tx2)
    
            # =================================================================================================
            # MOVE TO A SEPARATE FUNCTION TO CREATE A GNC TX
            self.make_gnc_tx_and_save(tx1, tx2, rev_acct)
    
        except Exception as ie:
            print_error("extract_gnc_info() EXCEPTION!! '{}'\n".format(str(ie)))
    
    # noinspection PyShadowingNames
    def prepare_accounts(self):
        for key in self.tx_coll:
            if key != OWNER:
                plan_type = key
                
                self.root = self.book.get_root_account()
                self.root.get_instance()
        
                self.price_db = self.book.get_price_db()
                self.price_db.begin_edit()
        
                commod_tab = self.book.get_table()
                
                self.CAD = commod_tab.lookup("ISO4217", "CAD")
        
                print_info("\n\nPlan type = '{}'".format(plan_type))
        
                rev_path = copy.copy(ACCT_PATHS[REVENUE])
                # print_info("rev_path = '{}'".format(str(rev_path)))
                rev_path.append(plan_type)
                # print_info("rev_path = '{}'".format(str(rev_path)))
                ast_parent_path = copy.copy(ACCT_PATHS[ASSET])
                ast_parent_path.append(plan_type)
                
                pl_owner = self.report_info.get_owner()
                if plan_type != PL_OPEN:
                    if pl_owner == '':
                        raise Exception("PROBLEM!! Trying to process plan type '{}' but NO Owner value found"
                                        " in Tx Collection!!".format(plan_type))
                    rev_path.append(ACCT_PATHS[pl_owner])
                    ast_parent_path.append(ACCT_PATHS[pl_owner])
    
                print_info("rev_path = '{}'".format(str(rev_path)))
                rev_acct = self.gncu.account_from_path(self.root, rev_path)
                print_info("rev_acct = '{}'".format(rev_acct.GetName()))
    
                print_info("ast_parent_path = '{}'".format(str(ast_parent_path)))
                asset_parent = self.gncu.account_from_path(self.root, ast_parent_path)
                print_info("ast_parent = '{}'".format(asset_parent.GetName()))
    
                for mtx in self.tx_coll[plan_type]:
                    self.extract_gnc_info(mtx, plan_type, asset_parent, rev_acct)

    # noinspection PyPep8,PyUnboundLocalVariable
    def create_gnc_txs(self):
        """
        Take the information from a transaction collection and produce Gnucash transactions to write to a Gnucash file
        :return: nil
        """
        print_info("\ngncFile = '{}'".format(self.gnc_file))

        try:
            session = Session(self.gnc_file)
            self.book = session.book

            self.report_info = ReportInfo(self.tx_coll[OWNER])
            self.prepare_accounts()

            # self.prepare_accounts(mode, book, PL_TFSA, mon_coll, gnc_coll)
            # 
            # self.prepare_accounts(mode, book, PL_RRSP, mon_coll, gnc_coll)

            if self.mode == "PROD":
                print_info("Mode = '{}': Save session.".format(self.mode), GREEN)
                self.price_db.commit_edit()
                # only ONE session save for the entire run
                session.save()

            session.end()
            session.destroy()

        except Exception as e:
            print_error("create_gnc_txs() EXCEPTION!! '{}'".format(str(e)))
            if "session" in locals() and session is not None:
                session.end()
                session.destroy()
            raise


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

    mode = argv[3].upper()

    gtc = GncTxCreator(tx_collxn, gnc_file, mode)
    gtc.create_gnc_txs()

    print_info("\n >>> PROGRAM ENDED.", MAGENTA)


if __name__ == '__main__':
    create_gnc_txs_main()
