##############################################################################################################################
# coding=utf-8
#
# Configuration.py -- constants and utility functions used to parse an initial Monarch pdf file,
#                     extract the information and create transactions and/or prices to write to a Gnucash file
#
# Copyright (c) 2019 Mark Sattolo <epistemik@gmail.com>
#
__author__ = 'Mark Sattolo'
__author_email__ = 'epistemik@gmail.com'
__python_version__ = 3.6
__created__ = '2018'
__updated__ = '2019-07-27'

import inspect
import os.path as osp
from datetime import datetime as dt

DATE_STR_FORMAT = "\u0023%Y-%m-%d\u0025\u0025%H-%M-%S"
dtnow = dt.now()
strnow = dtnow.strftime(DATE_STR_FORMAT)

# constant strings
TEST: str = 'test'
PROD: str = 'PROD'

GNC: str       = 'Gnucash'
MON: str       = 'Monarch'
TXS: str       = "TRANSACTIONS"
CLIENT_TX:str  = "CLIENT " + TXS
PLAN_TYPE: str = "Plan Type:"
OWNER: str     = "Owner"
AUTO_SYS: str  = "Automatic/Systematic"
DOLLARS: str   = '$'
CENTS: str     = '\u00A2'
UNKNOWN: str   = "UNKNOWN"

REVENUE: str  = "Revenue"
ASSET: str    = "Asset"
TRUST: str    = "TRUST"
MON_SATT: str = "Sattolo"
MON_MARK: str = "Mark H. " + MON_SATT
MON_ROBB: str = "Robb"
MON_LULU: str = "Louise " + MON_ROBB
GNC_MARK: str = "Mark"
GNC_LULU: str = "Lulu"

# Plan types
PLAN_DATA: str = "Plan Data"
PL_OPEN: str   = "OPEN"
PL_TFSA: str   = "TFSA"
PL_RRSP: str   = "RRSP"

# Tx categories
FUND: str       = "Fund"
FUND_CODE: str  = FUND + " Code"
FUND_CMPY: str  = FUND + " Company"
DATE: str       = "Date"
TRADE: str      = "Trade"
TRADE_DATE: str = TRADE + " " + DATE
TRADE_DAY: str  = TRADE + " Day"
TRADE_MTH: str  = TRADE + " Month"
TRADE_YR: str   = TRADE + " Year"
DESC: str       = "Description"
SWITCH: str     = "Switch"
GROSS: str      = "Gross"
NET: str        = "Net"
UNITS: str      = "Units"
PRICE: str      = "Price"
BOTH: str       = 'Both'
UNIT_BAL: str   = "Unit Balance"
ACCT: str       = "Account"  # in Gnucash
NOTES: str      = "Notes"
LOAD: str       = "Load"
FEE: str        = 'Fee'
FEE_RD: str     = FEE + " Redemption"
DIST: str       = "Dist"
SW_IN: str      = SWITCH + "-in"
SW_OUT: str     = SWITCH + "-out"
INTRF: str      = "Internal Transfer"
INTRF_IN: str   = INTRF + "-In"
INTRF_OUT: str  = INTRF + "-Out"
REINV: str      = 'Reinvested'
INTRCL:str      = 'Inter-Class'

COLOR_FLAG = '\x1b['
BLACK   = COLOR_FLAG + '30m'
RED     = COLOR_FLAG + '31m'
GREEN   = COLOR_FLAG + '32m'
YELLOW  = COLOR_FLAG + '33m'
BLUE    = COLOR_FLAG + '34m'
MAGENTA = COLOR_FLAG + '35m'
CYAN    = COLOR_FLAG + '36m'
WHITE   = COLOR_FLAG + '37m'
COLOR_OFF = COLOR_FLAG + '0m'


