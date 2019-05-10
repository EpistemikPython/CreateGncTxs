#
# Configuration.py -- static defines to help parse a Monarch text file
#                     and write the transactions to a gnucash file
#
# Copyright (c) 2018,2019 Mark Sattolo <epistemik@gmail.com>
#
# @author Mark Sattolo <epistemik@gmail.com>
# @version Python 3.6
# @created 2018
# @updated 2019-05-10

import inspect

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
        text = '================================================================================================================='
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


CLIENT_TX = "CLIENT TRANSACTIONS"
PLAN_TYPE = "Plan Type:"
OWNER     = "Owner"
AUTO_SYS  = "Automatic/Systematic"

# Plan types
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

# owner and list of transactions for each plan type
Tx_Collection = {
    OWNER   : "" ,
    PL_OPEN : [] ,
    PL_TFSA : [] ,
    PL_RRSP : []
}

# information for each Monarch transaction
Monarch_Tx = {
    FUND_CMPY  : "" ,
    FUND_CODE  : "" ,
    TRADE_DATE : "" ,
    DESC       : "" ,
    GROSS      : "" ,
    NET        : "" ,
    UNITS      : "" ,
    PRICE      : "" ,
    UNIT_BAL   : "" ,
    ACCT       : "" ,
    NOTES      : ""
}

# information for each Gnucash transaction
Gnucash_Tx = {
    FUND_CMPY  : ""   ,
    FUND_CODE  : ""   ,
    TRADE_DAY  : 0    ,
    TRADE_MTH  : 0    ,
    TRADE_YR   : 0    ,
    DESC       : ""   ,
    SWITCH     : False ,
    GROSS      : 0    ,
    NET        : 0    ,
    UNITS      : 0    ,
    PRICE      : 0.0  ,
    UNIT_BAL   : 0    ,
    ACCT       : None ,
    NOTES      : ""
}

REVENUE  = "Revenue"
ASSET    = "Asset"
TRUST    = "TRUST"
MON_MARK = "Mark H. Sattolo"
MON_LULU = "Louise Robb"
GNU_MARK = "Mark"
GNU_LULU = "Lulu"

FEE    = "Fee Redemption"
DIST   = "Dist"
IN     = "In"
OUT    = "Out"
SWITCH = "Switch"
SW_IN  = SWITCH + "-" + IN
SW_OUT = SWITCH + "-" + OUT
INTRF  = "Internal Transfer"
INTRF_IN  = INTRF + "-" + IN
INTRF_OUT = INTRF + "-" + OUT

# find the proper path to the account in the gnucash file
ACCT_PATHS = {
    REVENUE  : ["REV_Invest", DIST] ,  # + planType [+ Owner]
    ASSET    : ["FAMILY", "INVEST"] ,  # + planType [+ Owner]
    MON_MARK : GNU_MARK ,
    MON_LULU : GNU_LULU ,
    TRUST    : [TRUST, "Trust Assets", "Monarch ITF", COMPANY_NAME[CIG]]
}

# parsing states
STATE_SEARCH = 0x0001
FIND_START   = 0x0004
FIND_OWNER   = 0x0008
FIND_PLAN    = 0x000c
FIND_FUND    = 0x0010
FIND_PRICE   = 0x0014
FIND_COMPANY = 0x0018
FIND_NEXT_TX = 0x0020
FILL_CURR_TX = 0x0030

# file paths
GNC_FOLDER = "/home/marksa/dev/git/Python/Gnucash/gncFiles/"
READER_GNC = GNC_FOLDER + 'reader.gnc'
RUNNER_GNC = GNC_FOLDER + 'runner.gnc'
TEST1_GNC  = GNC_FOLDER + 'test1.gnc'
TEST2_GNC  = GNC_FOLDER + 'test2.gnc'
TEST3_GNC  = GNC_FOLDER + 'test3.gnc'
TEST4_GNC  = GNC_FOLDER + 'test4.gnc'

EXAMPLE_COLLECTION = {
    OWNER: "OWNER_MARK",
    PL_OPEN: [
        {"Trade Date": "10/26/2018", "Gross": "$34.53", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$8.9732", "Unit Balance": "694.4350", "Units": "3.8480", "Net": "$34.53",
         "Fund Code": "CIG 11461"},
        {"Trade Date": "11/23/2018", "Gross": "$34.73", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$8.9957", "Unit Balance": "698.2960", "Units": "3.8610", "Net": "$34.73",
         "Fund Code": "CIG 11461"},
        {"Trade Date": "10/26/2018", "Gross": "$5.30", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$8.9732", "Unit Balance": "106.6770", "Units": "0.5910", "Net": "$5.30",
         "Fund Code": "CIG 11111"},
        {"Trade Date": "11/23/2018", "Gross": "$5.33", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$8.9957", "Unit Balance": "107.2700", "Units": "0.5930", "Net": "$5.33",
         "Fund Code": "CIG 11111"}
    ],
    PL_TFSA: [
        {"Trade Date": "10/30/2018", "Gross": "$4.93", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$8.4422", "Unit Balance": "308.6739", "Units": "0.5840", "Net": "$4.93",
         "Fund Code": "TML 674"},
        {"Trade Date": "11/29/2018", "Gross": "$4.94", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$8.5672", "Unit Balance": "309.2505", "Units": "0.5766", "Net": "$4.94",
         "Fund Code": "TML 674"},
        {"Trade Date": "10/30/2018", "Gross": "$7.87", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$8.4422", "Unit Balance": "492.7939", "Units": "0.9322", "Net": "$7.87",
         "Fund Code": "TML 704"},
        {"Trade Date": "11/29/2018", "Gross": "$7.88", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$8.5672", "Unit Balance": "493.7137", "Units": "0.9198", "Net": "$7.88",
         "Fund Code": "TML 704"}
    ],
    PL_RRSP: [
        {"Trade Date": "10/19/2018", "Gross": "$26.28", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$4.2733", "Unit Balance": "1910.3030", "Units": "6.1490", "Net": "$26.28",
         "Fund Code": "MFC 856"},
        {"Trade Date": "11/23/2018", "Gross": "$33.43", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$4.1890", "Unit Balance": "1918.2830", "Units": "7.9800", "Net": "$33.43",
         "Fund Code": "MFC 856"},
        {"Trade Date": "10/19/2018", "Gross": "$20.49", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$10.1337", "Unit Balance": "1386.5420", "Units": "2.0220", "Net": "$20.49",
         "Fund Code": "MFC 6129"},
        {"Trade Date": "11/23/2018", "Gross": "$22.88", "Description": "Reinvested:Distribution/Interest:",
         "Price": "$10.1511", "Unit Balance": "1388.7960", "Units": "2.2540", "Net": "$22.88",
         "Fund Code": "MFC 6129"}
    ]
}
