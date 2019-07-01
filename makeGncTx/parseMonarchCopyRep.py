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
__updated__ = '2019-06-23'

import re
import json
from Configuration import *


class ParseMonarchCopyReport:
    def __init__(self, p_debug=False):
        self.debug = p_debug
        self.tx_coll = InvestmentRecord()

    def set_filename(self, fn):
        self.tx_coll.set_filename(fn)

    def get_record(self):
        return self.tx_coll

    def parse_copy_info(self, file_name, ts):
        """
        :param file_name: string: monarch transaction report text file to parse
        :param        ts: string: timestamp for file name
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
        print_info("\nparse_copy_info({})\nRuntime = {}\n".format(file_name, ts), MAGENTA)

        re_date = re.compile(r"([0-9]{2}-\w{3}-[0-9]{4})")

        mon_state = FIND_DATE
        plan_type = UNKNOWN
        plan_id = UNKNOWN
        with open(file_name) as fp:
            ct = 0
            for line in fp:
                ct += 1
                print_info("Line {}".format(ct))

                words = line.split()
                if len(words) <= 1:
                    continue

                if mon_state == FIND_DATE:
                    re_match = re.match(re_date, words[0])
                    if re_match:
                        doc_date = re_match.group(1)
                        print_info("Document date: {}".format(doc_date), YELLOW)
                        mon_state = FIND_OWNER
                        continue

                if mon_state == FIND_OWNER:
                    if words[0] == PL_OPEN:
                        owner = MON_MARK if words[6] == MON_ROBB else MON_LULU
                        self.tx_coll.set_owner(owner)
                        print_info("\n\t\u0022Current owner: {}\u0022".format(owner), MAGENTA)
                        mon_state = STATE_SEARCH
                        continue

                if words[0] == FUND.upper():
                    plan_type = words[2]
                    plan_id = words[5]
                    print_info("\n\t\u0022Current plan: type = {} ; id = {}\u0022".format(plan_type, plan_id), MAGENTA)
                    continue

                if mon_state == STATE_SEARCH:
                    # have to ensure that the joint transactions are only recorded ONCE
                    if owner == MON_LULU and plan_id == JOINT_PLAN_ID:
                        continue

                # PRICES
                if words[0] in FUND_NAME_CODE:
                    fd_co = words[0]
                    print_info("Fund company = {}".format(fd_co))
                    fund = words[-10].replace('-', ' ')
                    print_info("Fund = {}".format(fund))
                    bal = words[-8]
                    print_info("Final balance = {}".format(bal))
                    price = words[-7]
                    print_info("Final price = {}".format(price))

                    curr_tx = {DATE: doc_date, DESC: PRICE, FUND_CMPY: fd_co, FUND: fund, UNIT_BAL: bal, PRICE: price}
                    self.tx_coll.add_tx(plan_type, PRICE, curr_tx)
                    print_info('ADD current Tx to Collection!', GREEN)
                    continue

                # TRADES
                re_match = re.match(re_date, words[0])
                if re_match:
                    tx_date = re_match.group(1)
                    print_info("FOUND a NEW tx! Date: {}".format(tx_date), YELLOW)
                    curr_tx = {TRADE_DATE: tx_date}

                    fund_co = words[-8]
                    fund = fund_co + " " + words[-7]
                    curr_tx[FUND] = fund
                    print_info("curr_tx[FUND]: {}".format(curr_tx[FUND]))
                    tx_type = words[1]
                    desc = TX_TYPES[words[2]] if tx_type == INTRCL else TX_TYPES[tx_type]
                    curr_tx[DESC] = COMPANY_NAME[fund_co] + ": " + desc
                    print_info("curr_tx[DESC]: {}".format(curr_tx[DESC]))
                    curr_tx[GROSS] = words[-4]
                    print_info("curr_tx[GROSS]: {}".format(curr_tx[GROSS]))
                    curr_tx[UNITS] = words[-1]
                    print_info("curr_tx[UNITS]: {}".format(curr_tx[UNITS]))
                    curr_tx[PRICE] = words[-2]
                    print_info("curr_tx[PRICE]: {}".format(curr_tx[PRICE]))
                    curr_tx[LOAD] = words[-5]
                    print_info("curr_tx[LOAD]: {}".format(curr_tx[LOAD]))

                    self.tx_coll.add_tx(plan_type, TRADE, curr_tx)
                    print_info('ADD current Tx to Collection!', GREEN)

    def add_balance_to_trade(self):
        """
        for each plan type:
            go through Price tx:
                for each fund, find the latest tx in the Trade txs, if any
                if found, add the Unit Balance from the Price tx to the Trade tx
        :return: nil
        """
        print_info('add_balance_to_trade()', BLACK)
        for pl in self.tx_coll.plans:
            print_info("pl = {}".format(repr(pl)))
            plan = self.tx_coll.plans[pl]
            for prc in plan[PRICE]:
                indx = 0
                latest_indx = -1
                latest_dte = None
                fnd = prc[FUND]
                print_info("Fund = {}".format(fnd))
                for trd in plan[TRADE]:
                    if trd[FUND] == fnd:
                        dte = dt.strptime(trd[TRADE_DATE], '%d-%b-%Y')
                        if latest_dte is None or dte > latest_dte:
                            latest_dte = dte
                            print_info("Latest date for {} is {}".format(fnd, latest_dte))
                            latest_indx = indx
                    indx += 1
                if latest_indx > -1:
                    plan[TRADE][latest_indx][NOTES] = fnd + " Balance = " + prc[UNIT_BAL]

    def save_to_gnucash_file(self):
        print_info('save_to_gnucash_file()', BLACK)
        tx = self.tx_coll.get_next()


def mon_copy_rep_main(args):
    py_name = __file__.split('/')[-1]
    usage = "usage: py36 {} <Monarch copy-text file> <mode: prod|test> [Gnucash file]".format(py_name)
    if len(args) < 2:
        print_error("NOT ENOUGH parameters!")
        print_info(usage, MAGENTA)
        exit(175)

    mon_file = args[0]
    if not osp.isfile(mon_file):
        print_error("File path '{}' does not exist! Exiting...".format(mon_file))
        exit(180)
    print_info("mon_file = {}".format(mon_file))

    mode = args[1].upper()

    if mode == PROD:
        if len(args) < 3:
            print_error("NOT ENOUGH parameters!")
            print_info(usage, MAGENTA)
            exit(189)
        else:
            gnc_file = args[2]
            if not osp.isfile(gnc_file):
                print_error("File path '{}' does not exist. Exiting...".format(gnc_file))
                print_info(usage, GREEN)
                exit(195)
            print_info("gnc_file = {}".format(gnc_file))

    now = dt.now().strftime(DATE_STR_FORMAT)

    try:
        # parse an external Monarch COPIED report file
        parser = ParseMonarchCopyReport()

        parser.parse_copy_info(mon_file, now)
        parser.add_balance_to_trade()

        parser.set_filename(mon_file)

        src_dir = 'copyTxt'
        msg = TEST
        if mode == PROD:
            parser.save_to_gnucash_file()
        else:
            # PRINT RECORD AS JSON FILE
            # pluck path and basename from mon_file to use for the saved json file
            ospath, fname = osp.split(mon_file)
            # save to the output folder
            path = ospath.replace(src_dir, 'jsonFromTxt')
            basename, ext = osp.splitext(fname)
            # add a timestamp to get a unique file name
            out_file = path + '/' + basename + '_' + now + ".json"
            print_info("\nOUTPUT FILE: \u0022{}\u0022".format(out_file))
            fp = open(out_file, 'w', encoding='utf-8')
            json.dump(parser.get_record().to_json(), fp, indent=4)
            msg = "parseMonarchTxRep created file: {}".format(out_file)

    except Exception as e:
        msg = "mon_funds_rep_main() EXCEPTION!! '{}'".format(repr(e))
        print_error(msg)

    print_info("\n >>> PROGRAM ENDED.", GREEN)
    return msg


if __name__ == '__main__':
    import sys
    mon_copy_rep_main(sys.argv[1:])
