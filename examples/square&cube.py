#!/usr/bin/env python3

def squareIt(n):
    '''Square the given number.'''
    return n * n

def cubeIt(n):
    '''Cube the given number.'''
    return n*n*n

def main():
    anum = int( input("Please enter a number: ") )
#     print('Square:', squareIt(anum))
#     print('Cube:', cubeIt(anum))
    print( "Square: {0}".format(squareIt(anum)) )
    print( "Cube: {0}".format(cubeIt(anum)) )
    print("Bye!\n")
    
if __name__ == "__main__":
    main()
