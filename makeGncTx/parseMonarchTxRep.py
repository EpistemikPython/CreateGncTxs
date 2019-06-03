###############################################################################################################################
# coding=utf-8
#
# parseMonarchTxRep.py -- parse a text file with Monarch Transaction Report information,
#                         save as a dictionary and print out as a json file
#
# Copyright (c) 2019 Mark Sattolo <epistemik@gmail.com>
#
__author__ = 'Mark Sattolo'
__author_email__ = 'epistemik@gmail.com'
__python_version__ = 3.6
__created__ = '2018'
__updated__ = '2019-06-02'

import os.path as osp
import re
import json
from Configuration import *


def parse_pdf_txs(file_name, ts):
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
    print_info("\nparse_pdf_txs({})\nRuntime = {}\n".format(file_name, ts), MAGENTA)

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
            print_info("line is type {}".format(type(line)))
            line_list = line.split()
            for it in line_list:
                print_info("it = {}".format(it))
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


def parse_copy_txs(file_name, ts):
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

    # re searches
    re_tx  = re.compile(".*({}).*".format(TX))
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
                mon_state = FIND_PLAN
                continue

            if mon_state == FIND_PLAN:
                words = line.split()
                plan_type = words[1]
                print_info("\n\t\u0022Current plan_type: {}\u0022".format(plan_type), MAGENTA)
                mon_state = FIND_NEXT_TX
                continue

            if mon_state == FIND_NEXT_TX:
                words = line.split()
                re_match = re.match(re_tx, line)
                if re_match:
                    plan_type = words[1]
                    print_info("\n\t\u0022Current plan_type: {}\u0022".format(plan_type), MAGENTA)
                    continue

                re_match = re.match(re_date, line)
                if re_match:
                    tx_date = re_match.group(1)
                    print_info("FOUND a NEW tx! Date: {}".format(tx_date), YELLOW)
                    curr_tx = {TRADE_DATE: tx_date}

                    tx_type = words[1]
                    curr_tx[DESC] = TX_TYPES[tx_type]
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


def mon_tx_rep_main(args):
    if len(args) < 2:
        print_error("NOT ENOUGH parameters!")
        print_info("usage: py36 parseMonarchTxRep.py <monarch text file> <mode: prod|test>", MAGENTA)
        exit()

    mon_file = args[0]
    if not osp.isfile(mon_file):
        print_error("File path '{}' does not exist! Exiting...".format(mon_file))
        exit()

    mode = args[1].upper()

    now = dt.now().strftime(DATE_STR_FORMAT)

    # parse an external Monarch report file
    # from PDF
    # record = parse_pdf_txs(mon_file, now)
    # src_dir = 'txtFromPdf'
    # from copy & paste
    record = parse_copy_txs(mon_file, now)
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
    mon_tx_rep_main(sys.argv[1:])