class Gnulog:
    def __init__(self, p_debug):
        self.debug = p_debug
        self.log_text = []

    def clear_log(self):
        self.log_text = []

    def get_log(self):
        return self.log_text

    def print_info(self, info, color='', inspector=True, newline=True):
        """
        Print information with choices of color, inspection info, newline
        """
        if self.debug:
            inspect_line = ''
            if info is None:
                info = '==============================================================================================================='
                inspector = False
            text = str(info)
            if inspector:
                calling_frame = inspect.currentframe().f_back
                calling_file  = inspect.getfile(calling_frame).split('/')[-1]
                calling_line  = str(inspect.getlineno(calling_frame))
                inspect_line  = '[' + calling_file + '@' + calling_line + ']: '
            print(inspect_line + color + text + COLOR_OFF, end=('\n' if newline else ''))
            self.log_text.append(text)

    def print_error(self, text, newline=True):
        """
        Print Error information in RED with inspection info
        """
        if self.debug:
            calling_frame = inspect.currentframe().f_back
            parent_frame = calling_frame.f_back
            calling_file = inspect.getfile(calling_frame).split('/')[-1]
            calling_line = str(inspect.getlineno(calling_frame))
            parent_line = str(inspect.getlineno(parent_frame))
            inspect_line = '[' + calling_file + '@' + calling_line + '/' + parent_line + ']: '
            print(inspect_line + RED + str(text) + COLOR_OFF, end=('\n' if newline else ''))

    @staticmethod
    def print_text(info, color='', inspector=True, newline=True):
        """
        Print information with choices of color, inspection info, newline
        """
        inspect_line = ''
        if info is None:
            info = '==============================================================================================================='
            inspector = False
        text = str(info)
        if inspector:
            calling_frame = inspect.currentframe().f_back
            calling_file  = inspect.getfile(calling_frame).split('/')[-1]
            calling_line  = str(inspect.getlineno(calling_frame))
            inspect_line  = '[' + calling_file + '@' + calling_line + ']: '
        print(inspect_line + color + text + COLOR_OFF, end=('\n' if newline else ''))


class GncUtilities:
    def account_from_path(self, top_account, account_path, original_path=None):
        """
        get a Gnucash account from the given path
        :param   top_account: String: start
        :param  account_path: String: path
        :param original_path: String: recursive
        :return: Gnucash account
        """
        if original_path is None:
            original_path = account_path
        account, account_path = account_path[0], account_path[1:]

        account = top_account.lookup_by_name(account)
        if account is None:
            raise Exception("path " + str(original_path) + " could NOT be found")
        if len(account_path) > 0:
            return self.account_from_path(account, account_path, original_path)
        else:
            return account

    def show_account(self, root, path):
        """
        display an account and its descendants
        :param root: Gnucash root
        :param path: to the account
        :return: nil
        """
        acct = self.account_from_path(root, path)
        acct_name = acct.GetName()
        Gnulog.print_text("account = " + acct_name)
        descendants = acct.get_descendants()
        if len(descendants) == 0:
            Gnulog.print_text("{} has NO Descendants!".format(acct_name))
        else:
            Gnulog.print_text("Descendants of {}:".format(acct_name))
            # for subAcct in descendants:
            # print_info("{}".format(subAcct.GetName()))

    # END class GncUtilities


# TODO: TxRecord in standard format for both Monarch and Gnucash
class TxRecord:
    """
    All the required information for an individual transaction
    """
    def __init__(self, tx_dte, tx_cmpy, tx_code, tx_name, tx_gross, tx_price, tx_units):
        self.date = tx_dte
        self.company = tx_cmpy
        self.fd_name = tx_name
        self.fd_code = tx_code
        self.gross = tx_gross
        self.price = tx_price
        self.units = tx_units

# END class TxRecord


