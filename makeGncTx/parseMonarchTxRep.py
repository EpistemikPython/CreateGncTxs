#
# parseMonarchTxRep.py -- parse a text file with Monarch Transaction Report information,
#                         save as a dictionary and print out as a json file
#
# Copyright (c) 2018,2019 Mark Sattolo <epistemik@gmail.com>
#
# @author Mark Sattolo <epistemik@gmail.com>
# @version Python 3.6
# @created 2018
# @updated 2019-04-28

from sys import argv, exit
import os.path as osp
import re
import copy
import json
from Configuration import *

now = dt.now().strftime("%Y-%m-%d_%H-%M-%S")


def parse_monarch_tx_rep(file_name):
    """
    :param file_name: string: monarch transaction report text file to parse
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
    print_info("parse_monarch_report({})\nRuntime = {}\n".format(file_name, now), MAGENTA)

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
                    print_info("\n\tCurrent plan_type is: '{}'".format(plan_type), MAGENTA)
                    mon_state = FIND_OWNER
                    continue

            if mon_state == FIND_OWNER:
                if own_line == 0:
                    re_match = re.match(re_own, line)
                    if re_match:
                        own_line += 1
                else:
                    owner_name = line.strip()
                    print_info("Current owner_name is: '{}'".format(owner_name), GREEN)
                    tx_coll.set_owner(owner_name)
                    own_line = 0
                    mon_state = FIND_FUND
                continue

            if mon_state <= FIND_FUND:
                re_match = re.match(re_fund, line)
                if re_match:
                    fund_company = re_match.group(1)
                    fund_code = re_match.group(2)
                    curr_tx = {FUND_CMPY: fund_company, FUND_CODE: fund_code}
                    print_info("Current fund is: {}".format(fund_company + " " + fund_code), BLUE)
                    mon_state = FIND_NEXT_TX
                    continue

            if mon_state <= FIND_NEXT_TX:
                re_match = re.match(re_date, line)
                if re_match:
                    tx_date = re_match.group(1)
                    print_info("Current tx_date is: '{}'".format(tx_date), YELLOW)
                    curr_tx[TRADE_DATE] = tx_date
                    mon_state = FILL_CURR_TX
                    continue

            if mon_state == FILL_CURR_TX:
                curr_tx[DESC] = ''
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
                    print_info("curr_tx[DESC] is: '{}'".format(curr_tx[DESC]))
                    curr_tx[GROSS] = entry
                    print_info("curr_tx[GROSS] is: '{}'".format(curr_tx[GROSS]))
                if tx_line == 4:
                    curr_tx[NET] = entry
                    if curr_tx[NET] != curr_tx[GROSS]:
                        print_info("curr_tx[NET] is: '{}'".format(curr_tx[NET]))
                        print_info("\n>>> PROBLEM!!! GROSS and NET do NOT match!!!\n")
                        continue
                if tx_line == 5:
                    curr_tx[UNITS] = entry
                    print_info("curr_tx[UNITS] is: '{}'".format(curr_tx[UNITS]))
                if tx_line == 6:
                    curr_tx[PRICE] = entry
                    print_info("curr_tx[PRICE] is: '{}'".format(curr_tx[PRICE]))
                if tx_line == 7:
                    curr_tx[UNIT_BAL] = entry
                    print_info("curr_tx[UNIT_BAL] is: '{}'".format(curr_tx[UNIT_BAL]))
                    tx_coll.add(plan_type, curr_tx)
                    mon_state = STATE_SEARCH
                    tx_line = 0

    return tx_coll


def mon_tx_rep_main():
    if len(argv) < 3:
        print_error("NOT ENOUGH parameters!")
        exe = argv[0].split('/')[-1]
        print_info("usage: python {0} <monarch file> <mode: prod|test>".format(exe), MAGENTA)
        print_info("Example: {0} '{1}' 'test'".format(exe, "txtFromPdf/Monarch-Mark-all.txt"), GREEN)
        exit()

    mon_file = argv[1]
    if not osp.isfile(mon_file):
        print_error("File path '{}' does not exist. Exiting...".format(mon_file))
        exit()

    mode = argv[2].upper()

    # parse an external Monarch report file
    record = parse_monarch_tx_rep(mon_file)
    record.set_filename(mon_file)

    # PRINT RECORD AS JSON FILE
    if mode == 'PROD':
        # pluck path and basename from mon_file to use for the saved json file
        ospath, fname = osp.split(mon_file)
        # save to the output folder
        path = ospath.replace('txtFromPdf', 'jsonFromTxt')
        basename, ext = osp.splitext(fname)
        # add a timestamp to get a unique file name
        out_file = path + '/' + basename + '.' + now + ".json"
        print_info("out_file is '{}'".format(out_file))
        fp = open(out_file, 'w', encoding='utf-8')
        json.dump(record.to_json(), fp, indent=4)

    print_info("\n >>> PROGRAM ENDED.", GREEN)


if __name__ == '__main__':
    mon_tx_rep_main()
