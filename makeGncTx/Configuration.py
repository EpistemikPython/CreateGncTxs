
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
__updated__ = "2018-12-23 07:11"

CLIENT_TX = "CLIENT TRANSACTIONS"
PLAN_TYPE = "Plan Type:"
OWNER     = "Owner"
AUTO_SYS  = "Automatic/Systematic"

# Plan types
PL_OPEN   = "OPEN"
PL_TFSA   = "TFSA"
PL_RRSP   = "RRSP"

# tx categories
FUND_CODE  = "Fund Code"
FUND_CMPY  = "Fund Company"
TRADE_DATE = "Trade Date"
DESC       = "Description"
GROSS      = "Gross"
NET        = "Net"
UNITS      = "Units"
PRICE      = "Price"
UNIT_BAL   = "Unit Balance" 

# Fund companies
CIG = "CIG"
TML = "TML"
MFC = "MFC"
DYN = "DYN"
MMF = "MMF"

CMPY_FULL_NAME = {
    CIG : "CI Investments",
    TML : "Franklin Templeton",
    MFC : "Mackenzie Financial Corp",
    DYN : "Dynamic Funds",
    MMF : "Manulife Mutual Funds"
}

# Fund names
CIG_11461 = CIG + " 11461"
CIG_11111 = CIG + " 11111"
CIG_2304  = CIG + " 2304"
CIG_2321  = CIG + " 2321"
CIG_6104  = CIG + " 6104"
CIG_1154  = CIG + " 1154"
CIG_1304  = CIG + " 1304"
CIG_1521  = CIG + " 1521"
CIG_18140 = CIG + " 18140"
TML_180   = TML + " 180"
TML_184   = TML + " 184"
TML_202   = TML + " 202"
TML_203   = TML + " 203"
TML_518   = TML + " 518"
TML_519   = TML + " 519"
TML_598   = TML + " 598"
TML_674   = TML + " 674"
TML_694   = TML + " 694"
TML_704   = TML + " 704"
TML_707   = TML + " 707"
TML_1017  = TML + " 1017"
TML_1018  = TML + " 1018"
MFC_756   = MFC + " 756"
MFC_856   = MFC + " 856"
MFC_6129  = MFC + " 6129"
MFC_6130  = MFC + " 6130"
MFC_6138  = MFC + " 6138"
MFC_302   = MFC + " 302"
MFC_2238  = MFC + " 2238"
MFC_3232  = MFC + " 3232"
MFC_3769  = MFC + " 3769"
MFC_3689  = MFC + " 3689"
MFC_1960  = MFC + " 1960"
DYN_029   = DYN + " 029"
DYN_729   = DYN + " 729"
DYN_1562  = DYN + " 1562"
DYN_1560  = DYN + " 1560"
MMF_4524  = MMF + " 4524"
MMF_44424 = MMF + " 44424"
MMF_3517  = MMF + " 3517"
MMF_13417 = MMF + " 13417"

FundsList = [ 
    CIG_11461, CIG_11111, CIG_18140, CIG_2304, CIG_2321, CIG_6104, CIG_1154, CIG_1304, CIG_1521,
    TML_674, TML_704, TML_180, TML_184, TML_202, TML_203, TML_518, TML_519, TML_598, TML_694, TML_707, TML_1017, TML_1018, 
    MFC_756, MFC_856, MFC_6129, MFC_6130, MFC_6138, MFC_302, MFC_2238, MFC_3232, MFC_3769, MFC_3689, MFC_1960, 
    DYN_029, DYN_729, DYN_1562, DYN_1560,
    MMF_44424, MMF_4524, MMF_3517, MMF_13417
]

# owner and list of transactions for each plan type
Monarch_record = {
    OWNER   : "" ,
    PL_OPEN : [] ,
    PL_TFSA : [] ,
    PL_RRSP : []
}

# information for each transaction
Monarch_tx = {
    FUND_CMPY   : "" ,
    FUND_CODE   : "" ,
    TRADE_DATE  : "" ,
    DESC        : "" ,
    GROSS       : "" ,
    NET         : "" ,
    UNITS       : "" ,
    PRICE       : "" ,
    UNIT_BAL    : "" 
}

REVENUE  = "REVENUE"
ASSET    = "ASSET"
TRUST    = "TRUST"
MON_MARK = "Mark H. Sattolo"
MON_LULU = "Louise Robb"
GNU_MARK = "Mark"
GNU_LULU = "Lulu"

TRUST_ACCT = CIG_18140

# find the proper account in the gnucash file
ACCT_PATHS = {
    REVENUE  : ["REV", "REV_Invest", "Dist"] ,# + planType [+ Owner]
    ASSET    : ["FAMILY", "INVEST"] ,# + planType [+ Owner]
    MON_MARK : GNU_MARK ,
    MON_LULU : GNU_LULU ,
    TRUST    : ["XTERNAL", TRUST, "Trust Assets", "Monarch ITF", CMPY_FULL_NAME[CIG] ]
}

# information for each switch transaction
Gnucash_switch = {
    FUND_IN     : "" ,
    FUND_OUT    : "" ,
    TRADE_DATE  : "" ,
    DESC        : "" ,
    GROSS       : "" ,
    NET         : "" ,
    UNITS       : "" ,
    PRICE       : "" ,
    UNIT_BAL    : "" 
}

# list of gnucash switches, by date, for each company
Gnucash_record = {
    OWNER     : "" ,
    PLAN_TYPE : "" ,
    CIG       : [] ,
    TML       : [] ,
    MFC       : [] ,
    DYN       : [] ,
    MMF       : []
}

# parsing states
STATE_SEARCH   = 0
FIND_OWNER     = STATE_SEARCH + 1
FIND_FUND      = FIND_OWNER   + 1
FIND_NEXT_TX   = FIND_FUND    + 1
FILL_CURR_TX   = FIND_NEXT_TX + 1

# file paths
GNC_FOLDER = "/home/marksa/dev/Python/gnucash/"
PRAC1_GNC  = GNC_FOLDER + "practice1.gnc"
PRAC2_GNC  = GNC_FOLDER + "practice2.gnc"
PRAC3_GNC  = GNC_FOLDER + "practice3.gnc"
PRAC4_GNC  = GNC_FOLDER + "practice4.gnc"
