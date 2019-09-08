###############################################################################################################################
# coding=utf-8
#
# parseMonarchCopyRep.py -- parse a file with COPIED Monarch Report text, assembling and saving the information
#                           as transaction and price parameters in json format, then saving to a specified Gnucash file
#
# Copyright (c) 2019 Mark Sattolo <epistemik@gmail.com>
#
__author__ = 'Mark Sattolo'
__author_email__ = 'epistemik@gmail.com'
__python_version__ = 3.6
__created__ = '2019-06-22'
__updated__ = '2019-09-08'

from sys import path
path.append("/home/marksa/dev/git/Python/Gnucash/updateBudgetQtrly")
import re
from argparse import ArgumentParser
from gnucash_utilities import *
from investment import *


class ParseMonarchCopyReport:
    def __init__(self, p_monfile:str, p_mode:str, p_debug:bool=False):
        self.mon_file = p_monfile
        self.mode     = p_mode
        self.debug    = p_debug
        self.logger   = SattoLog(my_color=MAGENTA, do_logging=p_debug)
        self.inv_rec  = InvestmentRecord()

        self.logger.print_info('class ParseMonarchCopyReport')

    def set_filename(self, fn:str):
        self.inv_rec.set_filename(fn)

    def get_record(self):
        return self.inv_rec

    def get_log(self):
        return self.logger.get_log()

    def parse_copy_info(self):
        """
        parsing for NEW format txt files, ~ May 31, 2019, just COPIED from Monarch web page,
        as new Monarch pdf's are no longer practical to use -- extracted text just too inconsistent...
        *add ALL price and trade info to self.Configuration.InvestmentRecord object
        *loop lines:
            1: skip if line too short
            2: date
            3: owner
            4: FUND ->
                 find planID in words; type is PLAN_IDS[word][PLAN_TYPE]
            5: Pass if planID is Joint and owner is Lulu
            6: Prices ->
                 match fund name:
                    record fund company, fund, balance, price, doc date
            7: Trades ->
                 match date:
                    record fund, desc, gross, units, price, load, trade date
        :return nil
        """
        self.logger.print_info("ParseMonarchCopyReport.parse_copy_info()")

        re_date = re.compile(r"([0-9]{2}-\w{3}-[0-9]{4})")

        mon_state = FIND_DATE
        plan_type = UNKNOWN
        plan_id = UNKNOWN
        with open(self.mon_file) as fp:
            ct = 0
            for line in fp:
                ct += 1
                # self.logger.print_info("Line {}".format(ct))

                words = line.split()
                if len(words) <= 1:
                    continue

                if mon_state == FIND_DATE:
                    re_match = re.match(re_date, words[0])
                    if re_match:
                        doc_date = re_match.group(1)
                        self.logger.print_info("Document date: {}".format(doc_date))
                        mon_state = FIND_OWNER
                        continue

                if mon_state == FIND_OWNER:
                    if words[0] == OPEN:
                        owner = MON_MARK if MON_ROBB in words else MON_LULU
                        self.inv_rec.set_owner(owner)
                        self.logger.print_info("\n\t\u0022Current owner: {}\u0022".format(owner))
                        mon_state = STATE_SEARCH
                        continue

                if words[0] == FUND.upper():
                    for word in words:
                        if word in PLAN_IDS:
                            plan_type = PLAN_IDS[word][PLAN_TYPE]
                            plan_id = word
                            self.logger.print_info("\n\t\u0022Current plan: type = {} ; id = {}\u0022"
                                                   .format(plan_type, plan_id))
                            continue

                if mon_state == STATE_SEARCH:
                    # have to ensure that the joint transactions are only recorded ONCE
                    if owner == MON_LULU and plan_id == JOINT_PLAN_ID:
                        continue

                # PRICES
                if words[0] in FUND_NAME_CODE:
                    fd_co = words[0]
                    self.logger.print_info("Fund company = {}".format(fd_co))
                    fund = words[-10].replace('-', ' ')
                    self.logger.print_info("Fund = {}".format(fund))
                    bal = words[-8]
                    self.logger.print_info("Final balance = {}".format(bal))
                    price = words[-7]
                    self.logger.print_info("Final price = {}".format(price))

                    curr_tx = {DATE: doc_date, DESC: PRICE, FUND_CMPY: fd_co, FUND: fund, UNIT_BAL: bal, PRICE: price}
                    self.inv_rec.add_tx(plan_type, PRICE, curr_tx)
                    self.logger.print_info('ADD current Price Tx to Collection!')
                    continue

                # TRADES
                re_match = re.match(re_date, words[0])
                if re_match:
                    tx_date = re_match.group(1)
                    self.logger.print_info("FOUND a NEW tx! Date: {}".format(tx_date))
                    curr_tx = {TRADE_DATE: tx_date}

                    fund_co = words[-8]
                    fund = fund_co + " " + words[-7]
                    curr_tx[FUND] = fund
                    self.logger.print_info("curr_tx[FUND]: {}".format(curr_tx[FUND]))
                    tx_type = words[1]
                    desc = TX_TYPES[words[2]] if tx_type == INTRCL else TX_TYPES[tx_type]
                    curr_tx[DESC] = COMPANY_NAME[fund_co] + ": " + desc
                    self.logger.print_info("curr_tx[DESC]: {}".format(curr_tx[DESC]))
                    curr_tx[GROSS] = words[-4]
                    self.logger.print_info("curr_tx[GROSS]: {}".format(curr_tx[GROSS]))
                    curr_tx[UNITS] = words[-1]
                    self.logger.print_info("curr_tx[UNITS]: {}".format(curr_tx[UNITS]))
                    curr_tx[PRICE] = words[-2]
                    self.logger.print_info("curr_tx[PRICE]: {}".format(curr_tx[PRICE]))
                    curr_tx[LOAD] = words[-5]
                    self.logger.print_info("curr_tx[LOAD]: {}".format(curr_tx[LOAD]))

                    self.inv_rec.add_tx(plan_type, TRADE, curr_tx)
                    self.logger.print_info('ADD current Trade Tx to Collection!')

    def get_trade_info(self, mtx:dict, plan_type:str, ast_parent:Account, rev_acct:Account):
        """
        Parse the Monarch trade transactions from a copy&paste JSON file
        Asset accounts: use the proper path to find the parent then search for the Fund Code in the descendants
        Revenue accounts: pick the proper account based on owner and plan type
        gross_curr: re match to Gross then concatenate the two match groups
        date: convert the date then get day, month and year to form a Gnc date
        Units: re match and concatenate the two groups on either side of decimal point
        Description: use DESC and Fund Company
        :param        mtx: Monarch copied trade tx information
        :param  plan_type: plan names from Configuration.InvestmentRecord
        :param ast_parent: Asset parent account
        :param   rev_acct: Revenue account
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

    def process_monarch_trade(self, mtx:dict, plan_type:str, ast_parent:Account, rev_acct:Account):
        """
        Obtain each Monarch trade as a transaction item, or pair of transactions where required, and forward to Gnucash processing
        :param        mtx: Monarch transaction information
        :param  plan_type: plan names from Configuration.InvestmentRecord
        :param ast_parent: Asset parent account
        :param   rev_acct: Revenue account
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

    def add_balance_to_trade(self):
        """
        for each plan type:
            go through Price txs:
                for each fund, find the latest tx in the Trade txs, if any
                if found, add the Unit Balance from the Price tx to the Trade tx
        :return: nil
        """
        self.logger.print_info('add_balance_to_trade()')
        for pl in self.inv_rec.plans:
            self.logger.print_info("plan type = {}".format(repr(pl)))
            plan = self.inv_rec.plans[pl]
            for prc in plan[PRICE]:
                indx = 0
                latest_indx = -1
                latest_dte = None
                fnd = prc[FUND]
                # self.dbg.print_info("Fund = {}".format(fnd))
                for trd in plan[TRADE]:
                    if trd[FUND] == fnd:
                        dte = dt.strptime(trd[TRADE_DATE], '%d-%b-%Y')
                        if latest_dte is None or dte > latest_dte:
                            latest_dte = dte
                            self.logger.print_info("Latest date for {} is {}".format(fnd, latest_dte))
                            latest_indx = indx
                    indx += 1
                if latest_indx > -1:
                    plan[TRADE][latest_indx][UNIT_BAL] = prc[UNIT_BAL]
                    plan[TRADE][latest_indx][NOTES] = fnd + " Balance = " + prc[UNIT_BAL]

    def save_to_gnucash_file(self, gnc_file:str, domain:str):
        self.logger.print_info('save_to_gnucash_file()')
        gncs = GnucashSession(self.inv_rec, self.mode, gnc_file, self.debug, domain)
        msg = gncs.prepare_session()
        self.logger.append(msg)

