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
__updated__ = '2019-06-22'

import re
import json
from Configuration import *


class ParseMonarchCopyReport:
    def __init__(self, p_debug=False):
        self.debug = p_debug

    def parse_copy_info(self, file_name, ts):
        """
        :param file_name: string: monarch transaction report text file to parse
        :param        ts: string: timestamp for file name
        parsing for NEW format txt files, ~ May 31, 2019, just COPIED from Monarch web page,
        as new Monarch pdf's are no longer practical to use -- extracted text just too inconsistent...
        *loop lines:
            1: owner
            2: date
            3: split -> first plan_type = wd[1]
                if FUND: plan type
                if Fund company: fund and balance and price
        *create prices to add to price db
        *find gnc splits for each asset account:
            find last split and get tx:
                add final balance to notes
        :return: Configuration.InvestmentRecord object
        """
        print_info("\nparse_copy_info({})\nRuntime = {}\n".format(file_name, ts), MAGENTA)

        re_date = re.compile(r"([0-9]{2}-\w{3}-[0-9]{4})")

        tx_coll = InvestmentRecord()
        mon_state = FIND_OWNER
        plan_type = UNKNOWN
        with open(file_name) as fp:
            ct = 0
            for line in fp:
                ct += 1
                print_info("Line {}".format(ct))
                if mon_state == FIND_OWNER:
                    owner = line.strip()
                    tx_coll.set_owner(owner)
                    print_info("\n\t\u0022Current owner: {}\u0022".format(owner), MAGENTA)
                    mon_state = FIND_DATE
                    continue

                words = line.split()
                if len(words) <= 0:
                    continue

                if mon_state == FIND_DATE:
                    re_match = re.match(re_date, words[0])
                    if re_match:
                        tx_date = re_match.group(1)
                        print_info("Document date: {}".format(tx_date), YELLOW)
                        mon_state = STATE_SEARCH

                if words[0] == FUND.upper():
                    plan_type = words[2]
                    print_info("\n\t\u0022Current plan_type: {}\u0022".format(plan_type), MAGENTA)
                    continue

                if words[0] in FUND_NAME_CODE:
                    fd_co = words[0]
                    print_info("Fund company = {}".format(fd_co))
                    fund = words[-10].replace('-', ' ')
                    print_info("Fund = {}".format(fund))
                    bal = words[-8]
                    print_info("Final balance = {}".format(bal))
                    price = words[-7]
                    print_info("Final price = {}".format(price))

                    curr_tx = {TRADE_DATE: tx_date, FUND_CMPY: fd_co, FUND: fund, UNIT_BAL: bal, PRICE: price}
                    tx_coll.add_tx(plan_type, curr_tx)
                    print_info('ADD current Tx to Collection!', GREEN)

                self.parse_copy_txs(file_name, ts)

        return tx_coll

    def save_to_gnucash_file(self):
        print_info('save_to_gnucash_file', BLACK)

    def parse_copy_txs(self, file_name, ts):
        """
        :param file_name: string: monarch transaction report text file to parse
        :param        ts: string: timestamp for file name
        parsing for NEW format txt files, ~ May 31, 2019, just COPIED from Monarch web page,
        as new Monarch pdf's are no longer practical to use -- extracted text just too inconsistent...
        loop lines:
            1: owner
            2: split -> first plan_type = wd[1]
            search re_date or re_tx:
                TX: split -> update plan_type to wd[1]
                date: split:
                    date  = re_date.groups
                    type  = wd[1] -> TYPES[type]
                    units = wd[-1]
                    price = wd[-2]
                    gross = wd[-4]
                    load  = wd[-5]
                    code  = wd[-7]
                    company = wd[-8]
        :return: Configuration.InvestmentRecord object
        """
        print_info("\nparse_copy_txs({})\nRuntime = {}\n".format(file_name, ts), MAGENTA)

        re_date = re.compile(r"([0-9]{2}-\w{3}-[0-9]{4})")

        tx_coll = InvestmentRecord()
        mon_state = FIND_OWNER
        with open(file_name) as fp:
            ct = 0
            for line in fp:
                ct += 1
                print_info("Line {}".format(ct))
                if mon_state == FIND_OWNER:
                    owner = line.strip()
                    tx_coll.set_owner(owner)
                    print_info("\n\t\u0022Current owner: {}\u0022".format(owner), MAGENTA)
                    mon_state = STATE_SEARCH
                    continue

                words = line.split()
                if len(words) <= 0:
                    continue

                if words[0] == TXS:
                    plan_type = words[1]
                    print_info("\n\t\u0022Current plan_type: {}\u0022".format(plan_type), MAGENTA)
                    continue

                re_match = re.match(re_date, words[0])
                if re_match and len(words) > 2:
                    tx_date = re_match.group(1)
                    print_info("FOUND a NEW tx! Date: {}".format(tx_date), YELLOW)
                    curr_tx = {TRADE_DATE: tx_date}

                    tx_type = words[1]
                    curr_tx[DESC] = TX_TYPES[words[2]] if tx_type == INTRCL else TX_TYPES[tx_type]
                    print_info("curr_tx[DESC]: {}".format(curr_tx[DESC]))
                    curr_tx[GROSS] = words[-4]
                    print_info("curr_tx[GROSS]: {}".format(curr_tx[GROSS]))
                    curr_tx[UNITS] = words[-1]
                    print_info("curr_tx[UNITS]: {}".format(curr_tx[UNITS]))
                    curr_tx[PRICE] = words[-2]
                    print_info("curr_tx[PRICE]: {}".format(curr_tx[PRICE]))
                    curr_tx[LOAD] = words[-5]
                    print_info("curr_tx[LOAD]: {}".format(curr_tx[LOAD]))
                    curr_tx[FUND_CODE] = words[-7]
                    print_info("curr_tx[FUND_CODE]: {}".format(curr_tx[FUND_CODE]))
                    curr_tx[FUND_CMPY] = words[-8]
                    print_info("curr_tx[FUND_CMPY]: {}".format(curr_tx[FUND_CMPY]))

                    tx_coll.add_tx(plan_type, curr_tx)
                    print_info('ADD current Tx to Collection!', GREEN)

        return tx_coll


def mon_copy_rep_main(args):
    bin_name = __file__.split('/')[-1]
    usage = "usage: py36 {} <Monarch copy-text file> <mode: prod|test> [Gnucash file]".format(bin_name)
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
        # parse an external Monarch report file --  funds from copy & paste
        parser = ParseMonarchCopyReport()
        record = parser.parse_copy_info(mon_file, now)

        # parser.get_prices(record)
        # parser.get_final_balances(record)

        record.set_filename(mon_file)

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
            json.dump(record.to_json(), fp, indent=4)
            msg = "parseMonarchTxRep created file: {}".format(out_file)

    except Exception as e:
        msg = "mon_funds_rep_main() EXCEPTION!! '{}'".format(repr(e))
        print_error(msg)

    print_info("\n >>> PROGRAM ENDED.", GREEN)
    return msg


if __name__ == '__main__':
    import sys
    mon_copy_rep_main(sys.argv[1:])
