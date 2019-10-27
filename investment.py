##############################################################################################################################
# coding=utf-8
#
# investment.py -- classes, constants, variables & functions used with my investment scripts
#
# Copyright (c) 2019 Mark Sattolo <epistemik@gmail.com>
#
__author__ = 'Mark Sattolo'
__author_email__ = 'epistemik@gmail.com'
__python_version__ = 3.6
__created__ = '2018'
__updated__ = '2019-10-27'

from sys import path
import os.path as osp
path.append("/home/marksa/dev/git/Python/Utilities/")
from python_utilities import *

# constant strings
AU:str    = 'Gold'
AG:str    = 'Silver'
CASH:str  = 'Cash'
BANK:str  = 'Bank'
RWRDS:str = 'Rewards'
RESP:str  = 'RESP'
HOUSE:str = 'House'
TOTAL:str = 'Total'
ASTS:str  = 'FAMILY'
LIAB:str  = 'LIABS'
CHAL:str  = 'XCHALET'
HOLD:str  = 'HOLD'
TODAY:str = 'Today'
QTR:str   = 'Quarter'
YR:str    = 'Year'
MTH:str   = 'Month'
REV:str   = 'Revenue'
INV:str   = 'Invest'
OTH:str   = 'Other'
EMPL:str  = 'Employment'
BAL:str   = 'Balance'
CONT:str  = 'Contingent'
NEC:str   = 'Necessary'
DEDNS:str = 'Emp_Dedns'
TEST:str  = 'test'
SEND:str  = 'SEND'
PROD:str  = SEND
BUY:str   = 'Buy'
SELL:str  = 'Sell'

GNC:str       = 'Gnucash'
MON:str       = 'Monarch'
TXS:str       = "TRANSACTIONS"
CLIENT_TX:str = "CLIENT " + TXS
PLAN_TYPE:str = "Plan Type:"
PLAN_DATA:str = "Plan Data"
OPEN:str      = "OPEN"
TFSA:str      = "TFSA"
RRSP:str      = "RRSP"
OWNER:str     = "Owner"
JOINT:str     = "Joint"
EQUITY:str    = "EQUITY"
TRUST:str     = "TRUST"
AUTO_SYS:str  = "Automatic/Systematic"
UNKNOWN:str   = "UNKNOWN"
FIN_SERV:str  = "FinServices"
DOLLARS:str   = '$'
CENTS:str     = '\u00A2'

REVENUE:str   = "Revenue"
ASSET:str     = "Asset"
MON_SATT:str  = "Sattolo"
MON_MARK:str  = "Mark H. " + MON_SATT
MON_ROBB:str  = "Robb"
MON_LULU:str  = "Louise " + MON_ROBB
GNC_MARK:str  = "Mark"
GNC_LULU:str  = "Lulu"

# Tx categories
FUND:str        = "Fund"
CMPY:str        = "Company"
FUND_CODE:str   = FUND + " Code"
FUND_CMPY:str   = FUND + " " + CMPY
DATE:str        = "Date"
TRADE:str       = "Trade"
TRADE_DATE:str  = TRADE + " " + DATE
TRADE_DAY:str   = TRADE + " Day"
TRADE_MTH:str   = TRADE + " Month"
TRADE_YR:str    = TRADE + " Year"
TYPE:str        = "Type"
DESC:str        = "Description"
SWITCH:str      = "Switch"
GROSS:str       = "Gross"
NET:str         = "Net"
UNITS:str       = "Units"
PRICE:str       = "Price"
BOTH:str        = "Both"
UNIT_BAL:str    = "Unit Balance"
ACCT:str        = "Account"  # in Gnucash
NOTES:str       = "Notes"
LOAD:str        = "Load"
FEE:str         = "Fee"
RDMPN:str       = "Redemption"
FEE_RD:str      = FEE + " " + RDMPN
PURCH:str       = "Purchase"
DIST:str        = "Dist"
SW_IN:str       = SWITCH + "-in"
SW_OUT:str      = SWITCH + "-out"
INTRF:str       = "Internal Transfer"
INTRF_IN:str    = INTRF + "-In"
INTRF_OUT:str   = INTRF + "-Out"
REINV:str       = "Reinvested"
INTRCL:str      = "Inter-Class"

# Fund companies
ATL:str = "ATL"
CIG:str = "CIG"
DYN:str = "DYN"
MFC:str = "MFC"
MMF:str = "MMF"
TML:str = "TML"