# END class ParseMonarchCopyReport


def process_args():
    arg_parser = ArgumentParser(description='Process a copied Monarch Report to obtain Gnucash transactions',
                                prog='parseMonarchCopyRep.py')
    # required arguments
    required = arg_parser.add_argument_group('REQUIRED')
    required.add_argument('-m', '--monarch', required=True, help='path & filename of the copied Monarch Report file')
    # required if PROD
    subparsers = arg_parser.add_subparsers(help='with gnc option: MUST specify -f FILENAME and -t TX_TYPE')
    gnc_parser = subparsers.add_parser('gnc', help='Save the parsed trade and/or price transactions to a Gnucash file')
    gnc_parser.add_argument('-f', '--filename', required=True, help='path & filename of the Gnucash file')
    gnc_parser.add_argument('-t', '--type', required=True, choices=[TRADE, PRICE, BOTH],
                            help="type of transaction to save: {} or {} or {}".format(TRADE, PRICE, BOTH))
    # optional arguments
    arg_parser.add_argument('--json',  action='store_true', help='Write the parsed Monarch data to a JSON file')
    arg_parser.add_argument('--debug', action='store_true', help='GENERATE DEBUG OUTPUT: MANY LINES!')

    return arg_parser


def process_input_parameters(argv:list):
    args = process_args().parse_args(argv)
    SattoLog.print_text("\nargs = {}".format(args), BROWN)

    if args.debug:
        SattoLog.print_text('Printing ALL Debug output!!', RED)

    if not osp.isfile(args.monarch):
        SattoLog.print_text("File path '{}' does not exist! Exiting...".format(args.monarch), RED)
        exit(216)
    SattoLog.print_text("\nMonarch file = {}".format(args.monarch), CYAN)

    domain = BOTH
    mode = TEST
    gnc_file = None
    if 'filename' in args:
        if not osp.isfile(args.filename):
            SattoLog.print_text("File path '{}' does not exist. Exiting...".format(args.filename), RED)
            exit(225)
        gnc_file = args.filename
        SattoLog.print_text("\nGnucash file = {}".format(gnc_file), CYAN)
        mode = SEND
        domain = args.type
        SattoLog.print_text("Saving '{}' transaction types to Gnucash.".format(domain), YELLOW)

    return args.monarch, args.json, args.debug, mode, gnc_file, domain


