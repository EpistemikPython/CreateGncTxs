
# Configuration.py -- static defines to help parse a Monarch text file 
#                     and write transactions to a gnucash file
#
# Copyright (c) 2018, 2019 Mark Sattolo <epistemik@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# @author Mark Sattolo <epistemik@gmail.com>

__created__ = "2018-12-02 07:13"
__updated__ = "2019-01-01 10:59"

CLIENT_TX = "CLIENT TRANSACTIONS"
PLAN_TYPE = "Plan Type:"
OWNER     = "Owner"
AUTO_SYS  = "Automatic/Systematic"

# Plan types
PL_OPEN   = "OPEN"
PL_TFSA   = "TFSA"
PL_RRSP   = "RRSP"

# tx categories
FUND       = "Fund"
FUND_CODE  = FUND + " Code"
FUND_CMPY  = FUND + " Company"
TRADE_DATE = "Trade Date"
DESC       = "Description"
GROSS      = "Gross"
NET        = "Net"
UNITS      = "Units"
PRICE      = "Price"
UNIT_BAL   = "Unit Balance" 
NOTES      = "Notes"

# Fund companies
ATL = "ATL"
CIG = "CIG"
DYN = "DYN"
MFC = "MFC"
MMF = "MMF"
TML = "TML"

CMPY_FULL_NAME = {
    ATL : "CIBC Asset Management",
    CIG : "CI Investments",
    DYN : "Dynamic Funds",
    MFC : "Mackenzie Financial Corp",
    MMF : "Manulife Mutual Funds",
    TML : "Franklin Templeton"
}

# Fund names
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

FundsList = [ 
    CIG_11461, CIG_11111, CIG_18140, CIG_2304, CIG_2321, CIG_6104, CIG_1154, CIG_1304, CIG_1521,
    TML_674, TML_704, TML_180, TML_184, TML_202, TML_203, TML_223, TML_518, TML_519, TML_598, TML_694, TML_707, TML_1017, TML_1018, 
    MFC_756, MFC_856, MFC_6129, MFC_6130, MFC_6138, MFC_302, MFC_2238, MFC_3232, MFC_3769, MFC_3689, MFC_1960, 
    DYN_029, DYN_729, DYN_1562, DYN_1560,
    MMF_44424, MMF_4524, MMF_3517, MMF_13417
]

# owner and list of transactions for each plan type
Monarch_Record = {
    OWNER   : "" ,
    PL_OPEN : [] ,
    PL_TFSA : [] ,
    PL_RRSP : []
}

# information for each transaction
Monarch_Tx = {
    FUND_CMPY  : "" ,
    FUND_CODE  : "" ,
    TRADE_DATE : "" ,
    DESC       : "" ,
    GROSS      : "" ,
    NET        : "" ,
    UNITS      : "" ,
    PRICE      : "" ,
    UNIT_BAL   : "" 
}

REVENUE  = "Revenue"
ASSET    = "Asset"
TRUST    = "TRUST"
MON_MARK = "Mark H. Sattolo"
MON_LULU = "Louise Robb"
GNU_MARK = "Mark"
GNU_LULU = "Lulu"

TRUST_ACCT = CIG_18140

# find the proper path to the account in the gnucash file
ACCT_PATHS = {
    REVENUE  : ["REV", "REV_Invest", "Dist"] ,# + planType [+ Owner]
    ASSET    : ["FAMILY", "INVEST"] ,# + planType [+ Owner]
    MON_MARK : GNU_MARK ,
    MON_LULU : GNU_LULU ,
    TRUST    : ["XTERNAL", TRUST, "Trust Assets", "Monarch ITF", CMPY_FULL_NAME[CIG] ]
}

ACCT     = "Account" # Fund company & code
DIST     = "Dist"
SWITCH   = "Switch"
IN       = "In"
OUT      = "Out"
SW_IN    = SWITCH + "-" + IN
SW_OUT   = SWITCH + "-" + OUT
INTX     = "Internal Transfer"
INTX_IN  = INTX + "-" + IN
INTX_OUT = INTX + "-" + OUT

Switch_Pair = {
    IN  : OUT ,
    OUT : IN  
}

# information for each distribution transaction
Gnucash_Dist = {
    "ID"       : DIST ,
    TRADE_DATE : "" ,
    DESC       : "" ,
    REVENUE    : { ACCT:"", GROSS:"" } ,
    ASSET      : { ACCT:"", GROSS:"", UNITS:"" } 
}

# information for each switch transaction
Gnucash_Switch = {
    "ID"       : SWITCH ,
    FUND_CMPY  : "" ,
    TRADE_DATE : "" ,
    NOTES      : "" ,
    ACCT       : "" , 
    GROSS      : "" ,
    UNITS      : "" 
}
#     IN         : { ACCT:"", VALUE:"", AMOUNT:"", UNIT_BAL:"", PRICE:"" } ,
#     OUT        : { ACCT:"", VALUE:"", AMOUNT:"", UNIT_BAL:"", PRICE:"" } 
# }

# list of gnucash switches for each plan type and fund company
Gnucash_Record = {
    OWNER   : "" ,
    PL_OPEN : [] , # all CIG
    PL_TFSA : [] , # if Mark = TML, if Lulu = MFC
    PL_RRSP : [] #{ ATL:[], DYN:[], MFC:[], MMF:[], TML:[] }
}

    # parsing states
STATE_SEARCH = 0
FIND_OWNER   = STATE_SEARCH + 1
FIND_FUND    = FIND_OWNER   + 1
FIND_NEXT_TX = FIND_FUND    + 1
FILL_CURR_TX = FIND_NEXT_TX + 1

# file paths
GNC_FOLDER = "/home/marksa/dev/Python/gnucash/"
PRAC1_GNC  = GNC_FOLDER + "practice1.gnc"
PRAC2_GNC  = GNC_FOLDER + "practice2.gnc"
PRAC3_GNC  = GNC_FOLDER + "practice3.gnc"
PRAC4_GNC  = GNC_FOLDER + "practice4.gnc"
