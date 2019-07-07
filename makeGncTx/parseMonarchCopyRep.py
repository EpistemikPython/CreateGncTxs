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
__updated__ = '2019-07-07'

import re
import json
from argparse import ArgumentParser
from Configuration import *
from gnucashSession import GnucashSession


class ParseMonarchCopyReport:
    def __init__(self, p_monfile, p_mode, p_debug=False):
        self.mon_file = p_monfile
        self.mode     = p_mode
        self.debug    = p_debug
        self.dbg      = Gnulog(p_debug)
        self.inv_rec  = InvestmentRecord()

    def set_filename(self, fn):
        self.inv_rec.set_filename(fn)

    def get_record(self):
        return self.inv_rec

    def get_log(self):
        return self.dbg.get_log()

    def parse_copy_info(self, ts):
        """
        :param ts: string: timestamp for file name
        parsing for NEW format txt files, ~ May 31, 2019, just COPIED from Monarch web page,
        as new Monarch pdf's are no longer practical to use -- extracted text just too inconsistent...
        *loop lines:
            1: skip if line too short
            2: owner
            3: date
            4: FUND ->
                 if FUND: plan type = wd[1] ; plan ID = wd[5]
                 if Fund company: fund and balance and price
            5: Pass if Joint Plan and owner is Lulu
            6: TXS ->
                 match date:
                    date  = re_date.groups
                    type  = wd[1] -> TYPES[type]
                    units = wd[-1]
                    price = wd[-2]
                    gross = wd[-4]
                    load  = wd[-5]
                    code  = wd[-7]
                    company = wd[-8]
            *add ALL price and tx info to self.Configuration.InvestmentRecord object
        :return nil
        """
        self.dbg.print_info("\nparse_copy_info()\nRuntime = {}\n".format(ts), MAGENTA)

        re_date = re.compile(r"([0-9]{2}-\w{3}-[0-9]{4})")

        mon_state = FIND_DATE
        plan_type = UNKNOWN
        plan_id = UNKNOWN
        with open(self.mon_file) as fp:
            ct = 0
            for line in fp:
                ct += 1
                # self.dbg.print_info("Line {}".format(ct))

                words = line.split()
                if len(words) <= 1:
                    continue

                if mon_state == FIND_DATE:
                    re_match = re.match(re_date, words[0])
                    if re_match:
                        doc_date = re_match.group(1)
                        self.dbg.print_info("Document date: {}".format(doc_date), YELLOW)
                        mon_state = FIND_OWNER
                        continue

                if mon_state == FIND_OWNER:
                    if words[0] == PL_OPEN:
                        owner = MON_MARK if words[6] == MON_ROBB else MON_LULU
                        self.inv_rec.set_owner(owner)
                        self.dbg.print_info("\n\t\u0022Current owner: {}\u0022".format(owner), MAGENTA)
                        mon_state = STATE_SEARCH
                        continue

                if words[0] == FUND.upper():
                    plan_type = words[2]
                    plan_id = words[5]
                    self.dbg.print_info("\n\t\u0022Current plan: type = {} ; id = {}\u0022".format(plan_type, plan_id), MAGENTA)
                    continue

                if mon_state == STATE_SEARCH:
                    # have to ensure that the joint transactions are only recorded ONCE
                    if owner == MON_LULU and plan_id == JOINT_PLAN_ID:
                        continue

                # PRICES
                if words[0] in FUND_NAME_CODE:
                    fd_co = words[0]
                    self.dbg.print_info("Fund company = {}".format(fd_co))
                    fund = words[-10].replace('-', ' ')
                    self.dbg.print_info("Fund = {}".format(fund))
                    bal = words[-8]
                    self.dbg.print_info("Final balance = {}".format(bal))
                    price = words[-7]
                    self.dbg.print_info("Final price = {}".format(price))

                    curr_tx = {DATE: doc_date, DESC: PRICE, FUND_CMPY: fd_co, FUND: fund, UNIT_BAL: bal, PRICE: price}
                    self.inv_rec.add_tx(plan_type, PRICE, curr_tx)
                    self.dbg.print_info('ADD current Tx to Collection!', GREEN)
                    continue

                # TRADES
                re_match = re.match(re_date, words[0])
                if re_match:
                    tx_date = re_match.group(1)
                    self.dbg.print_info("FOUND a NEW tx! Date: {}".format(tx_date), YELLOW)
                    curr_tx = {TRADE_DATE: tx_date}

                    fund_co = words[-8]
                    fund = fund_co + " " + words[-7]
                    curr_tx[FUND] = fund
                    self.dbg.print_info("curr_tx[FUND]: {}".format(curr_tx[FUND]))
                    tx_type = words[1]
                    desc = TX_TYPES[words[2]] if tx_type == INTRCL else TX_TYPES[tx_type]
                    curr_tx[DESC] = COMPANY_NAME[fund_co] + ": " + desc
                    self.dbg.print_info("curr_tx[DESC]: {}".format(curr_tx[DESC]))
                    curr_tx[GROSS] = words[-4]
                    self.dbg.print_info("curr_tx[GROSS]: {}".format(curr_tx[GROSS]))
                    curr_tx[UNITS] = words[-1]
                    self.dbg.print_info("curr_tx[UNITS]: {}".format(curr_tx[UNITS]))
                    curr_tx[PRICE] = words[-2]
                    self.dbg.print_info("curr_tx[PRICE]: {}".format(curr_tx[PRICE]))
                    curr_tx[LOAD] = words[-5]
                    self.dbg.print_info("curr_tx[LOAD]: {}".format(curr_tx[LOAD]))

                    self.inv_rec.add_tx(plan_type, TRADE, curr_tx)
                    self.dbg.print_info('ADD current Tx to Collection!', GREEN)

    def add_balance_to_trade(self):
        """
        for each plan type:
            go through Price txs:
                for each fund, find the latest tx in the Trade txs, if any
                if found, add the Unit Balance from the Price tx to the Trade tx
        :return: nil
        """
        self.dbg.print_info('add_balance_to_trade()', BLACK)
        for pl in self.inv_rec.plans:
            self.dbg.print_info("plan type = {}".format(repr(pl)))
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
                            self.dbg.print_info("Latest date for {} is {}".format(fnd, latest_dte))
                            latest_indx = indx
                    indx += 1
                if latest_indx > -1:
                    plan[TRADE][latest_indx][NOTES] = fnd + " Balance = " + prc[UNIT_BAL]

    def save_to_gnucash_file(self, gnc_file):
        self.dbg.print_info('save_to_gnucash_file()', BLUE)
        gncs = GnucashSession(self.inv_rec, self.mode, gnc_file, self.debug)
        msg = gncs.prepare_session()
        self.dbg.print_info('msg = {}'.format(msg), MAGENTA)

