#!/usr/local/bin/python 

#Required imports
import sys
import dns.resolver
import dns.zone
	
def main():	
	record_types = ['A', 'MX', 'CNAME', 'NS']

	zone = sys.argv[1]

	
	#Redirect the output to a file.
	with open('./list_records.txt', 'w') as f:
		try:
			#get all name servers
			soa_answer = dns.resolver.resolve(zone, 'SOA')
			
			for i in record_types:
				print("The zone scanned is: " + zone, file=f)
				#get primary name server #dns.resolver.query
				master_answer = dns.resolver.resolve(soa_answer[0].mname, i)
				
				#get list of records
				z = dns.zone.from_xfr(dns.query.xfr(master_answer[0].address, zone))
				
				#print all records in valid type
				for n in sorted(z.nodes.keys()):
					print(z[n].to_text(n), file=f)
				
		except Exception as e:
				print("Failure with Scan. Double check Zone name \n" + str(e), file=f)



		
		
#Start Main()
if __name__ == '__main__':
    main()		