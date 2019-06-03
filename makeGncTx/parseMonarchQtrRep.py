###############################################################################################################################
# coding=utf-8
#
# parseMonarchQtrRep.py -- parse a text file with Monarch Quarterly Report information,
#                          then take the saved transaction information and create Gnucash prices
#                          and save to the specified Gnucash file
#
# Copyright (c) 2019 Mark Sattolo <epistemik@gmail.com>
#
# @author Mark Sattolo <epistemik@gmail.com>
# @version Python 3.6
# @created 2019-04-28
# @updated 2019-05-25

import os.path as osp
import re
import copy
import json
from gnucash import Session, GncNumeric, GncPrice
from Configuration import *


# noinspection PyUnresolvedReferences
class MonarchQrepToGncPrices:
    def __init__(self, fmon, gnc_file, mode):
        self.prod = (mode == PROD)
        self.mon_file = fmon

        self.session = Session(gnc_file)
        self.book = self.session.book

        self.root = self.book.get_root_account()
        self.root.get_instance()

        self.price_db = self.book.get_price_db()

        commod_tab = self.book.get_table()
        self.currency = commod_tab.lookup("ISO4217", "CAD")

    def parse_monarch_qtrep(self):
        """
        PARSE FOR PRICES TO ADD TO THE PRICE DB
        loop:
            find: 'For the Period <date1> to <date2>' for the date for the prices
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
        :return: Configuration.InvestmentRecord object
        """
        print_info("parse_monarch_qtrep()\nRuntime = {}\n".format(strnow), MAGENTA)

        # re searches
        re_date    = re.compile(r"^For the period (.*) to (\w{3}) (\d{1,2}), (\d{4})")
        re_mark    = re.compile(".*({}).*".format(MON_MARK))
        re_lulu    = re.compile(".*({}).*".format(MON_LULU))
        re_start   = re.compile(r"^Page 1.*")
        re_comp1   = re.compile(r"^(.*) - ([0-9ATL]{3,5}).*")
        re_comp2   = re.compile(r"^(- )?(\d{3,5}) - (.*)")
        re_price   = re.compile(r"^\$([0-9,]{1,5})\.(\d{2,4}).*")
        re_plan    = re.compile(r"(OPEN|TFSA|RRSP)(\s?.*)")
        re_endplan = re.compile(r"^Transaction Details.*")
        re_finish  = re.compile(r"^Disclosure.*")

        mon_state = FIND_OWNER
        with open(self.mon_file) as fp:
            ct = 0
            for line in fp:
                ct += 1
                if mon_state == FIND_OWNER:
                    match_mark = re.match(re_mark, line)
                    match_lulu = re.match(re_lulu, line)
                    if match_mark or match_lulu:
                        if match_mark:
                            owner = match_mark.group(1)
                        elif match_lulu:
                            owner = match_lulu.group(1)
                        print_info("{}/ Owner: {}".format(ct, owner), RED)
                        tx_coll = InvestmentRecord(owner)
                        mon_state = FIND_START
                        continue

                if mon_state == FIND_START:
                    match_start = re.match(re_start, line)
                    if match_start:
                        print_info("{}/ Found Start!".format(ct), GREEN)
                        mon_state = FIND_DATE
                        continue

                if mon_state == FIND_DATE:
                    match_date = re.match(re_date, line)
                    if match_date:
                        day = match_date.group(3)
                        month = match_date.group(2)
                        year = match_date.group(4)
                        datestring = "{}-{}-{}".format(year, month, day)
                        pr_date = dt.strptime(datestring, '%Y-%b-%d')
                        tx_coll.set_date(pr_date)
                        print_info("date: {}".format(pr_date), CYAN)
                        mon_state = FIND_PLAN
                        continue

                if mon_state == FIND_PLAN:
                    match_finish = re.match(re_finish, line)
                    if match_finish:
                        print_info("{}/ FINISHED!".format(ct), RED)
                        break
                    match_plan = re.match(re_plan, line)
                    if match_plan:
                        plan_type = match_plan.group(1)
                        print_info("{}/ Plan type: {}".format(ct, plan_type), BLUE)
                        mon_state = FIND_COMPANY
                        continue

                if mon_state == FIND_COMPANY:
                    match_endsum = re.match(re_endplan, line)
                    if match_endsum:
                        print_info("{}/ END of '{}' plan.".format(ct, plan_type), BLUE)
                        mon_state = FIND_PLAN
                        continue
                    match_comp1 = re.match(re_comp1, line)
                    match_comp2 = re.match(re_comp2, line)
                    if match_comp1 or match_comp2:
                        if match_comp1:
                            company = match_comp1.group(1)
                            fund_code = match_comp1.group(2)
                        elif match_comp2:
                            company = match_comp2.group(3)
                            fund_code = match_comp2.group(2)
                        curr_tx = {FUND_CMPY: company, FUND_CODE: fund_code}
                        print_info("{}/ Fund is: '{}:{}'".format(ct, company, fund_code), MAGENTA)
                        mon_state = FIND_PRICE
                        continue

                if mon_state == FIND_PRICE:
                    match_price = re.match(re_price, line)
                    if match_price:
                        dollar_str = match_price.group(1)
                        cents_str = match_price.group(2)
                        print_info("{}/ price = '${}.{}'".format(ct, dollar_str, cents_str), GREEN)
                        curr_tx[DOLLARS] = dollar_str
                        curr_tx[CENTS] = cents_str
                        tx_coll.add_tx(plan_type, curr_tx)
                        mon_state = FIND_COMPANY
                        continue

        print_info("Found {} transactions.".format(tx_coll.get_size()))
        return tx_coll

    def get_prices_and_save(self, tx_coll):
        """
        create Gnucash prices, load and save to the Gnucash file's PriceDB
        :param tx_coll: InvestmentRecord object: transactions to use to extract Gnucash prices
        :return: message
        """
        print_info('get_prices_and_save()', MAGENTA)

        gncu = GncUtilities()

        msg = TEST
        self.price_db.begin_edit()
        print_info("self.price_db.begin_edit()", MAGENTA)
        try:
            for plan_type in tx_coll.plans:
                print_info("\n\nPlan type = {}".format(plan_type))
                for tx in tx_coll.plans[plan_type]:
                    base = pow(10, len(tx[CENTS]))
                    int_price = int(tx[DOLLARS] + tx[CENTS])
                    val = GncNumeric(int_price, base)

                    ast_parent_path = copy.copy(ACCT_PATHS[ASSET])
                    ast_parent_path.append(plan_type)

                    if plan_type != PL_OPEN:
                        if tx_coll.get_owner() == UNKNOWN:
                            raise Exception("PROBLEM!! Trying to process plan type '{}' but NO Owner information found"
                                            " in Tx Collection!!".format(plan_type))
                        ast_parent_path.append(ACCT_PATHS[tx_coll.get_owner()])

                    print_info("ast_parent_path = {}".format(str(ast_parent_path)), BLUE)
                    asset_parent = gncu.account_from_path(self.root, ast_parent_path)

                    # get the asset account name
                    name_key = tx[FUND_CMPY].split(' ')[0]
                    print_info("name_key = {}".format(name_key), YELLOW)
                    if name_key in FUND_NAME_CODE.keys():
                        name_code = FUND_NAME_CODE[name_key]
                        # special case
                        if name_code == ATL:
                            asset_acct_name = ATL_O59
                        else:
                            asset_acct_name = name_code + " " + tx[FUND_CODE]
                    else:
                        raise Exception("Could NOT find name key {}!".format(name_key))
                    print_info("asset_acct_name = {}".format(asset_acct_name), BLUE)

                    # special location for Trust Asset account
                    if asset_acct_name == TRUST_AST_ACCT:
                        asset_parent = self.root.lookup_by_name(TRUST)
                    print_info("asset_parent = {}".format(asset_parent.GetName()), BLUE)

                    # get the asset account
                    asset_acct = asset_parent.lookup_by_name(asset_acct_name)
                    if asset_acct is None:
                        # just skip updating cash-holding funds
                        if str(val) == '100000/10000':
                            continue
                        else:
                            raise Exception(
                                "Could NOT find acct '{}' under parent '{}'".format(asset_acct_name, asset_parent.GetName()))

                    print_info("Adding: {}[{}] @ ${}".format(asset_acct_name, tx_coll.get_date_str(), val), GREEN)

                    pr = GncPrice(self.book)
                    pr.begin_edit()
                    pr.set_time64(tx_coll.get_date())
                    comm = asset_acct.GetCommodity()
                    print_info("Commodity = {}:{}".format(comm.get_namespace(), comm.get_printname()), YELLOW)
                    pr.set_commodity(comm)

                    pr.set_currency(self.currency)
                    pr.set_value(val)
                    pr.set_source_string("user:price")
                    pr.set_typestr('last')
                    pr.commit_edit()

                    if self.prod:
                        print_info("PROD: Add Price to DB.\n", GREEN)
                        self.price_db.add_price(pr)
                    else:
                        print_info("PROD: ABANDON Prices!\n", RED)

            if self.prod:
                msg = "PROD: COMMIT Price DB edits and Save session."
                print_info("PROD: COMMIT Price DB edits and Save session.", GREEN)
                self.price_db.commit_edit()
                # only ONE session save for the entire run
                self.session.save()

            self.session.end()
            self.session.destroy()

        except Exception as e:
            msg = "get_prices_and_save() EXCEPTION!! '{}'".format(str(e))
            print_error(msg)
            if "session" in locals() and self.session is not None:
                self.session.end()
                self.session.destroy()
            raise

        return msg


