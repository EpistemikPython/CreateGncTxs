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

import re
from argparse import ArgumentParser
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
        self.logger.print_info("ParseMonarchCopyReport.parse_copy_info()", BLUE)

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
                        self.logger.print_info("Document date: {}".format(doc_date), BROWN)
                        mon_state = FIND_OWNER
                        continue

                if mon_state == FIND_OWNER:
                    if words[0] == OPEN:
                        owner = MON_MARK if MON_ROBB in words else MON_LULU
                        self.inv_rec.set_owner(owner)
                        self.logger.print_info("\n\t\u0022Current owner: {}\u0022".format(owner), MAGENTA)
                        mon_state = STATE_SEARCH
                        continue

                if words[0] == FUND.upper():
                    for word in words:
                        if word in PLAN_IDS:
                            plan_type = PLAN_IDS[word][PLAN_TYPE]
                            plan_id = word
                            self.logger.print_info("\n\t\u0022Current plan: type = {} ; id = {}\u0022".format(plan_type, plan_id), MAGENTA)
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
                    self.logger.print_info('ADD current Price Tx to Collection!', CYAN)
                    continue

                # TRADES
                re_match = re.match(re_date, words[0])
                if re_match:
                    tx_date = re_match.group(1)
                    self.logger.print_info("FOUND a NEW tx! Date: {}".format(tx_date), BROWN)
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
                    self.logger.print_info('ADD current Trade Tx to Collection!', GREEN)

    def add_balance_to_trade(self):
        """
        for each plan type:
            go through Price txs:
                for each fund, find the latest tx in the Trade txs, if any
                if found, add the Unit Balance from the Price tx to the Trade tx
        :return: nil
        """
        self.logger.print_info('add_balance_to_trade()', BLUE)
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
        self.logger.print_info('save_to_gnucash_file()', BLUE)
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
