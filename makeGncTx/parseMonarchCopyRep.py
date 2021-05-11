###############################################################################################################################
# coding=utf-8
#
# parseMonarchCopyRep.py -- parse a file with COPIED Monarch Report text, assembling and saving
#                           the information as transaction and price parameters in an InvestmentRecord,
#                           OR use a JSON file with previously saved Monarch tx/price data,
#                           then optionally write the transactions/prices to a specified Gnucash file.
#
# Copyright (c) 2019-21 Mark Sattolo <epistemik@gmail.com>

__author__ = "Mark Sattolo"
__author_email__ = "epistemik@gmail.com"
__created__ = "2019-06-22"
__updated__ = "2021-05-11"

from sys import path, argv, exc_info
import re
import json
from argparse import ArgumentParser
path.append("/newdata/dev/git/Python/utils")
from mhsUtils import JSON, save_to_json, get_base_filename, get_base_fileparts
import mhsLogging
path.append("/newdata/dev/git/Python/Gnucash/common")
from gncUtils import *

base_run_file = get_base_filename(__file__)


class ParseMonarchInput:
    def __init__(self, r_infile:str, r_lgr:lg.Logger):
        self.in_file = r_infile
        self._input_txs = InvestmentRecord(r_lgr)
        self._gnucash_txs = InvestmentRecord(r_lgr)
        self._lgr = r_lgr

    def get_input_record(self) -> InvestmentRecord:
        return self._input_txs

    def get_gnucash_record(self) -> InvestmentRecord:
        return self._gnucash_txs

    def parse_input_file(self, ftype:str):
        self._input_txs.set_filename(self.in_file)

        if ftype == MON.lower():
            self._lgr.info(F"Have a {MON.upper()} type input file.")
            self.parse_monarch_info()
            self.add_balance_to_trade()
        elif ftype == JSON:
            self._lgr.info(F"Have a {JSON.upper()} type input file.")
            self.parse_json_info()
        else:
            raise ValueError(F"Improper file type: {ftype}")

    def parse_json_info(self):
        """parse the json file and copy the data to self._input_txs"""
        self._lgr.info( get_current_time() )
        with open(self.in_file) as inf:
            data = json.load(inf)
        self._input_txs.set_data( data[PLAN_DATA] )
        self._input_txs.set_owner( data[OWNER] )
        self._lgr.debug( self._input_txs.get_data() )

    def parse_monarch_info(self):
        """
        parsing for NEW format txt files, ~ May 31, 2019, just COPIED from Monarch web page,
        as new Monarch pdf's are no longer practical to use -- extracted text just too inconsistent...
        >> add ALL price and trade info to an InvestmentRecord instance
        *loop lines:
            1: skip if line too short
            2: date
            3: owner
            4: FUND ->
                 find planID in words; type is PLAN_IDS[word][PLAN_TYPE]
            5: Pass if planID is Joint and owner is Lulu
            6: Prices ->
                 match fund name at [0]:
                    record: fund company, fund, balance, price, doc date
            7: Trades ->
                 match date at [0]:
                    record: fund, desc, gross, units, price, load, trade date
        """
        self._lgr.debug( get_current_time() )

        re_date = re.compile(r"([0-9]{2}-\w{3}-[0-9]{4})")

        mon_state = FIND_DATE
        plan_type = UNKNOWN
        plan_id = UNKNOWN
        with open(self.in_file) as mfp:
            ct = 0
            for line in mfp:
                ct += 1
                words = line.split()
                if len(words) <= 1:
                    continue

                if mon_state == FIND_DATE:
                    re_match = re.match(re_date, words[0])
                    if re_match:
                        doc_date = re_match.group(1)
                        self._lgr.debug(F"Document date: {doc_date}")
                        mon_state = FIND_OWNER
                        continue

                if mon_state == FIND_OWNER:
                    if words[0] == OPEN:
                        owner = MON_MARK if MON_ROBB in words else MON_LULU
                        self._input_txs.set_owner(owner)
                        self._lgr.debug(F"\n\t\u0022Current owner: {owner}\u0022")
                        mon_state = STATE_SEARCH
                        continue

                if words[0] == FUND.upper():
                    for word in words:
                        if word in PLAN_IDS:
                            plan_type = PLAN_IDS[word][0]
                            plan_id = word
                            self._lgr.debug(F"\n\t\t\u0022Current plan: type = {plan_type} ; id = {plan_id}\u0022")
                            continue

                if mon_state == STATE_SEARCH:
                    # ensure that JOINT transactions are only recorded ONCE
                    if owner == MON_LULU and plan_id == JOINT_PLAN_ID:
                        continue

                # PRICES
                if words[0] in FUND_NAME_CODE:
                    # NOTE: price lines start with a fund name and have enough words to match the accounts header
                    if len(words) >= 11:
                        fd_cpy = words[0]
                        self._lgr.debug(F"FOUND a NEW Price: {fd_cpy}")
                        fund = words[-11]
                        if '-' in fund:
                            fund = fund.replace('-', ' ')
                        else:
                            raise Exception(F"Did NOT find proper fund name: {fund}!")
                        bal = words[-9]
                        if '.' not in bal or '$' in bal:
                            raise Exception(F"Did NOT find proper balance: {bal}!")
                        price = words[-8]
                        if '.' not in price or '$' not in price:
                            raise Exception(F"Did NOT find proper price: {price}!")
                        curr_tx = { DATE:doc_date, DESC:PRICE, FUND_CMPY:fd_cpy, FUND:fund, UNIT_BAL:bal, PRICE:price }
                        self._input_txs.add_tx(plan_type, PRICE, curr_tx)
                        self._lgr.debug(F"ADD current Price Tx:\n\t{curr_tx}")
                    continue

                # TRADES
                re_match = re.match(re_date, words[0])
                # NOTE: trade lines start with a date and have enough words to match the tx header
                if re_match and len(words) >= 8:
                    tx_date = re_match.group(1)
                    self._lgr.debug(F"FOUND a NEW Tx! Date: {tx_date}")
                    fund_cpy = words[-8]
                    if fund_cpy not in FUND_NAME_CODE.values():
                        raise Exception(F"Did NOT find proper Fund company: {fund_cpy}!")
                    fund_code = words[-7]
                    if not fund_code.isnumeric():
                        raise Exception(F"Did NOT find proper Fund code: {fund_code}!")
                    fund = fund_cpy + " " + fund_code

                    # have to identify & handle different types
                    tx_type = words[1]
                    if tx_type == DOLLAR:
                        tx_type = DCA_IN if words[4] == SW_IN else DCA_OUT
                    desc = words[2] if tx_type == INTRCL else TX_TYPES[tx_type]
                    if not desc.isprintable():
                        raise Exception(F"Did NOT find proper Description: {desc}!")

                    # noinspection PyDictCreation
                    curr_tx = { TRADE_DATE:tx_date, FUND:fund, TYPE:desc, CMPY:COMPANY_NAME[fund_cpy] }
                    curr_tx[DESC]  = curr_tx[CMPY] + ": " + desc
                    curr_tx[UNITS] = words[-1]
                    if '.' not in curr_tx[UNITS] or '$' in curr_tx[UNITS]:
                        raise Exception(F"Did NOT find proper Units!: {curr_tx[UNITS]}")
                    curr_tx[PRICE] = words[-2]
                    if '.' not in curr_tx[PRICE] or '$' not in curr_tx[PRICE]:
                        raise Exception(F"Did NOT find proper Price: {curr_tx[PRICE]}!")
                    curr_tx[NET]   = words[-3]
                    if '.' not in curr_tx[NET] or '$' not in curr_tx[NET]:
                        raise Exception(F"Did NOT find proper Net amount: {curr_tx[NET]}!")
                    curr_tx[GROSS] = words[-4]
                    if '.' not in curr_tx[GROSS] or '$' not in curr_tx[GROSS]:
                        raise Exception(F"Did NOT find proper Gross amount: {curr_tx[GROSS]}!")
                    curr_tx[LOAD]  = words[-5]
                    if not curr_tx[LOAD].isalpha():
                        raise Exception(F"Did NOT find proper Load: {curr_tx[LOAD]}!")

                    self._input_txs.add_tx(plan_type, TRADE, curr_tx)
                    self._lgr.debug(F"ADD current Trade Tx:\n\t{curr_tx}")

    def get_trade_info(self, mon_tx:dict, plan_type:str, ast_parent:Account, rev_acct:Account) -> (dict,dict):
        """
        Parse a Monarch trade transaction:
        * useful to have this intermediate function to obtain a collection of txs with the Gnucash data handy
          and also to ensure that all the matching 'in' and 'out' Switch txs are properly paired up...
          before creating the actual Gnucash.Transactions
            Asset accounts: use the proper path to find the parent then search for the Fund Code in the descendants
            Revenue accounts: pick the proper account based on owner and plan type
            Amounts: re match to Gross and Net then use the match groups
            date: convert the date then get day, month and year to form a Gnc date
            Units: re match and concatenate the two groups on either side of decimal point
            Description: use DESC and Fund Company
        :param     mon_tx: Monarch transaction
        :param  plan_type: plan name from InvestmentRecord
        :param ast_parent: Asset parent account
        :param   rev_acct: Revenue account
        :return: one trade tx or both txs of a switch, if available
        """
        self._lgr.debug(F"plan type = {plan_type}, asset parent = {ast_parent.GetName()}")

        # set the regex needed to match the required groups in each value
        # NOTE: re_dollars must match (leading minus sign) OR (amount is in parentheses) to indicate NEGATIVE number
        re_dollars = re.compile(r"^([-(]?)\$([0-9,]{1,6})\.([0-9]{2}).*(\)?)")
        re_units   = re.compile(r"^(-?)([0-9]{1,5})\.([0-9]{4}).*")

        fund_name = mon_tx[FUND]
        asset_acct = self.gnc_session.get_account(fund_name, ast_parent)

        # special locations for Trust revenue accounts
        if fund_name == TRUST_AST_ACCT:
            trust_acct = TRUST_REV_ACCT if mon_tx[TYPE] == TX_TYPES[REINV] else TRUST_EQY_ACCT
            rev_acct = self.gnc_session.get_account(trust_acct)

        self._lgr.debug(F"get_trade_info(): asset account = {asset_acct.GetName()}; revenue account = {rev_acct.GetName()}")

        # get required date fields
        conv_date = dt.strptime(mon_tx[TRADE_DATE], "%d-%b-%Y")
        init_tx = { FUND:fund_name, ACCT:asset_acct, REV:rev_acct, TRADE_DATE:mon_tx[TRADE_DATE],
                    TRADE_DAY:conv_date.day, TRADE_MTH:conv_date.month, TRADE_YR:conv_date.year }
        self._lgr.debug(F"trade day-month-year = {init_tx[TRADE_DAY]}-{init_tx[TRADE_MTH]}-{init_tx[TRADE_YR]}")

        # different accounts depending if Switch, Redemption, Purchase, Distribution
        init_tx[TYPE] = mon_tx[TYPE]
        init_tx[CMPY] = mon_tx[CMPY]

        # get the gross dollar value of the tx
        re_match = re.match(re_dollars, mon_tx[GROSS])
        if re_match:
            str_gross = re_match.group(2) + re_match.group(3)
            # remove possible comma
            gross_amt = int(str_gross.replace(',', ''))
            # if match group 1 is not empty, amount is negative
            if re_match.group(1):
                gross_amt *= -1
            self._lgr.debug(F"gross amount = {gross_amt}")
            init_tx[GROSS] = gross_amt
        else:
            raise Exception(F"PROBLEM: gross amount DID NOT match with value: {mon_tx[GROSS]}!")

        # get the net dollar value of the tx
        re_match = re.match(re_dollars, mon_tx[NET])
        if re_match:
            str_net = re_match.group(2) + re_match.group(3)
            # remove possible comma
            net_amount = int(str_net.replace(',', ''))
            # if match group 1 is not empty, amount is negative
            if re_match.group(1):
                net_amount *= -1
            self._lgr.debug(F"net_amount = {net_amount}")
            init_tx[NET] = net_amount
        else:
            raise Exception(F"PROBLEM: net amount DID NOT match with value: {mon_tx[NET]}!")

        # get the units of the tx
        re_match = re.match(re_units, mon_tx[UNITS])
        if re_match:
            units = int(re_match.group(2) + re_match.group(3))
            # if match group 1 is not empty, units is negative
            if re_match.group(1):
                units *= -1
            self._lgr.debug(F"units = {units}")
            init_tx[UNITS] = units
        else:
            raise Exception(F"PROBLEM: units DID NOT match with value: {mon_tx[UNITS]}!")

        # assemble the Description string
        descr = "{} {}".format(mon_tx[DESC], fund_name)
        init_tx[DESC] = descr
        self._lgr.debug(F"descr = {init_tx[DESC]}")

        # notes field
        notes = mon_tx[NOTES] if NOTES in mon_tx else F"Load = {mon_tx[LOAD]}"
        init_tx[NOTES] = notes
        self._lgr.debug(F"notes = {init_tx[NOTES]}")

        pair_tx = None
        have_pair = False
        if init_tx[TYPE] in PAIRED_TYPES:
            self._lgr.debug("Tx is a Switch to ANOTHER account in SAME Fund company.")
            # look for switches in this plan type with same company and date but with opposite gross value
            for gnc_tx in self._gnucash_txs.get_trades(plan_type):
                if gnc_tx[TYPE] in PAIRED_TYPES and gnc_tx[FUND].split()[0] == init_tx[FUND].split()[0] \
                        and gnc_tx[GROSS] == (net_amount * -1) and gnc_tx[TRADE_DATE] == init_tx[TRADE_DATE]:
                    # FOUND THE FIRST ITEM IN THIS PAIR
                    have_pair = True
                    pair_tx = gnc_tx
                    self._lgr.debug("*** Found the MATCH of a Switch pair ***")
                    break

            if not have_pair:
                # store the tx until we find the matching tx
                self._gnucash_txs.add_tx(plan_type, TRADE, init_tx)
                self._lgr.debug("Found the FIRST of a Switch pair...\n")

        return init_tx, pair_tx

    def process_monarch_trades(self, mon_tx:dict, plan_type:str, ast_parent:Account, p_owner:str):
        """
        Obtain each Monarch trade as a transaction item, or pair of transactions where required,
        and forward to Gnucash processing
        :param     mon_tx: Monarch transaction information
        :param  plan_type: plan names from Configuration.InvestmentRecord
        :param ast_parent: Asset parent account
        :param    p_owner: str name
        """
        self._lgr.debug(F"plan type = {plan_type}, asset parent = {ast_parent.GetName()}, owner = {p_owner}")
        try:
            rev_acct = self.gnc_session.get_revenue_account(plan_type, p_owner)

            # get all the tx required information from the Monarch json
            tx1, tx2 = self.get_trade_info(mon_tx, plan_type, ast_parent, rev_acct)

            # just return if there is a matching tx but we don't have it yet
            if tx1[TYPE] in PAIRED_TYPES and tx2 is None:
                return

            # use the Gnucash API to create Transactions and save to a Gnucash file
            self.gnc_session.create_trade_tx(tx1, tx2)

        except Exception as pmte:
            pmte_msg = F"EXCEPTION: {repr(pmte)}!\n"
            self._lgr.error(pmte_msg)
            raise pmte.with_traceback( exc_info()[2] )

    def add_balance_to_trade(self):
        """
        Append the current unit balance from the Price list to the latest Trade tx.
        for each plan type:
            go through Price txs:
                for each tx, find the latest Trade tx for that fund, if any...
                if found, add the Unit Balance from the Price tx to the Trade tx
        """
        self._lgr.debug( get_current_time() )
        for iplan in self._input_txs.get_data():
            self._lgr.debug(F"plan type = {repr(iplan)}")
            plan = self._input_txs.get_plan(iplan)
            for tx in plan[PRICE]:
                indx = 0
                latest_indx = -1
                latest_dte = None
                for trd in plan[TRADE]:
                    if trd[FUND] == tx[FUND]:
                        trd_date = dt.strptime(trd[TRADE_DATE], "%d-%b-%Y")
                        if latest_dte is None or trd_date > latest_dte:
                            latest_dte = trd_date
                            self._lgr.debug(F"Latest date for {tx[FUND]} = {latest_dte}")
                            latest_indx = indx
                    indx += 1
                if latest_indx > -1:
                    plan[TRADE][latest_indx][UNIT_BAL] = tx[UNIT_BAL]
                    plan[TRADE][latest_indx][NOTES] = F"{tx[FUND]} Balance = {tx[UNIT_BAL]}"

    # noinspection PyAttributeOutsideInit
    def insert_txs_to_gnucash_file(self, p_gncs:GnucashSession):
        """
        transfer the Monarch information to a Gnucash file
        :return: gnucash session log or error message
        """
        self._lgr.info(get_current_time())
        self.gnc_session = p_gncs
        try:
            owner = self._input_txs.get_owner()
            self._lgr.debug(F"Owner = {owner}")

            self.gnc_session.begin_session()
            self.create_gnucash_info(owner)
            self.gnc_session.end_session()

        except Exception as itgfe:
            sgfe_msg = F"EXCEPTION: {repr(itgfe)}!"
            self._lgr.error(sgfe_msg)
            self.gnc_session.check_end_session(locals())
            raise itgfe.with_traceback( exc_info()[2] )

    def create_gnucash_info(self, p_owner:str):
        """
        Process each transaction from the Monarch input file to get the required Gnucash information
        """
        domain = self.gnc_session.get_domain()
        plans = self._input_txs.get_data()
        for plan_type in plans:
            self._lgr.debug(F"\n\n\t\t\u0022Plan type = {plan_type}\u0022")

            asset_parent = self.gnc_session.get_asset_account(plan_type, p_owner)
            self._lgr.debug(F"create_gnucash_info(): asset parent = {asset_parent.GetName()}")

            if domain in (TRADE,BOTH):
                for mon_tx in plans[plan_type][TRADE]:
                    self.process_monarch_trades(mon_tx, plan_type, asset_parent, p_owner)

            if domain in (PRICE,BOTH):
                for mon_tx in plans[plan_type][PRICE]:
                    self.gnc_session.create_price(mon_tx, asset_parent)

