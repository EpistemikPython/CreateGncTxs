###############################################################################################################################
# coding=utf-8
#
# parseMonarchCopyRep.py -- parse a file with COPIED Monarch Report text, assembling and saving
#                           the information as transaction and price parameters in an InvestmentRecord,
#                           then saving to a specified Gnucash file
#
# Copyright (c) 2020 Mark Sattolo <epistemik@gmail.com>
#
__author__ = 'Mark Sattolo'
__author_email__ = 'epistemik@gmail.com'
__python_version__  = 3.9
__gnucash_version__ = 3.8
__created__ = '2019-06-22'
__updated__ = '2020-01-11'

from sys import path, argv, exc_info
import re
from argparse import ArgumentParser
path.append("/home/marksa/dev/git/Python/Gnucash/updateBudgetQtrly")
from gnucash_utilities import *

JSON_FOLDER = 'jsonFromTxt'


# TODO: use investment.TxRecord instead of dicts to store Monarch & Gnucash information
class ParseMonarchCopyReport:
    def __init__(self, p_monfile:str, p_debug:bool=False):
        self.mon_file = p_monfile
        self.debug = p_debug
        self._monarch_txs = InvestmentRecord()
        self._gnucash_txs = InvestmentRecord()

        self._logger = SattoLog(my_color=MAGENTA, do_printing=p_debug)
        self._log('class ParseMonarchCopyReport')

    def _log(self, p_msg:object, p_color:str=''):
        self._logger.print_info(p_msg, p_color, p_info=inspect.currentframe().f_back)

    def _err(self, p_msg:object, err_info:object):
        self._logger.print_info(p_msg, BR_RED, p_info=err_info)

    def set_filename(self, fn:str):
        self._monarch_txs.set_filename(fn)

    def get_monarch_record(self) -> InvestmentRecord:
        return self._monarch_txs

    def get_gnucash_record(self) -> InvestmentRecord:
        return self._gnucash_txs

    def get_log(self) -> list:
        return self._logger.get_log()

    def parse_copy_info(self):
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
                 match fund name:
                    record fund company, fund, balance, price, doc date
            7: Trades ->
                 match date:
                    record fund, desc, gross, units, price, load, trade date
        :return nil
        """
        self._log('ParseMonarchCopyReport.parse_copy_info()')

        re_date = re.compile(r"([0-9]{2}-\w{3}-[0-9]{4})")

        mon_state = FIND_DATE
        plan_type = UNKNOWN
        plan_id = UNKNOWN
        with open(self.mon_file) as fp:
            ct = 0
            for line in fp:
                ct += 1
                words = line.split()
                if len(words) <= 1:
                    continue

                if mon_state == FIND_DATE:
                    re_match = re.match(re_date, words[0])
                    if re_match:
                        doc_date = re_match.group(1)
                        self._log(F"Document date: {doc_date}")
                        mon_state = FIND_OWNER
                        continue

                if mon_state == FIND_OWNER:
                    if words[0] == OPEN:
                        owner = MON_MARK if MON_ROBB in words else MON_LULU
                        self._monarch_txs.set_owner(owner)
                        self._log(F"\n\t\u0022Current owner: {owner}\u0022")
                        mon_state = STATE_SEARCH
                        continue

                if words[0] == FUND.upper():
                    for word in words:
                        if word in PLAN_IDS:
                            plan_type = PLAN_IDS[word][PLAN_TYPE]
                            plan_id = word
                            self._log(F"\n\t\u0022Current plan: type = {plan_type} ; id = {plan_id}\u0022")
                            continue

                if mon_state == STATE_SEARCH:
                    # ensure that JOINT transactions are only recorded ONCE
                    if owner == MON_LULU and plan_id == JOINT_PLAN_ID:
                        continue

                # PRICES
                if words[0] in FUND_NAME_CODE:
                    fd_co = words[0]
                    fund = words[-10].replace('-', ' ')
                    bal = words[-8]
                    price = words[-7]
                    curr_tx = {DATE:doc_date, DESC:PRICE, FUND_CMPY:fd_co, FUND:fund, UNIT_BAL:bal, PRICE:price}
                    self._monarch_txs.add_tx(plan_type, PRICE, curr_tx)
                    self._log(F"ADD current Price Tx:\n\t{curr_tx}")
                    continue

                # TRADES
                re_match = re.match(re_date, words[0])
                if re_match:
                    tx_date = re_match.group(1)
                    self._log(F"FOUND a NEW tx! Date: {tx_date}")
                    fund_co = words[-8]
                    fund = fund_co + " " + words[-7]
                    tx_type = words[1]
                    if tx_type == DOLLAR:
                        tx_type = DCA_IN if words[4] == SW_IN else DCA_OUT
                    # have to identify & handle different types
                    desc = words[2] if tx_type == INTRCL else TX_TYPES[tx_type]
                    # noinspection PyDictCreation
                    curr_tx = {TRADE_DATE:tx_date, FUND:fund, TYPE:desc, CMPY:COMPANY_NAME[fund_co]}
                    curr_tx[DESC]  = curr_tx[CMPY] + ": " + desc
                    curr_tx[GROSS] = words[-4]
                    curr_tx[NET]   = words[-3]
                    curr_tx[UNITS] = words[-1]
                    curr_tx[PRICE] = words[-2]
                    curr_tx[LOAD]  = words[-5]
                    self._monarch_txs.add_tx(plan_type, TRADE, curr_tx)
                    self._log(F"ADD current Trade Tx:\n\t{curr_tx}")

    # TODO: Produce Gnucash txs directly in a GnucashSession function??
    def get_trade_info(self, mon_tx:dict, plan_type:str, ast_parent:Account, rev_acct:Account) -> (dict,dict):
        """
        Parse a Monarch trade transaction
        ** useful to have this intermediate function to obtain matching 'in' and 'out' Switch txs...
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
        self._log('ParseMonarchCopyReport.get_trade_info()', BLUE)

        # set the regex needed to match the required groups in each value
        # re_dollars must match (leading minus sign) OR (amount is in parentheses) to indicate NEGATIVE number
        re_dollars = re.compile(r"^([-(]?)\$([0-9,]{1,6})\.([0-9]{2}).*(\)?)")
        re_units   = re.compile(r"^(-?)([0-9]{1,5})\.([0-9]{4}).*")

        fund_name = mon_tx[FUND]
        asset_acct = self.gnc_session.get_account(fund_name, ast_parent)

        # special locations for Trust revenue accounts
        if fund_name == TRUST_AST_ACCT:
            trust_acct = TRUST_REV_ACCT if mon_tx[TYPE] == TX_TYPES[REINV] else TRUST_EQY_ACCT
            rev_acct = self.gnc_session.get_account(trust_acct)

        self._log(F"get_trade_info(): asset account = {asset_acct.GetName()}; revenue account = {rev_acct.GetName()}")

        # get required date fields
        conv_date = dt.strptime(mon_tx[TRADE_DATE], "%d-%b-%Y")
        init_tx = {FUND:fund_name, ACCT:asset_acct, REVENUE:rev_acct, TRADE_DATE:mon_tx[TRADE_DATE],
                   TRADE_DAY:conv_date.day, TRADE_MTH:conv_date.month, TRADE_YR:conv_date.year}
        self._log(F"trade day-month-year = {init_tx[TRADE_DAY]}-{init_tx[TRADE_MTH]}-{init_tx[TRADE_YR]}")

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
            self._log(F"gross amount = {gross_amt}")
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
            self._log(F"net_amount = {net_amount}")
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
            self._log(F"units = {units}")
            init_tx[UNITS] = units
        else:
            raise Exception(F"PROBLEM: units DID NOT match with value: {mon_tx[UNITS]}!")

        # assemble the Description string
        descr = "{} {}".format(mon_tx[DESC], fund_name)
        init_tx[DESC] = descr
        self._log(F"descr = {init_tx[DESC]}", CYAN)

        # notes field
        notes = mon_tx[NOTES] if NOTES in mon_tx else F"Load = {mon_tx[LOAD]}"
        init_tx[NOTES] = notes
        self._log(F"notes = {init_tx[NOTES]}", CYAN)

        pair_tx = None
        have_pair = False
        if init_tx[TYPE] in PAIRED_TYPES:
            self._log('Tx is a Switch to ANOTHER account in SAME Fund company.', BLUE)
            # look for switches in this plan type with same company and date but with opposite gross value
            for gnc_tx in self._gnucash_txs.get_trades(plan_type):
                if gnc_tx[TYPE] in PAIRED_TYPES and gnc_tx[FUND].split()[0] == init_tx[FUND].split()[0] \
                        and gnc_tx[GROSS] == (net_amount * -1) and gnc_tx[TRADE_DATE] == init_tx[TRADE_DATE]:
                    # ALREADY HAVE THE FIRST ITEM OF THE PAIR
                    have_pair = True
                    pair_tx = gnc_tx
                    self._log('*** Found the MATCH of a Switch pair ***', BROWN)
                    break

            if not have_pair:
                # store the tx until we find the matching tx
                self._gnucash_txs.add_tx(plan_type, TRADE, init_tx)
                self._log('Found the FIRST of a Switch pair...\n', BROWN)

        return init_tx, pair_tx

    def process_monarch_trade(self, mon_tx:dict, plan_type:str, ast_parent:Account, p_owner:str):
        """
        Obtain each Monarch trade as a transaction item, or pair of transactions where required,
        and forward to Gnucash processing
        :param     mon_tx: Monarch transaction information
        :param  plan_type: plan names from Configuration.InvestmentRecord
        :param ast_parent: Asset parent account
        :param    p_owner: str name
        """
        self._log('ParseMonarchCopyReport.process_monarch_trade()', BLUE)
        try:
            rev_acct = self.gnc_session.get_revenue_account(plan_type, p_owner)

            # get the additional required information from the Monarch json
            tx1, tx2 = self.get_trade_info(mon_tx, plan_type, ast_parent, rev_acct)

            # just return if there is a matching tx but we don't have it yet
            if tx1[TYPE] in PAIRED_TYPES and tx2 is None:
                return

            self.gnc_session.create_trade_tx(tx1, tx2)

        except Exception as pmte:
            pmte_msg = F"process_monarch_trade() EXCEPTION: {repr(pmte)}!\n"
            tb = exc_info()[2]
            self._err(pmte_msg, tb)
            raise pmte.with_traceback(tb)

    def add_balance_to_trade(self):
        """
        Append the current unit balance from the Price list to the latest Trade tx.
        for each plan type:
            go through Price txs:
                for each tx, find the latest Trade tx for that fund, if any...
                if found, add the Unit Balance from the Price tx to the Trade tx
        :return: nil
        """
        self._log('ParseMonarchCopyReport.add_balance_to_trade()')
        for iplan in self._monarch_txs.get_plans():
            self._log(F"plan type = {repr(iplan)}")
            plan = self._monarch_txs.get_plan(iplan)
            for tx in plan[PRICE]:
                indx = 0
                latest_indx = -1
                latest_dte = None
                for trd in plan[TRADE]:
                    if trd[FUND] == tx[FUND]:
                        trd_date = dt.strptime(trd[TRADE_DATE], '%d-%b-%Y')
                        if latest_dte is None or trd_date > latest_dte:
                            latest_dte = trd_date
                            self._log(F"Latest date for {tx[FUND]} is {latest_dte}")
                            latest_indx = indx
                    indx += 1
                if latest_indx > -1:
                    plan[TRADE][latest_indx][UNIT_BAL] = tx[UNIT_BAL]
                    plan[TRADE][latest_indx][NOTES] = F"{tx[FUND]} Balance = {tx[UNIT_BAL]}"

    def insert_txs_to_gnucash_file(self, p_gncs:GnucashSession) -> list:
        """
        transfer the Monarch information to a Gnucash file
        :return: gnucash session log or error message
        """
        self._log('ParseMonarchCopyReport.insert_txs_to_gnucash_file()')
        # noinspection PyAttributeOutsideInit
        self.gnc_session = p_gncs
        msg = [TEST]
        try:
            owner = self._monarch_txs.get_owner()
            self._log(F"Owner = {owner}")

            self.gnc_session.begin_session()
            self.create_gnucash_info(owner)
            self.gnc_session.end_session()

            msg = self._logger.get_log()

        except Exception as itgfe:
            sgfe_msg = F"insert_txs_to_gnucash_file() EXCEPTION: {repr(itgfe)}!"
            tb = exc_info()[2]
            self._err(sgfe_msg, tb)
            self.gnc_session.check_end_session(locals())
            raise itgfe.with_traceback(tb)

        self._logger.append(msg)
        return msg

    def create_gnucash_info(self, p_owner:str):
        """
        Process each transaction from the Monarch input file to get the required Gnucash information
        """
        domain = self.gnc_session.get_domain()
        plans = self._monarch_txs.get_plans()
        for plan_type in plans:
            self._log(F"\n\n\t\t\u0022Plan type = {plan_type}\u0022", BROWN)

            asset_parent = self.gnc_session.get_asset_parent(plan_type, p_owner)
            self._log(F"create_gnucash_info(): asset parent = {asset_parent.GetName()}")

            if domain in (TRADE,BOTH):
                for mon_tx in plans[plan_type][TRADE]:
                    self.process_monarch_trade(mon_tx, plan_type, asset_parent, p_owner)

            if domain in (PRICE,BOTH):
                for mon_tx in plans[plan_type][PRICE]:
                    self.gnc_session.create_price_tx(mon_tx, asset_parent)

