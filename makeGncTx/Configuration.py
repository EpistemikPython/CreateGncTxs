##############################################################################################################################
# coding=utf-8
#
# Configuration.py -- constants and utility functions used to parse an initial Monarch pdf file,
#                     extract the information and create transactions and/or prices to write to a Gnucash file
#
# Copyright (c) 2019 Mark Sattolo <epistemik@gmail.com>
#
# @author Mark Sattolo <epistemik@gmail.com>
# @version Python 3.6
# @created 2018
# @updated 2019-05-25

import inspect
from datetime import datetime as dt

DATE_STR_FORMAT = "$%Y-%m-%d:%H-%M-%S"
dtnow = dt.now()
strnow = dtnow.strftime(DATE_STR_FORMAT)

# constant strings
TEST = 'test'
PROD = 'PROD'

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


def print_info(text, color='', inspector=True, newline=True):
    """
    Print information with choices of color, inspection info, newline
    """
    inspect_line = ''
    if text is None:
        text = '==============================================================================================================='
        inspector = False
    if inspector:
        calling_frame = inspect.currentframe().f_back
        calling_file  = inspect.getfile(calling_frame).split('/')[-1]
        calling_line  = str(inspect.getlineno(calling_frame))
        inspect_line  = '[' + calling_file + '@' + calling_line + ']: '
    print(inspect_line + color + str(text) + COLOR_OFF, end=('\n' if newline else ''))


def print_error(text, newline=True):
    """
    Print Error information in RED with inspection info
    """
    calling_frame = inspect.currentframe().f_back
    parent_frame = calling_frame.f_back
    calling_file = inspect.getfile(calling_frame).split('/')[-1]
    calling_line = str(inspect.getlineno(calling_frame))
    parent_line = str(inspect.getlineno(parent_frame))
    inspect_line = '[' + calling_file + '@' + calling_line + '/' + parent_line + ']: '
    print(inspect_line + RED + str(text) + COLOR_OFF, end=('\n' if newline else ''))


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
        print_info("account = " + acct_name)
        descendants = acct.get_descendants()
        if len(descendants) == 0:
            print_info("{} has NO Descendants!".format(acct_name))
        else:
            print_info("Descendants of {}:".format(acct_name))
            # for subAcct in descendants:
            # print_info("{}".format(subAcct.GetName()))


class InvestmentRecord:
    def __init__(self, own=None, dte=None, fn=None):
        print_info("InvestmentRecord()\nRuntime = {}\n".format(strnow), MAGENTA)
        if own is not None:
            assert isinstance(own, str), 'Must be a valid string!'
        self.owner = own
        self.date = dte if dte is not None and isinstance(dte, dt) else dtnow
        if fn is not None:
            assert isinstance(fn, str), 'Must be a valid string!'
        self.filename = fn
        self.plans = {
            PL_OPEN : [],
            PL_TFSA : [],
            PL_RRSP : []
        }

    def set_owner(self, own):
        self.owner = str(own)

    def get_owner(self):
        return UNKNOWN if self.owner is None or self.owner == '' else self.owner

    def set_date(self, dte):
        if isinstance(dte, dt):
            self.date = dte
        else:
            print_error("dte is type: {}".format(type(dte)))

    def get_date(self):
        return self.date

    def get_date_str(self):
        return self.date.strftime(DATE_STR_FORMAT)

    def set_filename(self, fn):
        self.filename = str(fn)

    def get_filename(self):
        return UNKNOWN if self.filename is None or self.filename == '' else self.filename

    def get_size(self):
        return len(self.plans[PL_OPEN]) + len(self.plans[PL_TFSA]) + len(self.plans[PL_RRSP])

    def get_size_str(self):
        return "{} = {}:{} + {}:{} + {}:{}".format(str(self.get_size()), PL_OPEN, len(self.plans[PL_OPEN]),
                                                   PL_TFSA, len(self.plans[PL_TFSA]), PL_RRSP, len(self.plans[PL_RRSP]))

    def add_tx(self, plan, obj):
        if isinstance(plan, str) and plan in self.plans.keys():
            if obj is not None:
                self.plans[plan].append(obj)

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


GNC       = 'Gnucash'
MON       = 'Monarch'
CLIENT_TX = "CLIENT TRANSACTIONS"
PLAN_TYPE = "Plan Type:"
OWNER     = "Owner"
AUTO_SYS  = "Automatic/Systematic"
DOLLARS   = '$'
CENTS     = '\u00A2'
UNKNOWN   = "UNKNOWN"

# Plan types
PLAN_DATA = "Plan Data"
PL_OPEN   = "OPEN"
PL_TFSA   = "TFSA"
PL_RRSP   = "RRSP"

# Tx categories
FUND       = "Fund"
FUND_CODE  = FUND + " Code"
FUND_CMPY  = FUND + " Company"
TRADE_DATE = "Trade Date"
TRADE_DAY  = "Trade Day"
TRADE_MTH  = "Trade Month"
TRADE_YR   = "Trade Year"
DESC       = "Description"
SWITCH     = "Switch"
GROSS      = "Gross"
NET        = "Net"
UNITS      = "Units"
PRICE      = "Price"
UNIT_BAL   = "Unit Balance"
ACCT       = "Account"  # in Gnucash
NOTES      = "Notes"

# Fund companies
ATL = "ATL"
CIG = "CIG"
DYN = "DYN"
MFC = "MFC"
MMF = "MMF"
TML = "TML"

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
    "CIBC"      : ATL ,
    "CI"        : CIG ,
    "Dynamic"   : DYN ,
    "Mackenzie" : MFC ,
    "Manulife"  : MMF ,
    "Franklin"  : TML ,
    "Templeton" : TML
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
    TML_674, TML_704, TML_180, TML_184, TML_202, TML_203, TML_223, TML_518, TML_519, TML_598, TML_694, TML_707, TML_1017, TML_1018,
    MFC_756, MFC_856, MFC_6129, MFC_6130, MFC_6138, MFC_302, MFC_2238, MFC_3232, MFC_3769, MFC_3689, MFC_1960,
    DYN_029, DYN_729, DYN_1562, DYN_1560,
    MMF_44424, MMF_4524, MMF_3517, MMF_13417
]

TRUST_AST_ACCT = CIG_18140
TRUST_REV_ACCT = "Trust Base"

REVENUE  = "Revenue"
ASSET    = "Asset"
TRUST    = "TRUST"
MON_MARK = "Mark H. Sattolo"
MON_LULU = "Louise Robb"
GNC_MARK = "Mark"
GNC_LULU = "Lulu"

FEE    = "Fee Redemption"
DIST   = "Dist"
IN     = "In"
OUT    = "Out"
SW_IN  = SWITCH + "-" + IN
SW_OUT = SWITCH + "-" + OUT
INTRF  = "Internal Transfer"
INTRF_IN  = INTRF + "-" + IN
INTRF_OUT = INTRF + "-" + OUT

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

# file paths
GNC_FOLDER = "/home/marksa/dev/git/Python/Gnucash/gncFiles/"
READER_GNC = GNC_FOLDER + 'reader.gnc'
RUNNER_GNC = GNC_FOLDER + 'runner.gnc'
TEST1_GNC  = GNC_FOLDER + 'test1.gnc'
TEST2_GNC  = GNC_FOLDER + 'test2.gnc'
TEST3_GNC  = GNC_FOLDER + 'test3.gnc'
TEST4_GNC  = GNC_FOLDER + 'test4.gnc'