def mon_qtr_rep_main(args):
    usage = "usage: py36 parseMonarchQtrRep.py <monarch pdf-text file> <gnucash file> <mode: prod|test>"
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

    gnc_file = args[1]
    if not osp.isfile(gnc_file):
        print_error("File path '{}' does not exist. Exiting...".format(gnc_file))
        print_info(usage, GREEN)
        exit()
    print_info("gnc_file = {}".format(gnc_file))

    mode = args[2].upper()

    global strnow
    strnow = dt.now().strftime(DATE_STR_FORMAT)

    pr_creator = MonarchQrepToGncPrices(mon_file, gnc_file, mode)
    record = pr_creator.parse_monarch_qtrep()
    record.set_filename(mon_file)

    # PRINT RECORD AS JSON FILE
    if mode == PROD:
        # pluck path and basename from mon_file to use for the saved json file
        ospath, fname = osp.split(mon_file)
        # print_info("path: {}".format(ospath))
        # save to the output folder
        path = ospath.replace('txtFromPdf', 'jsonFromTxt')
        basename, ext = osp.splitext(fname)
        # add a timestamp to get a unique file name
        out_file = path + '/' + basename + '_' + strnow + ".json"
        print_info("\nout_file: {}".format(out_file))
        fp = open(out_file, 'w', encoding='utf-8')
        json.dump(record.to_json(), fp, indent=4)

    msg = pr_creator.get_prices_and_save(record)

    print_info("\n >>> PROGRAM ENDED.", GREEN)
    return msg


if __name__ == '__main__':
    import sys
    mon_qtr_rep_main(sys.argv[1:])