# END class ParseMonarchCopyReport


def process_args():
    arg_parser = ArgumentParser(description='Process a copied Monarch Report to obtain Gnucash transactions',
                                prog='parseMonarchCopyRep.py')
    # required arguments
    required = arg_parser.add_argument_group('REQUIRED')
    required.add_argument('-m', '--monarch', required=True, help='path & filename of the copied Monarch Report file')
    # required if PROD
    subparsers = arg_parser.add_subparsers(help='with gnc option: MUST specify -f FILENAME and -t TX_TYPE')
    gnc_parser = subparsers.add_parser('gnc', help='Insert the parsed trade and/or price transactions to a Gnucash file')
    gnc_parser.add_argument('-f', '--filename', required=True, help='path & filename of the Gnucash file')
    gnc_parser.add_argument('-t', '--type', required=True, choices=[TRADE, PRICE, BOTH],
                            help="type of transaction to record: {} or {} or {}".format(TRADE, PRICE, BOTH))
    # optional arguments
    arg_parser.add_argument('--json',  action='store_true', help='Write the parsed Monarch data to a JSON file')
    arg_parser.add_argument('--debug', action='store_true', help='GENERATE DEBUG OUTPUT: MANY LINES!')

    return arg_parser


def process_input_parameters(argx:list):
    args = process_args().parse_args(argx)
    SattoLog.print_text(F"\nargs = {args}", BROWN)

    if args.debug:
        SattoLog.print_text('Printing ALL Debug output!!', RED)

    if not osp.isfile(args.monarch):
        msg = F"File path '{args.monarch}' does not exist! Exiting..."
        SattoLog.print_text(msg, RED)
        raise Exception(msg)
    SattoLog.print_text(F"\nMonarch file = {args.monarch}", CYAN)

    mode = TEST
    domain = BOTH
    gnc_file = None
    if 'filename' in args:
        if not osp.isfile(args.filename):
            msg = F"File path '{args.filename}' does not exist. Exiting..."
            SattoLog.print_text(msg, RED)
            raise Exception(msg)
        gnc_file = args.filename
        SattoLog.print_text(F"\nGnucash file = {gnc_file}", CYAN)
        mode = SEND
        domain = args.type
        SattoLog.print_text(F"Inserting '{domain}' transaction types to Gnucash.", BROWN)

    return args.monarch, args.json, args.debug, mode, gnc_file, domain


