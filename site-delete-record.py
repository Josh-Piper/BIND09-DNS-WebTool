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

#Get the last didgits from an IP address.
#Used for removing a PTR record
def get_last_octet_number(ipaddress):
	octets = ipaddress.split('.')
	return octets[-1]
	
#Get converted data type if fourth parameter is passed. Used to support other record types.	
def convertType(type):	
	
	choices = {'cname':dns.rdatatype.CNAME, 'a':dns.rdatatype.A, 'mx':dns.rdatatype.MX}
	key = type.lower()
	return choices.get(key, 'default')	
	
#Datatype to String		
def get_datatype_string(getType):

	choices = {dns.rdatatype.CNAME:'CNAME', dns.rdatatype.A:'A', dns.rdatatype.MX:'MX'}
	return choices.get(getType, 'default')	
	
def main():

	#Define global key 
	key = dns.tsigkeyring.from_text({
		'ddns.key': 'vgwHU16TVZaG6o57OdnMqJGaQf89Rd6/FCfBjEFKQTg='
    })
	ip = None

	#Declare parametres gathered from webpage.
	sub_domain = sys.argv[1]
	
	parentZone = sys.argv[2]
	
	if len(sys.argv) == 4:
		data_type = convertType(sys.argv[3])
	else: 	
		data_type = dns.rdatatype.A	

	full_fqdn_name = sub_domain + '.' + parentZone

	#Only get FQDN if IP is used
	if (get_datatype_string(data_type) != "CNAME"):
		ip = socket.gethostbyname(full_fqdn_name)


	#Insert query into the DNS BIND09 Server
	zone = dns.update.Update(parentZone, keyring=key) 
	update = zone.delete(sub_domain, data_type)
	response = dns.query.tcp(zone, '127.0.0.1')
	
	
	try:
	#Check if IP address in in Swinburne IP range, ADD PTR record if is.
		if (IPAddress(ip) in IPNetwork("136.186.230.0/24")):
			reverse_zone = dns.update.Update("230.186.136.in-addr.arpa.", keyring=key) 
			ip_last_octet = get_last_octet_number(ip)
			pdate2 = reverse_zone.delete(ip_last_octet, dns.rdatatype.PTR) 
			response2 = dns.query.tcp(reverse_zone, '127.0.0.1')
	except Exception as e:
		print(e)
	


if __name__ == '__main__':
	main()