# END class ParseMonarchCopyReport


def process_args():
    arg_parser = ArgumentParser(description="Process Monarch or JSON input data to obtain Gnucash transactions",
                                prog="parseMonarchCopyRep.py")
    # required arguments
    required = arg_parser.add_argument_group("REQUIRED")
    required.add_argument('-i', '--inputfile', required=True, help="path & name of the Monarch or JSON input file")
    # required if PROD
    subparsers = arg_parser.add_subparsers(help="with gnc option: MUST specify -g FILENAME and -t TX_TYPE")
    gnc_parser = subparsers.add_parser("gnc", help="Insert the parsed trade and/or price transactions to a Gnucash file")
    gnc_parser.add_argument('-g', '--gncfile', required=True, help="path & name of the Gnucash file")
    gnc_parser.add_argument('-t', '--type', required=True, choices=[TRADE, PRICE, BOTH],
                            help="type of transaction to record: {} or {} or {}".format(TRADE, PRICE, BOTH))
    # optional arguments
    arg_parser.add_argument('-l', '--level', type=int, default=lg.INFO, help="set LEVEL of logging output")
    arg_parser.add_argument('--json',  action="store_true", help="Write the parsed Monarch data to a JSON file")

    return arg_parser


def process_input_parameters(argx:list):
    args = process_args().parse_args(argx)
    info = [F"args = {args}"]

    if not osp.isfile(args.inputfile):
        raise Exception(F"File path '{args.inputfile}' does not exist! Exiting...")
    info.append(F"Input file = {args.inputfile}")

    mode = TEST
    domain = BOTH
    gnc_file = None
    if "gncfile" in args:
        if not osp.isfile(args.gncfile):
            raise Exception(F"File path '{args.gncfile}' does not exist. Exiting...")
        gnc_file = args.gncfile
        info.append(F"writing to Gnucash file = {gnc_file}")
        mode = SEND
        domain = args.type
        info.append(F"Inserting '{domain}' transaction types to Gnucash.")
    else:
        info.append("mode = TEST")

    return args.inputfile, args.json, args.level, mode, gnc_file, domain, info


