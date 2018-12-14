
# Configuration.py -- static defines to help parse a Monarch text file 
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
__updated__ = "2018-12-14 18:13"

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
# re = ([0-9]{2}/[0-9]{2}/[0-9]{4})
TRADE_DATE = "Trade Date"
DESC       = "Description"
GROSS      = "Gross"
NET        = "Net"
UNITS      = "Units"
PRICE      = "Price"
UNIT_BAL   = "Unit Balance" 

# Fund codes
# re = ([A-Z]{3}_[0-9]{3,5})
CIG_11461 = "CIG 11461"
CIG_11111 = "CIG 11111"
CIG_18140 = "CIG 18140"
TML_674   = "TML 674"
TML_704   = "TML 704"
TML_203   = "TML 203"
TML_519   = "TML 519"
TML_1017  = "TML 1017"
TML_1018  = "TML 1018"
MFC_856   = "MFC 856"
MFC_6129  = "MFC 6129"
MFC_6130  = "MFC 6130"
MFC_6138  = "MFC 6138"
MFC_302   = "MFC 302"
MFC_3232  = "MFC 3232"
MFC_3689  = "MFC 3689"
MFC_1960  = "MFC 1960"
DYN_029   = "DYN 029"
DYN_729   = "DYN 729"
DYN_1562  = "DYN 1562"
DYN_1560  = "DYN 1560"
MMF_44424 = "MMF 44424"
MMF_4524  = "MMF 4524"

FundsList = [ 
    CIG_11461, CIG_11111, CIG_18140, 
    TML_674, TML_704, TML_203, TML_519, TML_1017, TML_1018, 
    MFC_856, MFC_6129, MFC_6130, MFC_6138, MFC_302, MFC_3232, MFC_3689, MFC_1960, 
    DYN_029, DYN_729, DYN_1562, DYN_1560,
    MMF_44424, MMF_4524
]

Monarch_record = {
    OWNER   : "" ,
    PL_OPEN : [] ,
    PL_TFSA : [] ,
    PL_RRSP : []
}

Monarch_tx = {
    FUND_CODE    : "" ,
    TRADE_DATE   : "" ,
    DESC         : "" ,
    GROSS        : "" ,
    NET          : "" ,
    UNITS        : "" ,
    PRICE        : "" ,
    UNIT_BAL     : "" 
}

REVENUE = "REVENUE"
ASSET   = "ASSET"
OWNER_MARK = "Mark H. Sattolo"
OWNER_LULU = "Louise Robb"
ACCT_MARK  = "Mark"
ACCT_LULU  = "Lulu"
RRSP_ACCT_Mk = "Mk-RR"
RRSP_ACCT_Lu = "Lu-RR"
TFSA_ACCT_Mk = "Mk-TF"
TFSA_ACCT_Lu = "Lu-TF"

Account_Paths = {
    PL_OPEN: {
        REVENUE : ["REV", "REV_Invest", "Dist", PL_OPEN] ,
        ASSET   : ["FAMILY", "INVEST", "Open", "RB-Joint", "CI Open"] 
    } ,
    PL_TFSA: {
        REVENUE : ["REV", "REV_Invest", "Dist", PL_TFSA] ,
        ASSET   : ["FAMILY", "INVEST", PL_TFSA] 
    } ,
    PL_RRSP: {
        REVENUE : ["REV", "REV_Invest", "Dist", PL_RRSP] ,
        ASSET   : ["FAMILY", "INVEST", PL_RRSP] 
    }
}

# parsing states
STATE_SEARCH   = 0
FIND_OWNER     = STATE_SEARCH + 1
FIND_FUND      = FIND_OWNER   + 1
FIND_NEXT_TX   = FIND_FUND    + 1
FILL_CURR_TX   = FIND_NEXT_TX + 1

# file paths
PRACTICE_GNC = "/bak/home/marksa/dev/Python/gnucash/liclipse/practice.gnc"
RL_GNC       = "/bak/home/marksa/dev/Python/gnucash/liclipse/RL.gnc"
NEW_GNC      = "/bak/home/marksa/dev/Python/gnucash/liclipse/new.gnc"
