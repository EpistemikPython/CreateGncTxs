###############################################################################################################################
# coding=utf-8
#
# parseMonarchTxRep.py -- parse a text file with Monarch Transaction Report information,
#                         save as a dictionary and print out as a json file
#
# Copyright (c) 2019 Mark Sattolo <epistemik@gmail.com>
#
# @author Mark Sattolo <epistemik@gmail.com>
# @version Python 3.6
# @created 2018
# @updated 2019-05-25

import os.path as osp
import re
import json
from Configuration import *


def parse_monarch_tx_rep(file_name, ts):
    """
    :param file_name: string: monarch transaction report text file to parse
    :param        ts: string: timestamp for file name
    loop:
        check for 'Plan Type:'
            next line is either 'OPEN...', 'TFSA...' or 'RRSP...'
            use that as the key for this section of the Tx_Collection
        check for '$INVESTMENT_COMPANY/$MF_NAME-...' :
            use $MF_NAME as the Fund Code in the tx
        look for date: 'MM/DD/YYYY' becomes 'Trade Date'
            then parse:
                2 lines = 'Description'  : Text
                  line  = 'Gross'        : Currency float
                  line  = 'Net'          : Currency float
                  line  = 'Units'        : float
                  line  = 'Price'        : Currency float
                  line  = 'Unit Balance' : float
    :return: Configuration.InvestmentRecord object
    """
    print_info("\nparse_monarch_tx_rep({})\nRuntime = {}\n".format(file_name, ts), MAGENTA)

    # re searches
    re_own  = re.compile(".*({}).*".format(OWNER))
    re_plan = re.compile(r"([OPENTFSAR]{4})(\s?.*)")
    re_fund = re.compile(r".*([A-Z]{3})\s?([0-9]{3,5}).*")
    re_date = re.compile(r".*([0-9]{2}/[0-9]{2}/[0-9]{4}).*")

    tx_coll = InvestmentRecord()
    own_line = 0
    tx_line = 0
    mon_state = STATE_SEARCH
    with open(file_name) as fp:
        ct = 0
        for line in fp:
            ct += 1
            if mon_state == STATE_SEARCH:
                re_match = re.match(re_plan, line)
                if re_match:
                    plan_type = re_match.group(1)
                    print_info("\n\t\u0022Current plan_type: {}\u0022".format(plan_type), MAGENTA)
                    mon_state = FIND_OWNER
                    continue

            if mon_state == FIND_OWNER:
                if own_line == 0:
                    re_match = re.match(re_own, line)
                    if re_match:
                        own_line += 1
                else:
                    owner_name = line.strip()
                    print_info("Current owner_name: {}".format(owner_name), GREEN)
                    tx_coll.set_owner(owner_name)
                    own_line = 0
                    mon_state = FIND_FUND
                continue

            if mon_state <= FIND_FUND:
                re_match = re.match(re_fund, line)
                if re_match:
                    fund_company = re_match.group(1)
                    fund_code = re_match.group(2)
                    print_info("Current fund: {}".format(fund_company + " " + fund_code), BLUE)
                    mon_state = FIND_NEXT_TX
                    continue

            if mon_state <= FIND_NEXT_TX:
                re_match = re.match(re_date, line)
                if re_match:
                    tx_date = re_match.group(1)
                    print_info("FOUND a NEW tx! Date: {}".format(tx_date), YELLOW)
                    curr_tx = {FUND_CMPY: fund_company, FUND_CODE: fund_code, TRADE_DATE: tx_date, DESC: ''}
                    # curr_tx[TRADE_DATE] = tx_date
                    mon_state = FILL_CURR_TX
                    continue

            if mon_state == FILL_CURR_TX:
                tx_line += 1
                entry = line.strip()
                if tx_line < 3:
                    if entry == AUTO_SYS or entry == INTRF_IN:
                        # back up by one as have one MORE line of DESCRIPTION for AUTO_SYS and INTRF_IN cases
                        tx_line -= 1
                    elif entry == SW_IN or entry == SW_OUT or entry == FEE:
                        # move forward by one because one FEWER line of DESCRIPTION for these cases
                        tx_line += 1
                    # TODO: match number to proceed to looking for GROSS?
                    curr_tx[DESC] += (entry + ":")
                    continue
                if tx_line == 3:
                    print_info("curr_tx[DESC]: {}".format(curr_tx[DESC]))
                    curr_tx[GROSS] = entry
                    print_info("curr_tx[GROSS]: {}".format(curr_tx[GROSS]))
                if tx_line == 4:
                    curr_tx[NET] = entry
                    if curr_tx[NET] != curr_tx[GROSS]:
                        print_info("curr_tx[NET]: {}".format(curr_tx[NET]))
                        print_error("\n>>> PROBLEM!!! GROSS and NET do NOT match!!!\n")
                        continue
                if tx_line == 5:
                    curr_tx[UNITS] = entry
                    print_info("curr_tx[UNITS]: {}".format(curr_tx[UNITS]))
                if tx_line == 6:
                    curr_tx[PRICE] = entry
                    print_info("curr_tx[PRICE]: {}".format(curr_tx[PRICE]))
                if tx_line == 7:
                    curr_tx[UNIT_BAL] = entry
                    print_info("curr_tx[UNIT_BAL]: {}".format(curr_tx[UNIT_BAL]))
                    tx_coll.add_tx(plan_type, curr_tx)
                    print_info('ADD current Tx to Collection!', GREEN)
                    mon_state = STATE_SEARCH
                    tx_line = 0

    return tx_coll


def mon_tx_rep_main(args):
    if len(args) < 2:
        print_error("NOT ENOUGH parameters!")
        print_info("usage: py36 parseMonarchTxRep.py <monarch file> <mode: prod|test>", MAGENTA)
        exit()

    mon_file = args[0]
    if not osp.isfile(mon_file):
        print_error("File path '{}' does not exist! Exiting...".format(mon_file))
        exit()

    mode = args[1].upper()

    now = dt.now().strftime(DATE_STR_FORMAT)

    # parse an external Monarch report file
    record = parse_monarch_tx_rep(mon_file, now)
    record.set_filename(mon_file)

    msg = TEST
    # PRINT RECORD AS JSON FILE
    if mode == PROD:
        # pluck path and basename from mon_file to use for the saved json file
        ospath, fname = osp.split(mon_file)
        # save to the output folder
        path = ospath.replace('txtFromPdf', 'jsonFromTxt')
        basename, ext = osp.splitext(fname)
        # add a timestamp to get a unique file name
        out_file = path + '/' + basename + '_' + now + ".json"
        print_info("\nout_file: {}".format(out_file))
        fp = open(out_file, 'w', encoding='utf-8')
        json.dump(record.to_json(), fp, indent=4)
        msg = "parseMonarchTxRep created file: {}".format(out_file)

    print_info("\n >>> PROGRAM ENDED.", GREEN)
    return msg


if __name__ == '__main__':
    import sys
    mon_tx_rep_main(sys.argv[1:])
