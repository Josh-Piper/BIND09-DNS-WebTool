#!/usr/local/bin/python 

#Required imports
import sys
import socket

def main():
	#Perform a nslookup from the first parameter
	domain_search = sys.argv[1]
	#Redirect the output to a file.
	with open('./lookup_result.txt', 'w') as f:
		try:
			output = socket.gethostbyname_ex(domain_search)
			print(output, file=f)
		except Exception as e:
				print(e, file=f)


    
#Start Main()
if __name__ == '__main__':
    main()