# TODO: data date and run date
class InvestmentRecord:
    """
    All transactions from an investment report
    """
    def __init__(self, own=None, dte=None, fn=None):
        Gnulog.print_text("InvestmentRecord(): Runtime = {}\n".format(strnow), MAGENTA)
        if own is not None:
            assert (own == MON_MARK or own == MON_LULU), 'Must be a valid Owner!'
        self.owner: str = own
        self.date = dte if dte is not None and isinstance(dte, dt) else dtnow
        if fn is not None:
            assert (isinstance(fn, str) and osp.isfile(fn)), 'Must be a valid filename!'
        self.filename: str = fn
        self.plans = {
            # lists of TxRecords
            PL_OPEN : { TRADE:[], PRICE:[] } ,
            PL_TFSA : { TRADE:[], PRICE:[] } ,
            PL_RRSP : { TRADE:[], PRICE:[] }
        }

    def set_owner(self, own):
        self.owner = str(own)

    def get_owner(self):
        return UNKNOWN if self.owner is None or self.owner == '' else self.owner

    def set_date(self, dte):
        if isinstance(dte, dt):
            self.date = dte
        else:
            Gnulog.print_text("dte is type: {}".format(type(dte)), RED)

    def get_plans(self):
        return self.plans

    def get_next(self):
        # keep track of TxRecords and return next
        return self.plans[PL_OPEN][PRICE][0]

    def get_date(self):
        return self.date

    def get_date_str(self):
        return self.date.strftime(DATE_STR_FORMAT)

    def set_filename(self, fn):
        self.filename = str(fn)

    def get_filename(self):
        return UNKNOWN if self.filename is None or self.filename == '' else self.filename

    def get_size(self, p_spec:str = None, q_spec:str = None):
        if p_spec is None:
            return self.get_size(PL_OPEN) + self.get_size(PL_TFSA) + self.get_size(PL_RRSP)
        if q_spec is None:
            if p_spec == PL_OPEN or p_spec == PL_TFSA or p_spec == PL_RRSP:
                return len(self.plans[p_spec][PRICE]) + len(self.plans[p_spec][TRADE])
            if p_spec == PRICE or p_spec == TRADE:
                return len(self.plans[PL_OPEN][p_spec]) + len(self.plans[PL_TFSA][p_spec]) + len(self.plans[PL_RRSP][p_spec])
        return len(self.plans[p_spec][q_spec])

    def get_size_str(self, str_spec:str = None):
        if str_spec is not None:
            return "P{}/T{}".format(self.get_size(str_spec, PRICE), self.get_size(str_spec, TRADE))
        return "{} = {}:{} + {}:{} + {}:{}".format( self.get_size(), PL_OPEN, self.get_size_str(PL_OPEN),
                PL_TFSA, self.get_size_str(PL_TFSA), PL_RRSP, self.get_size_str(PL_RRSP) )

    def add_tx(self, plan, tx_type, obj):
        if isinstance(plan, str) and plan in self.plans.keys():
            if obj is not None:
                self.plans[plan][tx_type].append(obj)

    def to_json(self):
        return {
            "__class__"    : self.__class__.__name__ ,
            "__module__"   : self.__module__         ,
            OWNER          : self.get_owner()        ,
            "Source File"  : self.get_filename()     ,
            "Date"         : self.get_date_str()     ,
            "Size"         : self.get_size_str()     ,
            PLAN_DATA      : self.plans
        }

# END class InvestmentRecord


# Fund companies
ATL: str = "ATL"
CIG: str = "CIG"
DYN: str = "DYN"
MFC: str = "MFC"
MMF: str = "MMF"
TML: str = "TML"

TX_TYPES = {
    FEE      : FEE_RD ,
    SW_IN    : SW_IN  ,
    SW_OUT   : SW_OUT ,
    REINV    : REINV + ' Distribution' ,
    AUTO_SYS : AUTO_SYS + ' Withdrawal Plan'
}

# Company names
COMPANY_NAME = {
    ATL : "CIBC Asset Management",
    CIG : "CI Investments",
    DYN : "Dynamic Funds",
    MFC : "Mackenzie Financial Corp",
    MMF : "Manulife Mutual Funds",
    TML : "Franklin Templeton"
}

# Company name codes
FUND_NAME_CODE = {
    "CIBC"        : ATL ,
    "Renaissance" : ATL ,
    "CI"          : CIG ,
    "Cambridge"   : CIG ,
    "Signature"   : CIG ,
    "Dynamic"     : DYN ,
    "Mackenzie"   : MFC ,
    "Manulife"    : MMF ,
    "Franklin"    : TML ,
    "Templeton"   : TML
}

