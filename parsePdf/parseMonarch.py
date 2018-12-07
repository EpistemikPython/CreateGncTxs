
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
DYN_029   = "DYN 029"
DYN_729   = "DYN 729"
DYN_1562  = "DYN 1562"
DYN_1560  = "DYN 1560"
MMF_44424 = "MMF 44424"
MMF_4524  = "MMF 4524"

FundsList = [ 
    CIG_11461, CIG_11111,
    TML_674, TML_704, TML_203, TML_519, TML_1017, TML_1017, 
    MFC_856, MFC_6129, MFC_6130, MFC_6138, MFC_302, MFC_3232,
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