# END class ParseMonarchCopyReport


def test_args():
    found_args = ArgumentParser(description='Process a copied Monarch Report to obtain Gnucash transactions',
                                prog='parseMonarchCopyRep.py')
    # required arguments
    found_args.add_argument('-m', '--monarch', required=True, help='REQUIRED: path & filename of the copied Monarch Report file')
    # optional arguments
    found_args.add_argument('-g', '--gnucash', help='Required if PROD: path & filename of the Gnucash file')
    found_args.add_argument('--json', action='store_true', help='Write the parsed Monarch data to a JSON file')
    found_args.add_argument('--prod', action='store_true', help='Save the parsed trade and/or price transactions to a Gnucash file')
    found_args.add_argument('--debug', action='store_true', help='GENERATE DEBUG OUTPUT: MANY LINES!')

    return found_args


def process_input_parameters(argv):
    args = test_args().parse_args(argv)

    if args.debug:
        Gnulog.print_text('Printing ALL Debug output!!', RED)

    if not osp.isfile(args.monarch):
        Gnulog.print_text("File path '{}' does not exist! Exiting...".format(args.monarch), RED)
        exit(208)
    Gnulog.print_text("monarch file = {}".format(args.monarch))

    mode = PROD if args.prod else TEST
    if mode == PROD:
        if args.gnucash is None or not osp.isfile(args.gnucash):
            Gnulog.print_text("File path '{}' does not exist. Exiting...".format(args.gnucash), RED)
            exit(215)
        Gnulog.print_text("gnucash file = {}".format(args.gnucash))

    return args.monarch, args.json, args.debug, mode, args.gnucash


def mon_copy_rep_main(args):
    mon_file, save_json, debug, mode, gnc_file = process_input_parameters(args)

    now = dt.now().strftime(DATE_STR_FORMAT)

    try:
        # parse an external Monarch COPIED report file
        parser = ParseMonarchCopyReport(mon_file, mode, debug)

        parser.parse_copy_info(now)
        parser.add_balance_to_trade()

        parser.set_filename(mon_file)

        if mode == PROD:
            parser.save_to_gnucash_file(gnc_file)

        msg = parser.get_log()

        if save_json:
            # PRINT RECORD AS JSON FILE
            src_dir = 'copyTxt'
            # pluck path and basename from mon_file to use for the saved json file
            ospath, fname = osp.split(mon_file)
            # save to the output folder
            path = ospath.replace(src_dir, 'jsonFromTxt')
            basename, ext = osp.splitext(fname)
            # add a timestamp to get a unique file name
            out_file = path + '/' + basename + '_' + now + ".json"
            Gnulog.print_text("\nOUTPUT FILE: \u0022{}\u0022".format(out_file))
            fp = open(out_file, 'w', encoding='utf-8')
            json.dump(parser.get_record().to_json(), fp, indent=4)
            msg.append("\nparseMonarchTxRep created file:\n{}".format(out_file))

    except Exception as e:
        msg = "mon_funds_rep_main() EXCEPTION!! '{}'".format(repr(e))
        Gnulog.print_text(msg, RED)

    Gnulog.print_text("\n >>> PROGRAM ENDED.", GREEN)
    return msg


if __name__ == '__main__':
    import sys
    mon_copy_rep_main(sys.argv[1:])