def mon_copy_rep_main(args:list):
    SattoLog.print_text("Parameters = \n{}".format(json.dumps(args, indent=4)), GREEN)
    mon_file, save_json, debug, mode, gnc_file, domain = process_input_parameters(args)

    mcr_now = dt.now().strftime(DATE_STR_FORMAT)
    SattoLog.print_text("mon_copy_rep_main(): Runtime = {}".format(mcr_now), BLUE)

    try:
        # parse an external Monarch COPIED report file
        parser = ParseMonarchCopyReport(mon_file, mode, debug)

        parser.parse_copy_info()
        parser.add_balance_to_trade()

        parser.set_filename(mon_file)

        if mode == SEND:
            parser.save_to_gnucash_file(gnc_file, domain)

        msg = parser.get_log()

        if save_json:
            src_dir = 'copyTxt'
            # pluck path and basename from mon_file to use for the saved json file
            ospath, fname = osp.split(mon_file)
            json_path = ospath.replace(src_dir, 'jsonFromTxt')
            basename, ext = osp.splitext(fname)

            out_file = save_to_json(json_path + '/' + basename, mcr_now, parser.get_record().to_json(), p_color=MAGENTA)
            msg.append("\nmon_copy_rep_main() created JSON file:\n{}".format(out_file))

    except Exception as e:
        msg = "mon_copy_rep_main() EXCEPTION!! '{}'".format(repr(e))
        SattoLog.print_text(msg, RED)

    SattoLog.print_text("\n >>> PROGRAM ENDED.", GREEN)
    return msg


if __name__ == '__main__':
    import sys
    mon_copy_rep_main(sys.argv[1:])
