
import sys  
import os

def main():  
    filepath = sys.argv[1]

    if not os.path.isfile(filepath):
        print("File path {} does not exist. Exiting...".format(filepath))
        sys.exit()

    bag_of_words = {}
    with open(filepath) as fp:
        cnt = 0
        for line in fp:
            print("line {} contents {}".format(cnt, line))
            record_word_cnt(line.strip().split(' '), bag_of_words)
            cnt += 1
    sorted_words = order_bag_of_words(bag_of_words, desc=True)
    print("Most frequent 10 words {}".format(sorted_words[:10]))

def parseFile(file):
    print("parseFile")
    # look for 'CLIENT TRANSACTIONS' = start of transactions
    # loop:
    #     check for 'Plan Type:'
    #         next line is either 'OPEN...', 'TFSA...' or 'RRSP...'
    #     check for $INVESTMENT_COMPANY/$MF_NAME... :
    #         change Account saving to
    #     look for date: MM/DD/YYYY = 'Trade Date'
    #         then parse:
    #             2 lines = 'Description'  : Text
    #               line  = 'Gross'        : Currency float
    #               line  = 'Net'          : Currency float
    #               line  = 'Units'        : float
    #               line  = 'Price'        : Currency float
    #               line  = 'Unit Balance' : float

def order_bag_of_words(bag_of_words, desc=False):  
    words = [(word, cnt) for word, cnt in bag_of_words.items()]
    return sorted(words, key=lambda x: x[1], reverse=desc)

def record_word_cnt(words, bag_of_words):  
    for word in words:
        if word != '':
            if word.lower() in bag_of_words:
                bag_of_words[word.lower()] += 1
            else:
                bag_of_words[word.lower()] = 1

def printLines():
    filepath = 'Iliad.txt'  
    with open(filepath) as fp:  
       for cnt, line in enumerate(fp):
           print("Line {}: {}".format(cnt, line))
       
if __name__ == '__main__':  
   main()