# Fund codes/names
ATL_O59   = ATL + " 059"   # Renaissance Global Infrastructure Fund Class A
CIG_11111 = CIG + " 11111" # Signature Diversified Yield II Fund A
CIG_11461 = CIG + " 11461" # Signature Diversified Yield II Fund A
CIG_1304  = CIG + " 1304"  # Signature High Income Corporate Class A
CIG_2304  = CIG + " 2304"  # Signature High Income Corporate Class A
CIG_1521  = CIG + " 1521"  # Cambridge Canadian Equity Corporate Class A
CIG_2321  = CIG + " 2321"  # Cambridge Canadian Equity Corporate Class A
CIG_1154  = CIG + " 1154"  # CI Can-Am Small Cap Corporate Class A
CIG_6104  = CIG + " 6104"  # CI Can-Am Small Cap Corporate Class A
CIG_18140 = CIG + " 18140" # Signature Diversified Yield Corporate Class O
TML_180   = TML + " 180"   # Franklin Mutual Global Discovery Fund A
TML_184   = TML + " 184"   # Franklin Mutual Global Discovery Fund A
TML_202   = TML + " 202"   # Franklin Bissett Canadian Equity Fund Series A
TML_518   = TML + " 518"   # Franklin Bissett Canadian Equity Fund Series A
TML_203   = TML + " 203"   # Franklin Bissett Dividend Income Fund A
TML_519   = TML + " 519"   # Franklin Bissett Dividend Income Fund A
TML_223   = TML + " 223"   # Franklin Bissett Small Cap Fund Series A
TML_598   = TML + " 598"   # Franklin Bissett Small Cap Fund Series A
TML_674   = TML + " 674"   # Templeton Global Bond Fund Series A
TML_704   = TML + " 704"   # Templeton Global Bond Fund Series A
TML_694   = TML + " 694"   # Templeton Global Smaller Companies Fund A
TML_707   = TML + " 707"   # Templeton Global Smaller Companies Fund A
TML_1017  = TML + " 1017"  # Franklin Bissett Canadian Dividend Fund A
TML_1018  = TML + " 1018"  # Franklin Bissett Canadian Dividend Fund A
TML_204   = TML + " 204"   # Franklin Bissett Money Market
TML_703   = TML + " 703"   # Franklin Templeton Treasury Bill
MFC_756   = MFC + " 756"   # Mackenzie Corporate Bond Fund Series A
MFC_856   = MFC + " 856"   # Mackenzie Corporate Bond Fund Series A
MFC_6130  = MFC + " 6130"  # Mackenzie Corporate Bond Fund Series PW
MFC_2238  = MFC + " 2238"  # Mackenzie Strategic Income Fund Series A
MFC_3232  = MFC + " 3232"  # Mackenzie Strategic Income Fund Series A
MFC_6138  = MFC + " 6138"  # Mackenzie Strategic Income Fund Series PW
MFC_302   = MFC + " 302"   # Mackenzie Canadian Bond Fund Series A
MFC_3769  = MFC + " 3769"  # Mackenzie Canadian Bond Fund Series SC
MFC_6129  = MFC + " 6129"  # Mackenzie Canadian Bond Fund Series PW
MFC_1960  = MFC + " 1960"  # Mackenzie Strategic Income Class Series T6
MFC_3689  = MFC + " 3689"  # Mackenzie Strategic Income Class Series T6
MFC_298   = MFC + " 298"   # Mackenzie Cash Management A
MFC_4378  = MFC + " 4378"  # Mackenzie Canadian Money Market Fund Series C
DYN_029   = DYN + " 029"   # Dynamic Equity Income Fund Series A
DYN_729   = DYN + " 729"   # Dynamic Equity Income Fund Series A
DYN_1560  = DYN + " 1560"  # Dynamic Strategic Yield Fund Series A
DYN_1562  = DYN + " 1562"  # Dynamic Strategic Yield Fund Series A
MMF_4524  = MMF + " 4524"  # Manulife Yield Opportunities Fund Advisor Series
MMF_44424 = MMF + " 44424" # Manulife Yield Opportunities Fund Advisor Series
MMF_3517  = MMF + " 3517"  # Manulife Conservative Income Fund Advisor Series
MMF_13417 = MMF + " 13417" # Manulife Conservative Income Fund Advisor Series

FUNDS_LIST = [
    CIG_11461, CIG_11111, CIG_18140, CIG_2304, CIG_2321, CIG_6104, CIG_1154, CIG_1304, CIG_1521,
    TML_674, TML_703, TML_704, TML_180, TML_184, TML_202, TML_203, TML_204, TML_223, 
    TML_518, TML_519, TML_598, TML_694, TML_707, TML_1017, TML_1018,
    MFC_756, MFC_856, MFC_6129, MFC_6130, MFC_6138, MFC_302, MFC_2238, 
    MFC_3232, MFC_3769, MFC_3689, MFC_1960, MFC_298, MFC_4378,
    DYN_029, DYN_729, DYN_1562, DYN_1560,
    MMF_44424, MMF_4524, MMF_3517, MMF_13417
]

# Plan IDs
JOINT_PLAN_ID: str = '78512'

MONEY_MKT_FUNDS = [MFC_298, MFC_4378, TML_204, TML_703]

TRUST_AST_ACCT = CIG_18140
TRUST_REV_ACCT = "Trust Base"

# find the proper path to the account in the gnucash file
ACCT_PATHS = {
    REVENUE  : ["REV_Invest", DIST] ,  # + planType [+ Owner]
    ASSET    : ["FAMILY", "INVEST"] ,  # + planType [+ Owner]
    MON_MARK : GNC_MARK ,
    MON_LULU : GNC_LULU ,
    TRUST    : [TRUST, "Trust Assets", "Monarch ITF", COMPANY_NAME[CIG]]
}

# parsing states
STATE_SEARCH = 0x0001
FIND_START   = 0x0010
FIND_OWNER   = 0x0020
FIND_PLAN    = 0x0030
FIND_FUND    = 0x0040
FIND_PRICE   = 0x0050
FIND_DATE    = 0x0060
FIND_COMPANY = 0x0070
FIND_NEXT_TX = 0x0080
FILL_CURR_TX = 0x0090
