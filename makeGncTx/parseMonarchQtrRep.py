#
# parseMonarchQtrRep.py -- parse a text file with Monarch Quarterly Report information,
#                          save as a dictionary and print out as a json file
#
# Copyright (c) 2018,2019 Mark Sattolo <epistemik@gmail.com>
#
# @author Mark Sattolo <epistemik@gmail.com>
# @version Python 3.6
# @created 2019-04-28
# @updated 2019-05-10

from sys import argv, exit
import os.path as osp
import re
import copy
import json
from datetime import datetime as dt
from Configuration import *

now = dt.now().strftime("%Y-%m-%d_%H-%M-%S")


def parse_monarch_qtrep(file_name):
    """
    :param file_name: string: monarch quarterly report text file to parse
    PARSE FOR PRICES TO ADD TO THE PRICE DB
    - look for Q1 or Q2 or Q3 or Q4 in filename to get the date
    loop:
        find: MON_MARK or MON_LULU as OWNER
        find: 'Page 1' as the key to start finding prices
        find: 'OPEN...' or 'TFSA...' or 'RRSP...' as Plan Type
              use that as the key for this section of the Tx_Collection
        find: '(match1) - (match2) (match3)...'
                1) use match1 as Fund Company, match2 as Fund Code for the account
                2) use match3 as Fund Company, match2 as Fund Code for the account
        find: '$price'
        find: 'Transaction Details' as key to search for next Plan Type
            OR: another match of 'Fund Company & Fund Code'
    :return: Configuration.Tx_Collection
    """
    print_info("parse_monarch_report({})\nRuntime = {}\n".format(file_name, now), MAGENTA)

    tx_coll = copy.deepcopy(Tx_Collection)

    # re searches
    re_mark    = re.compile(".*({}).*".format(MON_MARK))
    re_lulu    = re.compile(".*({}).*".format(MON_LULU))
    re_start   = re.compile(r"^Page 1.*")
    re_comp1   = re.compile(r"^(.*) - ([0-9ATL]{3,5}).*")
    re_comp2   = re.compile(r"^(- )?([0-9]{3,5}) - (.*)")
    re_price   = re.compile(r"^\$([0-9,]{1,5})\.([0-9]{2,4}).*")
    re_endsum  = re.compile(r"^Transaction Details.*")
    re_plan    = re.compile(r"([OPENTFSAR]{4})(\s?.*)")

    curr_tx = {}
    mon_state = FIND_OWNER
    with open(file_name) as fp:
        ct = 0
        for line in fp:
            ct += 1
            if mon_state == FIND_OWNER:
                match_mark = re.match(re_mark, line)
                if match_mark:
                    owner = match_mark.group(1)
                    print_info("{}/ Owner is: '{}'".format(ct, owner), CYAN)
                    mon_state = FIND_START
                    continue
                match_lulu = re.match(re_lulu, line)
                if match_lulu:
                    owner = match_lulu.group(1)
                    print_info("{}/ Owner is: '{}'".format(ct, owner), RED)
                    mon_state = FIND_START
                    continue

            if mon_state == FIND_START:
                match_start = re.match(re_start, line)
                if match_start:
                    print_info("{}/ Found Start!".format(ct), GREEN)
                    mon_state = FIND_PLAN
                    continue

            if mon_state == FIND_PLAN:
                match_plan = re.match(re_plan, line)
                if match_plan:
                    plan_type = match_plan.group(1)
                    print_info("{}/ Plan type is: '{}'".format(ct, plan_type), BLUE)
                    mon_state = FIND_COMPANY
                    continue

            if mon_state >= FIND_COMPANY:
                match_comp1 = re.match(re_comp1, line)
                if match_comp1:
                    company = match_comp1.group(1)
                    fund_code = match_comp1.group(2)
                    print_info("{}/ Fund is: '{}-{}'".format(ct, company, fund_code), YELLOW)
                    mon_state = FIND_PRICE
                    continue
                match_comp2 = re.match(re_comp2, line)
                if match_comp2:
                    company = match_comp2.group(3)
                    fund_code = match_comp2.group(2)
                    print_info("{}/ Fund is: '{}-{}'".format(ct, company, fund_code), MAGENTA)
                    mon_state = FIND_PRICE
                    continue
                match_endsum = re.match(re_endsum, line)
                if match_endsum:
                    print_info("{}/ END of '{}' plan.".format(ct, plan_type), BLUE)
                    mon_state = FIND_PLAN
                    continue

            if mon_state == FIND_PRICE:
                match_price = re.match(re_price, line)
                if match_price:
                    dollar_str = match_price.group(1)
                    cents_str = match_price.group(2)
                    print_info("{}/ price = '${}.{}'".format(ct, dollar_str, cents_str), GREEN)
                    mon_state = FIND_NEXT_TX
                    continue

    # package vars and send to price fxn

    return tx_coll


def mon_qtr_rep_main():
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
    record = parse_monarch_qtrep(mon_file)

    # PRINT RECORD AS JSON FILE
    if mode == 'PROD':
        # pluck path and basename from mon_file to use for the saved json file
        ospath, fname = osp.split(mon_file)
        # print_info("path is '{}'".format(ospath))
        # save to the output folder
        path = ospath.replace('txtFromPdf', 'jsonFromTxt')
        basename, ext = osp.splitext(fname)
        # add a timestamp to get a unique file name
        out_file = path + '/' + basename + '.' + now + ".json"
        print_info("out_file is '{}'".format(out_file))
        fp = open(out_file, 'w')
        json.dump(record, fp, indent=4)

    print_info("\n >>> PROGRAM ENDED.", GREEN)


if __name__ == '__main__':
    mon_qtr_rep_main()
