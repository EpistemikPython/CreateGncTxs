###############################################################################################################################
# coding=utf-8
#
# gnucashSession.py -- create and manage a Gnucash session, create Gnucash price and trade transactions
#                      from an InvestmentRecord
#
# Copyright (c) 2019 Mark Sattolo <epistemik@gmail.com>
#
__author__ = 'Mark Sattolo'
__author_email__ = 'epistemik@gmail.com'
__python_version__ = 3.6
__created__ = '2019-07-01'
__updated__ = '2019-07-30'

import copy
import re
from gnucash import Session, Transaction, Split, GncNumeric, GncPrice
from gnucash.gnucash_core_c import CREC
from Configuration import *


# TODO: standard functions to create Gnucash session, prices, transactions
# noinspection PyUnresolvedReferences,PyUnboundLocalVariable
class GnucashSession:
    """
    Create and manage a Gnucash session
    """
    def __init__(self, p_mrec, p_mode, p_gncfile, p_debug, p_domain, 
                 p_pdb=None, p_book=None, p_root=None, p_curr=None, p_grec=None):
        self.logger = Gnulog(p_debug)
        self.monarch_record = p_mrec
        self.gnucash_record = p_grec
        self.gnc_file  = p_gncfile
        self.mode      = p_mode
        self.domain    = p_domain
        self.price_db  = p_pdb
        self.book      = p_book
        self.root_acct = p_root
        self.currency  = p_curr
        self.gnc_util  = GncUtilities()
        self.logger.print_info("class GnucashSession: Runtime = {}\n".format(dt.now().strftime(DATE_STR_FORMAT)), MAGENTA)

    def set_gnc_rec(self, p_gncrec):
        self.gnucash_record = p_gncrec

    def get_trade_info(self, mtx, plan_type, ast_parent, rev_acct):
        """
        Parse the Monarch trade transactions from a copy&paste JSON file
        Asset accounts: use the proper path to find the parent then search for the Fund Code in the descendants
        Revenue accounts: pick the proper account based on owner and plan type
        gross_curr: re match to Gross then concatenate the two match groups
        date: convert the date then get day, month and year to form a Gnc date
        Units: re match and concatenate the two groups on either side of decimal point
        Description: use DESC and Fund Company
        :param        mtx: dict: Monarch copied trade tx information
        :param  plan_type:  str: Plans from a Configuration.InvestmentRecord
        :param ast_parent: Gnucash account: Asset parent
        :param   rev_acct: Gnucash account: Revenue
        :return: dict, dict
        """
        self.logger.print_info('get_trade_info()', BLUE)

        # set the regex needed to match the required groups in each value
        re_gross  = re.compile(r"^(-?)\$([0-9,]{1,6})\.([0-9]{2}).*")
        re_units  = re.compile(r"^(-?)([0-9]{1,5})\.([0-9]{4}).*")

        fund_name = mtx[FUND]

        # self.dbg.print_info("trade date = {}".format(mtx[TRADE_DATE]))
        conv_date = dt.strptime(mtx[TRADE_DATE], "%d-%b-%Y")
        # self.dbg.print_info("converted date = {}".format(conv_date))
        init_tx = { FUND:fund_name, TRADE_DATE:mtx[TRADE_DATE], 
                    TRADE_DAY:conv_date.day, TRADE_MTH:conv_date.month, TRADE_YR:conv_date.year }
        self.logger.print_info("trade day-month-year = '{}-{}-{}'"
                               .format(init_tx[TRADE_DAY], init_tx[TRADE_MTH], init_tx[TRADE_YR]))

        # check if we have a switch-in/out
        sw_ind = mtx[DESC].split()[-1]
        switch = True if sw_ind == SW_IN or sw_ind == SW_OUT else False
        init_tx[SWITCH] = switch
        self.logger.print_info("{} Have a Switch!".format('***' if switch else 'DO NOT'), BLUE)

        asset_acct, rev_acct = self.get_accounts(ast_parent, fund_name, rev_acct)
        init_tx[ACCT] = asset_acct
        # save the (possibly modified) Revenue account to the Gnc tx
        init_tx[REVENUE] = rev_acct

        # get the dollar value of the tx
        re_match = re.match(re_gross, mtx[GROSS])
        if re_match:
            str_gross_curr = re_match.group(2) + re_match.group(3)
            # remove possible comma
            gross_curr = int(str_gross_curr.replace(',', ''))
            # if match group 1 is not empty, amount is negative
            if re_match.group(1) != '':
                gross_curr *= -1
            self.logger.print_info("gross_curr = {}".format(gross_curr))
            init_tx[GROSS] = gross_curr
        else:
            raise Exception("PROBLEM[100]!! re_gross DID NOT match with value '{}'!".format(mtx[GROSS]))

        # get the units of the tx
        re_match = re.match(re_units, mtx[UNITS])
        if re_match:
            units = int(re_match.group(2) + re_match.group(3))
            # if match group 1 is not empty, units is negative
            if re_match.group(1) != '':
                units *= -1
            init_tx[UNITS] = units
            self.logger.print_info("units = {}".format(units))
        else:
            raise Exception("PROBLEM[105]!! re_units DID NOT match with value '{}'!".format(mtx[UNITS]))

        # assemble the Description string
        descr = "{} {}".format(mtx[DESC], fund_name)
        init_tx[DESC] = descr
        self.logger.print_info("descr = {}".format(init_tx[DESC]), CYAN)

        # notes field
        notes = mtx[NOTES] if NOTES in mtx else "{} Load = {}".format(fund_name, mtx[LOAD])
        init_tx[NOTES] = notes
        self.logger.print_info("notes = {}".format(init_tx[NOTES]), CYAN)

        pair_tx = None
        have_pair = False
        if switch:
            self.logger.print_info("Tx is a Switch to OTHER Monarch account.", BLUE)
            # look for switches in this plan type with same company, day, month and opposite gross value
            for itx in self.gnucash_record.plans[plan_type][TRADE]:
                if itx[SWITCH] and itx[FUND].split()[0] == init_tx[FUND].split()[0] and itx[GROSS] == (gross_curr * -1) \
                        and itx[TRADE_DATE] == init_tx[TRADE_DATE] :
                    # ALREADY HAVE THE FIRST ITEM OF THE PAIR
                    have_pair = True
                    pair_tx = itx
                    self.logger.print_info('*** Found the MATCH of a pair ***', YELLOW)
                    break

            if not have_pair:
                # store the tx until we find the matching tx
                self.gnucash_record.plans[plan_type][TRADE].append(init_tx)
                self.logger.print_info('Found the FIRST of a pair...\n', YELLOW)

        return init_tx, pair_tx

    def get_accounts(self, ast_parent, asset_acct_name, rev_acct):
        """
        Find the proper Asset and Revenue accounts
        :param      ast_parent: Gnucash account: Asset account parent
        :param asset_acct_name:             str: Asset account name
        :param        rev_acct: Gnucash account: Revenue account
        :return: Gnucash account, Gnucash account
        """
        self.logger.print_info('get_accounts()', BLUE)
        asset_parent = ast_parent
        # special locations for Trust Revenue and Asset accounts
        if asset_acct_name == TRUST_AST_ACCT:
            asset_parent = self.root_acct.lookup_by_name(TRUST)
            self.logger.print_info("asset_parent = {}".format(asset_parent.GetName()))
            rev_acct = self.root_acct.lookup_by_name(TRUST_REV_ACCT)
            self.logger.print_info("MODIFIED rev_acct = {}".format(rev_acct.GetName()))
        # get the asset account
        asset_acct = asset_parent.lookup_by_name(asset_acct_name)
        if asset_acct is None:
            raise Exception("[164] Could NOT find acct '{}' under parent '{}'"
                            .format(asset_acct_name, asset_parent.GetName()))

        self.logger.print_info("asset_acct = {}".format(asset_acct.GetName()), color=CYAN)
        return asset_acct, rev_acct

    def create_gnc_price_txs(self, mtx, ast_parent, rev_acct):
        """
        Create and load Gnucash prices to the Gnucash PriceDB
        :param        mtx: InvestmentRecord transaction
        :param ast_parent: Gnucash account
        :param   rev_acct: Gnucash account
        :return: nil
        """
        self.logger.print_info('create_gnc_price_txs()', BLUE)
        conv_date = dt.strptime(mtx[DATE], "%d-%b-%Y")
        pr_date = dt(conv_date.year, conv_date.month, conv_date.day)
        datestring = pr_date.strftime("%Y-%m-%d")

        fund_name = mtx[FUND]
        if fund_name in MONEY_MKT_FUNDS:
            return

        int_price = int(mtx[PRICE].replace('.', '').replace('$', ''))
        val = GncNumeric(int_price, 10000)
        self.logger.print_info("Adding: {}[{}] @ ${}".format(fund_name, datestring, val))

        pr1 = GncPrice(self.book)
        pr1.begin_edit()
        pr1.set_time64(pr_date)

        asset_acct, rev_acct = self.get_accounts(ast_parent, fund_name, rev_acct)
        comm = asset_acct.GetCommodity()
        self.logger.print_info("Commodity = {}:{}".format(comm.get_namespace(), comm.get_printname()))
        pr1.set_commodity(comm)

        pr1.set_currency(self.currency)
        pr1.set_value(val)
        pr1.set_source_string("user:price")
        pr1.set_typestr('nav')
        pr1.commit_edit()

        if self.mode == PROD:
            self.logger.print_info("Mode = {}: Add Price to DB.".format(self.mode), GREEN)
            self.price_db.add_price(pr1)
        else:
            self.logger.print_info("Mode = {}: ABANDON Prices!\n".format(self.mode), RED)

    def create_gnc_trade_txs(self, tx1, tx2):
        """
        Create and load Gnucash transactions to the Gnucash file
        :param tx1: first transaction
        :param tx2: matching transaction if a switch
        :return: nil
        """
        self.logger.print_info('create_gnc_trade_txs()', BLUE)
        # create a gnucash Tx
        gtx = Transaction(self.book)
        # gets a guid on construction

        gtx.BeginEdit()

        gtx.SetCurrency(self.currency)
        gtx.SetDate(tx1[TRADE_DAY], tx1[TRADE_MTH], tx1[TRADE_YR])
        # self.dbg.print_info("gtx date = {}".format(gtx.GetDate()), BLUE)
        self.logger.print_info("tx1[DESC] = {}".format(tx1[DESC]), YELLOW)
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
            # the second split is for a REVENUE account
            spl_rev = Split(self.book)
            spl_rev.SetParent(gtx)
            # set the Account, Value and Reconciled of the REVENUE split
            spl_rev.SetAccount(tx1[REVENUE])
            rev_gross = tx1[GROSS] * -1
            # self.dbg.print_info("revenue gross = {}".format(rev_gross))
            spl_rev.SetValue(GncNumeric(rev_gross, 100))
            spl_rev.SetReconcile(CREC)
            # set Notes for the Tx
            gtx.SetNotes(tx1[NOTES])
            # set Action for the ASSET split
            action = FEE if FEE in tx1[DESC] else ("Sell" if tx1[UNITS] < 0 else DIST)
            self.logger.print_info("action = {}".format(action))
            spl_ast.SetAction(action)

        # ROLL BACK if something went wrong and the two splits DO NOT balance
        if not gtx.GetImbalanceValue().zero_p():
            self.logger.print_error("Gnc tx IMBALANCE = {}!! Roll back transaction changes!"
                                    .format(gtx.GetImbalanceValue().to_string()))
            gtx.RollbackEdit()
            return

        if self.mode == PROD:
            self.logger.print_info("Mode = {}: Commit transaction changes.\n".format(self.mode), GREEN)
            gtx.CommitEdit()
        else:
            self.logger.print_info("Mode = {}: Roll back transaction changes!\n".format(self.mode), RED)
            gtx.RollbackEdit()

    def process_monarch_trade(self, mtx, plan_type, ast_parent, rev_acct):
        """
        Obtain each Monarch trade as a transaction item, or pair of transactions where required, and forward to Gnucash processing
        :param        mtx: dict: Monarch transaction information
        :param  plan_type: str: types of plans in a Configuration.InvestmentRecord
        :param ast_parent: Gnucash account
        :param   rev_acct: Gnucash account
        :return: nil
        """
        self.logger.print_info('process_monarch_trade()', BLUE)
        try:
            # get the additional required information from the Monarch json
            tx1, tx2 = self.get_trade_info(mtx, plan_type, ast_parent, rev_acct)

            # just return if there is a matching tx but we don't have it yet
            if tx1[SWITCH] and tx2 is None:
                return

            self.create_gnc_trade_txs(tx1, tx2)

        except Exception as ie:
            self.logger.print_error("process_monarch_trade() EXCEPTION!! '{}'\n".format(str(ie)))

    def create_gnucash_info(self):
        """
        Process each transaction from the Monarch input file to get the required Gnucash information
        :return: nil
        """
        self.logger.print_info("create_gnucash_info()", BLUE)
        self.root_acct = self.book.get_root_account()
        self.root_acct.get_instance()

        if self.domain != TRADE:
            self.price_db = self.book.get_price_db()
            self.price_db.begin_edit()
            self.logger.print_info("self.price_db.begin_edit()", CYAN)

        commod_tab = self.book.get_table()
        self.currency = commod_tab.lookup("ISO4217", "CAD")

        plans = self.monarch_record.get_plans()
        for plan_type in plans:
            self.logger.print_info("\n\t\u0022Plan type = {}\u0022".format(plan_type), YELLOW)

            asset_parent, rev_acct = self.get_asset_revenue_info(plan_type)

            if self.domain != PRICE:
                for mon_tx in plans[plan_type][TRADE]:
                    self.process_monarch_trade(mon_tx, plan_type, asset_parent, rev_acct)

            if self.domain != TRADE:
                for mon_tx in plans[plan_type][PRICE]:
                    self.create_gnc_price_txs(mon_tx, asset_parent, rev_acct)

    def get_asset_revenue_info(self, plan_type):
        """
        Get the required asset and/or revenue information from each plan
        :param plan_type: string: see Configuration
        :return: Gnucash account, Gnucash account: revenue account and asset parent account
        """
        self.logger.print_info("get_asset_revenue_info()", BLUE)
        rev_path = copy.copy(ACCT_PATHS[REVENUE])
        rev_path.append(plan_type)
        ast_parent_path = copy.copy(ACCT_PATHS[ASSET])
        ast_parent_path.append(plan_type)

        pl_owner = self.gnucash_record.get_owner()
        if plan_type != PL_OPEN:
            if pl_owner == '':
                raise Exception("PROBLEM[355]!! Trying to process plan type '{}' but NO Owner value found"
                                " in Tx Collection!!".format(plan_type))
            rev_path.append(ACCT_PATHS[pl_owner])
            ast_parent_path.append(ACCT_PATHS[pl_owner])
        self.logger.print_info("rev_path = {}".format(str(rev_path)))

        rev_acct = self.gnc_util.account_from_path(self.root_acct, rev_path)
        self.logger.print_info("rev_acct = {}".format(rev_acct.GetName()))
        self.logger.print_info("asset_parent_path = {}".format(str(ast_parent_path)))
        asset_parent = self.gnc_util.account_from_path(self.root_acct, ast_parent_path)
        self.logger.print_info("asset_parent = {}".format(asset_parent.GetName()))

        return asset_parent, rev_acct

    def prepare_session(self):
        """
        initialization needed for a Gnucash session
        :return: message
        """
        self.logger.print_info("prepare_session()", BLUE)
        msg = TEST
        try:
            session = Session(self.gnc_file)
            self.book = session.book

            owner = self.monarch_record.get_owner()
            self.logger.print_info("Owner = {}".format(owner), GREEN)
            self.set_gnc_rec(InvestmentRecord(owner))

            self.create_gnucash_info()

            if self.mode == PROD:
                self.logger.print_info("Mode = {}: COMMIT Price DB edits and Save session.".format(self.mode), GREEN)

                if self.domain != TRADE:
                    self.price_db.commit_edit()

                # only ONE session save for the entire run
                session.save()

            session.end()
            session.destroy()

            msg = self.logger.get_log()

        except Exception as se:
            msg = "prepare_session() EXCEPTION!! '{}'".format(repr(se))
            self.logger.print_error(msg)
            if "session" in locals() and session is not None:
                session.end()
                session.destroy()
            raise se

        return msg