def mon_copy_rep_main(args:list) -> list:
    mon_file, save_json, debug, mode, gnc_file, domain = process_input_parameters(args)

    mcr_now = dt.now().strftime(DATE_STR_FORMAT)
    SattoLog.print_text(F"mon_copy_rep_main(): Runtime = {mcr_now}", BLUE)

    try:
        # parse an external Monarch COPIED report file
        parser = ParseMonarchCopyReport(mon_file, debug)

        parser.parse_copy_info()
        parser.add_balance_to_trade()

        parser.set_filename(mon_file)

        if mode == SEND:
            gnc_session = GnucashSession(mode, gnc_file, debug, domain)
            parser.insert_txs_to_gnucash_file(gnc_session)

        msg = parser.get_log()

        if save_json:
            # pluck basename from mon_file to use for the saved json file
            _, fname = osp.split(mon_file)
            json_path = JSON_FOLDER
            basename, ext = osp.splitext(fname)

            out_file = save_to_json(json_path + '/' + basename, mcr_now,
                                    parser.get_monarch_record().to_json(), p_color=MAGENTA)
            msg.append(F"\nmon_copy_rep_main() created JSON file:\n{out_file}")

    except Exception as mcre:
        mcre_msg = F"mon_copy_rep_main() EXCEPTION: {repr(mcre)}!!"
        tb = exc_info()[2]
        SattoLog.print_warning(mcre_msg, tb)
        msg = [mcre_msg]

    SattoLog.print_text('\n >>> PROGRAM ENDED.', GREEN)
    return msg


if __name__ == '__main__':
    mon_copy_rep_main(argv[1:])