TX_TYPES = {
    FEE      : FEE_RD ,
    SW_IN    : SW_IN  ,
    SW_OUT   : SW_OUT ,
    REINV    : REINV + " Distribution" ,
    AUTO_SYS : AUTO_SYS + " Withdrawal Plan" ,
    RDMPN    : RDMPN ,
    PURCH    : PURCH
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
JOINT_PLAN_ID:str = '78512'
LULU_TRUST_ID:str = '78514'
LULU_RRSP_ID:str  = '278825'
LULU_TFSA_ID:str  = '278826'
MARK_RRSP_ID:str  = '278827'
MARK_TFSA_ID:str  = '300787'
PLAN_IDS = {
    JOINT_PLAN_ID : {PLAN_TYPE: OPEN, OWNER: MON_MARK} ,
    LULU_TRUST_ID : {PLAN_TYPE: OPEN, OWNER: MON_LULU} ,
    LULU_RRSP_ID  : {PLAN_TYPE: RRSP, OWNER: MON_LULU} ,
    LULU_TFSA_ID  : {PLAN_TYPE: TFSA, OWNER: MON_LULU} ,
    MARK_RRSP_ID  : {PLAN_TYPE: RRSP, OWNER: MON_MARK} ,
    MARK_TFSA_ID  : {PLAN_TYPE: TFSA, OWNER: MON_MARK}
}

MONEY_MKT_FUNDS = [MFC_298, MFC_4378, TML_204, TML_703]

TRUST_AST_ACCT = CIG_18140
TRUST_EQY_ACCT = "Trust Base"

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


# TODO: TxRecord in standard format for both Monarch and Gnucash
class TxRecord:
    """
    All the required information for an individual transaction
    """
    def __init__(self, p_dt:dt=None, p_dt_str:str='', p_sw:bool=False, p_fcmpy:str='', p_fcode:str='', p_fname:str='',
                 p_gr:float=0.0, p_gr_str:str='', p_pr:float=0.0, p_pr_str:str='', p_un:float=0.0, p_un_str:str='',
                 p_logger:SattoLog=None):
        self.set_date(p_dt)
        self.date_str = p_dt_str
        self.switch = p_sw
        self.company = p_fcmpy
        self.fd_name = p_fname
        self.fd_code = p_fcode
        self.gross = p_gr
        self.gross_str = p_gr_str
        self.price = p_pr
        self.price_str = p_pr_str
        self.units = p_un
        self.units_str = p_un_str
        self._logger = p_logger

    def __getitem__(self, item):
        if item == DATE:
            return self.date
        if item == FUND:
            return self.fd_name
        if item == GROSS:
            return self.gross
        if item in (FUND_CMPY, COMPANY_NAME):
            return self.company
        if item == FUND_CODE:
            return self.fd_code
        if item == PRICE:
            return self.price
        if item == UNITS:
            return self.units
        if item == SWITCH:
            return self.switch
        else:
            self._log(F"UNKNOWN item: {item}")
            return None

    def _log(self, p_msg:str, p_color:str=''):
        if self._logger:
            self._logger.print_info(p_msg, p_color, p_info=inspect.currentframe().f_back)

    def _err(self, p_msg: str, err_info:object):
        if self._logger:
            self._logger.print_info(p_msg, BR_RED, p_info=err_info)

    def set_fund_cmpy(self, p_co:str):
        self.company = p_co

    def set_fund_code(self, p_code:str):
        self.fd_code = p_code

    def set_fund_name(self, p_name:str):
        self.fd_name = p_name

    def set_type(self, p_type):
        if p_type in (TRADE,PRICE):
            self.type = p_type
        else:
            self._log(F"BAD type: {p_type}")

    def set_date(self, p_date:dt) -> dt:
        old_date = self.date
        if p_date is not None and isinstance(p_date, dt):
            self.date = p_date
        else:
            self._log(F"BAD date: {p_date}")
        return old_date

# END class TxRecord


# TODO: data date and run date?
class InvestmentRecord:
    """
    All transactions from an investment report
    """
    def __init__(self, p_owner:str='', p_date:dt=None, p_fname:str='', logger:SattoLog=None):
        self._logger = logger
        if p_owner:
            assert (p_owner == MON_MARK or p_owner == MON_LULU), 'MUST be a valid Owner!'
        self._owner = p_owner
        self._date = p_date if p_date is not None and isinstance(p_date, dt) else dtnow
        if p_fname:
            assert (isinstance(p_fname, str) and osp.isfile(p_fname)), 'MUST be a valid filename!'
        self._filename = p_fname

        self._plans = {
            # lists of TxRecords
            OPEN : {TRADE:[], PRICE:[]} ,
            TFSA : {TRADE:[], PRICE:[]} ,
            RRSP : {TRADE:[], PRICE:[]}
        }
        self._log("\n\tInvestmentRecord(): Runtime = {}".format(strnow))

    def __getitem__(self, item:str):
        if item in (OPEN,TFSA,RRSP):
            return self._plans[item]
        self._err(F"BAD plan: {str(item)}", inspect.currentframe().f_back)
        return None

    def _log(self, p_msg:str, p_color:str=''):
        if self._logger:
            self._logger.print_info(p_msg, p_color, p_info=inspect.currentframe().f_back)

    def _err(self, p_msg: str, err_info:object):
        if self._logger:
            self._logger.print_info(p_msg, BR_RED, p_info=err_info)

    def set_owner(self, own):
        self._owner = str(own)

    def get_owner(self) -> str:
        return UNKNOWN if self._owner is None or self._owner == '' else self._owner

    def set_date(self, p_date):
        if isinstance(p_date, dt):
            self._date = p_date
        else:
            self._err(F"Submitted date of improper type: {type(p_date)}", inspect.currentframe().f_back)

    def get_plans(self) -> dict:
        return self._plans

    def get_plan(self, p_plan:str) -> dict:
        if p_plan in (OPEN,TFSA,RRSP):
            return self._plans[p_plan]
        self._err(F"UNKNOWN plan: {p_plan}", inspect.currentframe().f_back)
        return {}

    def get_trades(self, p_plan) -> list:
        plan = self.get_plan(p_plan)
        return plan[TRADE] if plan else []

    def get_prices(self, p_plan) -> list:
        plan = self.get_plan(p_plan)
        return plan[PRICE] if plan else []

    def get_date(self) -> dt:
        return self._date

    def get_date_str(self) -> str:
        return self._date.strftime(DATE_STR_FORMAT)

    def set_filename(self, fn):
        self._filename = str(fn)

    def get_filename(self) -> str:
        return UNKNOWN if self._filename is None or self._filename == '' else self._filename

    def get_size(self, plan_spec:str='', type_spec:str='') -> int:
        if not plan_spec:
            if type_spec in (PRICE, TRADE):
                return len(self._plans[OPEN][type_spec]) + len(self._plans[TFSA][type_spec]) + len(self._plans[RRSP][type_spec])
            return self.get_size(OPEN) + self.get_size(TFSA) + self.get_size(RRSP)
        if not type_spec:
            if plan_spec in (OPEN, RRSP, TFSA):
                return len(self._plans[plan_spec][PRICE]) + len(self._plans[plan_spec][TRADE])
        return len(self._plans[plan_spec][type_spec])

    def get_size_str(self, plan_spec:str='', type_spec:str='') -> str:
        if plan_spec in (OPEN, RRSP, TFSA):
            if type_spec in (PRICE, TRADE):
                return F"{type_spec}[{self.get_size(plan_spec,type_spec)}]"
            return F"P{self.get_size(plan_spec,PRICE)}/T{self.get_size(plan_spec,TRADE)}"
        # return information for all plans and types
        return F"{self.get_size()} = {OPEN}:{self.get_size_str(OPEN)} + "\
               + F"{TFSA}:{self.get_size_str(TFSA)} + {RRSP}:{self.get_size_str(RRSP)}"

    def add_tx(self, plan, tx_type, obj):
        if isinstance(plan, str) and plan in self._plans.keys():
            if obj and tx_type in (TRADE, PRICE):
                self._plans[plan][tx_type].append(obj)

    def to_json(self, plan_spec:str='', type_spec:str=''):
        return {
            "__class__"    : self.__class__.__name__ ,
            "__module__"   : self.__module__         ,
            OWNER          : self.get_owner()        ,
            "Source File"  : self.get_filename()     ,
            "Date"         : self.get_date_str()     ,
            "Size"         : self.get_size_str(plan_spec, type_spec) ,
            PLAN_DATA      : self._plans
        }

# END class InvestmentRecord