def main_monarch_input(args:list) -> list:
    in_file, save_monarch, level, mode, gnc_file, domain, parse_info = process_input_parameters(args)

    log_control = mhsLogging.MhsLogger(base_run_file, con_level = level, suffix = "gncout")
    log_control.log_list(parse_info)
    lgr = log_control.get_logger()

    log_control.show(F"Runtime = {get_current_time()}")
    lgr.debug( repr(lgr.handlers) )

    # get name parts from the input file path
    basename, ftype = get_base_fileparts(in_file)
    ftype = ftype[1:]

    gnc_session = None
    parser = ParseMonarchInput(in_file, lgr)
    try:
        # parse an external Monarch COPIED report file
        # OR a JSON file with previously saved txs and/or prices
        parser.parse_input_file(ftype)

        if mode == SEND:
            # add gnc file name to log file name
            basename += '_' + get_base_filename(gnc_file)

            gnc_session = GnucashSession(mode, gnc_file, domain, lgr)
            parser.insert_txs_to_gnucash_file(gnc_session)

        msg = log_control.get_saved_info()

        if ftype == MON.lower() and save_monarch:
            out_file = save_to_json(basename, parser.get_input_record().to_json(), get_current_time(FILE_DATETIME_FORMAT))
            lgr.info(F"Created Monarch JSON file: {out_file}")

    except Exception as ex:
        ex_msg = repr(ex)
        lgr.exception(ex_msg)
        msg = [ex_msg]
        if gnc_session:
            gnc_session.end_session(False)

    lgr.warning(">>> PROGRAM ENDED.")
    return msg


if __name__ == "__main__":
    main_monarch_input(argv[1:])
    exit()
