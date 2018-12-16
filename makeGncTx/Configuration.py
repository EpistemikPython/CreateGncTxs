
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
__updated__ = "2018-12-16 09:48"

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

# Fund names
CIG_11461 = CIG + " 11461"
CIG_11111 = CIG + " 11111"
CIG_18140 = CIG + " 18140"
TML_674   = TML + " 674"
TML_704   = TML + " 704"
TML_203   = TML + " 203"
TML_519   = TML + " 519"
TML_1017  = TML + " 1017"
TML_1018  = TML + " 1018"
MFC_856   = MFC + " 856"
MFC_6129  = MFC + " 6129"
MFC_6130  = MFC + " 6130"
MFC_6138  = MFC + " 6138"
MFC_302   = MFC + " 302"
MFC_3232  = MFC + " 3232"
MFC_3689  = MFC + " 3689"
MFC_1960  = MFC + " 1960"
DYN_029   = DYN + " 029"
DYN_729   = DYN + " 729"
DYN_1562  = DYN + " 1562"
DYN_1560  = DYN + " 1560"
MMF_44424 = MMF + " 44424"
MMF_4524  = MMF + " 4524"

FundsList = [ 
    CIG_11461, CIG_11111, CIG_18140, 
    TML_674, TML_704, TML_203, TML_519, TML_1017, TML_1018, 
    MFC_856, MFC_6129, MFC_6130, MFC_6138, MFC_302, MFC_3232, MFC_3689, MFC_1960, 
    DYN_029, DYN_729, DYN_1562, DYN_1560,
    MMF_44424, MMF_4524
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
    FUND_CMPY    : "" ,
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
ASSET_MARK  = "Mark"
ASSET_LULU  = "Lulu"
RRSP_REV_Mk = "Mk-RR"
RRSP_REV_Lu = "Lu-RR"
TFSA_REV_Mk = "Mk-TF"
TFSA_REV_Lu = "Lu-TF"

# find the proper account in the gnucash file
Account_Paths = {
    PL_OPEN: {
        REVENUE : ["REV", "REV_Invest", "Dist", PL_OPEN] ,
        ASSET   : ["FAMILY", "INVEST", PL_OPEN] 
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

# list of gnucash transactions, by date, for each company
Gnucash_record = {
    OWNER : "" ,
    CIG : [] ,
    TML : [] ,
    MFC : [] ,
    DYN : [] ,
    MMF : []
}

# parsing states
STATE_SEARCH   = 0
FIND_OWNER     = STATE_SEARCH + 1
FIND_FUND      = FIND_OWNER   + 1
FIND_NEXT_TX   = FIND_FUND    + 1
FILL_CURR_TX   = FIND_NEXT_TX + 1

# file paths
PRAC_GNC = "/bak/home/marksa/dev/Python/gnucash/liclipse/practice.gnc"
PRAC1_GNC = "/bak/home/marksa/dev/Python/gnucash/liclipse/practice1.gnc"
PRAC2_GNC = "/bak/home/marksa/dev/Python/gnucash/liclipse/practice2.gnc"
PRAC3_GNC = "/bak/home/marksa/dev/Python/gnucash/liclipse/practice3.gnc"
RL_GNC       = "/bak/home/marksa/dev/Python/gnucash/liclipse/RL.gnc"
NEW_GNC      = "/bak/home/marksa/dev/Python/gnucash/liclipse/new.gnc"
