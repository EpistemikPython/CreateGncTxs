#!/usr/bin/env python3

def findPrimes(z):
    for n in range(2, (z+1)):
        for x in range(2, n):
            if n % x == 0:
                print(n, '=', x, '*', n//x)
                break
        else:
            # loop fell through without finding a factor
            print(n, 'is a prime number!')


def main():
    anum = int(input("Please enter a number: "))
    findPrimes(anum)

if __name__ == "__main__":
    main()
