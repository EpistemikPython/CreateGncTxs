###############################################################################################################################
# coding=utf-8
#
# parseMonarchFundsRep.py -- parse a text file with Monarch Fund information,
#                            to extract the final balance for each account
#
# Copyright (c) 2019 Mark Sattolo <epistemik@gmail.com>
#
__author__ = 'Mark Sattolo'
__author_email__ = 'epistemik@gmail.com'
__python_version__ = 3.6
__created__ = '2019-06-02'
__updated__ = '2019-06-02'

import os.path as osp
import re
import json
from Configuration import *


def parse_funds_info(file_name, ts):
    """
    :param file_name: string: monarch transaction report text file to parse
    :param        ts: string: timestamp for file name
    parsing for NEW format txt files, ~ May 31, 2019, just COPIED from Monarch web page,
    as new Monarch pdf's are no longer practical to use -- extracted text just too inconsistent...
    loop lines:
        1: owner
        2: date
        3: split -> first plan_type = wd[1]
            if FUND: plan type
            if Fund company: fund and balance and price
    create prices to add to price db
    find gnc splits for each asset account:
        find last split and get tx:
            add final balance to notes
    :return: Configuration.InvestmentRecord object
    """
    print_info("\nparse_copy_txs({})\nRuntime = {}\n".format(file_name, ts), MAGENTA)

    re_date = re.compile(r"^([0-9]{2}-\w{3}-[0-9]{4}).*")

    tx_coll = InvestmentRecord()
    mon_state = STATE_SEARCH
    with open(file_name) as fp:
        ct = 0
        for line in fp:
            ct += 1
            print_info("Line {}".format(ct))
            if mon_state == STATE_SEARCH:
                owner = line.strip()
                tx_coll.set_owner(owner)
                print_info("\n\t\u0022Current owner: {}\u0022".format(owner), MAGENTA)
                mon_state = FIND_DATE
                continue

            if mon_state == FIND_DATE:
                re_match = re.match(re_date, line)
                if re_match:
                    tx_date = re_match.group(1)
                    print_info("FOUND the Date: {}".format(tx_date), YELLOW)
                    mon_state = FIND_NEXT_TX
                    continue

            if mon_state == FIND_NEXT_TX:
                words = line.split()
                if len(words) >= 1:
                    if words[0] == 'FUND':
                        plan_type = words[2]
                        print_info("\n\t\u0022Current plan_type: {}\u0022".format(plan_type), MAGENTA)
                        mon_state = FIND_NEXT_TX
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

                        curr_tx = {FUND_CMPY: fd_co, FUND: fund, UNIT_BAL: bal, PRICE: price}
                        tx_coll.add_tx(plan_type, curr_tx)
                        print_info('ADD current Tx to Collection!', GREEN)

    return tx_coll


def mon_funds_rep_main(args):
    usage = "usage: py36 parseMonarchFundsRep.py <monarch copy-text file> <gnucash file> <mode: prod|test>"
    if len(args) < 3:
        print_error("NOT ENOUGH parameters!")
        print_info(usage, MAGENTA)
        exit()

    mon_file = args[0]
    if not osp.isfile(mon_file):
        print_error("File path '{}' does not exist. Exiting...".format(mon_file))
        print_info(usage, GREEN)
        exit()
    print_info("mon_file = {}".format(mon_file))

    mode = args[2].upper()

    gnc_file = args[1]
    if mode == PROD:
        if not osp.isfile(gnc_file):
            print_error("File path '{}' does not exist. Exiting...".format(gnc_file))
            print_info(usage, GREEN)
            exit()
        print_info("gnc_file = {}".format(gnc_file))

    now = dt.now().strftime(DATE_STR_FORMAT)

    # parse an external Monarch report file
    # from copy & paste
    record = parse_funds_info(mon_file, now)
    src_dir = 'copyTxt'

    record.set_filename(mon_file)

    msg = TEST
    # PRINT RECORD AS JSON FILE
    if mode == PROD:
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

    print_info("\n >>> PROGRAM ENDED.", GREEN)
    return msg


if __name__ == '__main__':
    import sys
    mon_funds_rep_main(sys.argv[1:])