def gnucash_session_main(args):
    """
    Take the information from an InvestmentRecord JSON file and produce Gnucash transactions to write to a Gnucash file
    :return: message
    """
    py_name = __file__.split('/')[-1]
    usage = "usage: py36 {} <Monarch copy-text JSON file> <mode: prod|test> [Gnucash file]".format(py_name)
    if len(args) < 3:
        Gnulog.print_text("NOT ENOUGH parameters!", RED)
        Gnulog.print_text(usage, MAGENTA)
        exit(421)

    mon_file = args[0]
    if not osp.isfile(mon_file):
        Gnulog.print_text("File path '{}' does not exist. Exiting...".format(mon_file), RED)
        Gnulog.print_text(usage, GREEN)
        exit(427)
    Gnulog.print_text("\nMonarch file = {}".format(mon_file), GREEN)

    # get Monarch transactions from the Monarch JSON file
    with open(mon_file, 'r') as fp:
        tx_coll = json.load(fp)

    gnc_file = args[1]
    if not osp.isfile(gnc_file):
        Gnulog.print_text("File path '{}' does not exist. Exiting...".format(gnc_file), RED)
        exit(437)
    Gnulog.print_text("\nGnucash file = {}".format(gnc_file), GREEN)

    mode = args[2].upper()

    gncs = GnucashSession(tx_coll, mode, gnc_file, True, BOTH)
    msg = gncs.prepare_session()

    Gnulog.print_text("\n >>> PROGRAM ENDED.", MAGENTA)
    return msg


if __name__ == '__main__':
    import sys
    gnucash_session_main(sys.argv[1:])
