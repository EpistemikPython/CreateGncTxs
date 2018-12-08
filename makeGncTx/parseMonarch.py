
# parseMonarch.py -- parse a Monarch text file 
#                    and create Gnucash transactions from the data
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
__updated__ = "2018-12-08 08:32"

import sys  
import os

CLIENT_TX = "CLIENT TRANSACTIONS"
PLAN_TYPE = "Plan Type"
PL_OPEN   = "OPEN"
PL_TFSA   = "TFSA"
PL_RRSP   = "RRSP"

FUND_CODE    = "Fund Code"
# re = ([0-9]{2}/[0-9]{2}/[0-9]{4})
TRADE_DATE   = "Trade Date"
DESCRIPTION  = "Description"
GROSS        = "Gross"
NET          = "Net"
UNITS        = "Units"
PRICE        = "Price"
UNIT_BALANCE = "Unit Balance" 

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

mon_open = list()
mon_tfsa = list()
mon_rrsp = list()
Monarch_record = {
    PL_OPEN : [] ,
    PL_TFSA : [] ,
    PL_RRSP : []
}

Monarch_tx = {
    FUND_CODE    : "" ,
    TRADE_DATE   : "" ,
    DESCRIPTION  : "" ,
    GROSS        : "" ,
    NET          : "" ,
    UNITS        : "" ,
    PRICE        : "" ,
    UNIT_BALANCE : "" 
}

def parseFile(file):
    print("parseFile()\n")
    # ?? look for 'CLIENT TRANSACTIONS' = start of transactions
    # loop:
    #     check for 'Plan Type:'
    #         next line is either 'OPEN...', 'TFSA...' or 'RRSP...'
    #         use that as the key for the record
    #     check for $INVESTMENT_COMPANY/$MF_NAME-... :
    #         use $MF_NAME as the Fund Code in the tx
    #     look for date: MM/DD/YYYY = 'Trade Date'
    #         then parse:
    #             2 lines = 'Description'  : Text
    #               line  = 'Gross'        : Currency float
    #               line  = 'Net'          : Currency float
    #               line  = 'Units'        : float
    #               line  = 'Price'        : Currency float
    #               line  = 'Unit Balance' : float

    with open(file) as fp:
        ct = 0
        for line in fp:
            print("line {} contents: {}".format(ct, line))
            #
            ct += 1

def main():  
    filepath = sys.argv[1]
    
    if not os.path.isfile(filepath):
        print("File path {} does not exist. Exiting...".format(filepath))
        sys.exit()
    
    parseFile(filepath)

if __name__ == '__main__':  
   main()
