#!/usr/local/bin/python

#Required imports for DNSPython
import dns.zone
import dns.query
import dns.update
import dns.rdataset
import dns.resolver
import dns.tsigkeyring
import dns.rdtypes.IN.A
import socket
import sys
import os
from dns.exception import DNSException
from netaddr import IPNetwork, IPAddress

#Get last hectet of an IP address. Used for PTR records
def get_last_octet_number(ipaddress):
	octets = ipaddress.split('.')
	return octets[-1]
	
#Get converted data type if fourth parameter is passed. Used to support other record types.	
def convertType(type):	
	
	choices = {'cname':dns.rdatatype.CNAME, 'a':dns.rdatatype.A, 'mx':dns.rdatatype.MX}
	key = type.lower()
	return choices.get(key, 'default')
	
	
def main():

	#Global key
	key = dns.tsigkeyring.from_text({
		'ddns.key': 'vgwHU16TVZaG6o57OdnMqJGaQf89Rd6/FCfBjEFKQTg='
    })

	#Declare parametres gathered from webpage.
	sub_domain = sys.argv[1]
	ip = sys.argv[2]
	parentZone = sys.argv[3]
	
	if len(sys.argv) == 5:
		data_type = convertType(sys.argv[4])
	else: 	
		data_type = dns.rdatatype.A	
	
	
	#Insert query into the DNS BIND09 Server
	zone = dns.update.Update(parentZone, keyring=key) 
	zone.add(sub_domain, 86400, data_type, ip)
	response = dns.query.tcp(zone, '127.0.0.1')
	try:
	#Check if IP address in in Swinburne IP range, ADD PTR record if is.
		if (data_type != dns.rdatatype.CNAME):
			if (IPAddress(ip) in IPNetwork("136.186.230.0/24")):
				full_fqdn_name = sub_domain + '.' + parentZone
				reverse_zone = dns.update.Update("230.186.136.in-addr.arpa.", keyring=key) 
				ip_last_octet = get_last_octet_number(ip)
				reverse_zone.add(ip_last_octet, 86400, dns.rdatatype.PTR, full_fqdn_name) 
				response2 = dns.query.tcp(reverse_zone, '127.0.0.1')
	except Exception as e:
		print(e)
	


if __name__ == '__main__':
	main()
