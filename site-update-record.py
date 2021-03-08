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


def get_last_octet_number(ipaddress):
	octets = ipaddress.split('.')
	return octets[-1]
	
#Get converted data type if fourth parameter is passed. Used to support other record types.	
def convertType(type):	
	
	choices = {'cname':dns.rdatatype.CNAME, 'a':dns.rdatatype.A, 'mx':dns.rdatatype.MX}
	key = type.lower()
	return choices.get(key, 'default')	
	
	
def main():

	key = dns.tsigkeyring.from_text({
		'ddns.key': 'vgwHU16TVZaG6o57OdnMqJGaQf89Rd6/FCfBjEFKQTg='
    })

	#Declare parametres gathered from webpage.
	old_sub_domain = sys.argv[1]
	sub_domain = sys.argv[2]
	new_ip = sys.argv[3]
	parentZone = sys.argv[4]
	
	if len(sys.argv) == 6:
		data_type = convertType(sys.argv[5])
	else: 	
		data_type = dns.rdatatype.A	
	
	full_fqdn_name = old_sub_domain + '.' + parentZone
	ip = socket.gethostbyname(full_fqdn_name)
	
	
	try:
		#Delete original record from DNS zone
		zone = dns.update.Update(parentZone, keyring=key) 
		update = zone.delete(old_sub_domain, data_type)
		response = dns.query.tcp(zone, '127.0.0.1')
		
		#Check if IP address in Swinburne IP range, If is, delete original record from it.
		if (IPAddress(ip) in IPNetwork("136.186.230.0/24")):
			reverse_zone = dns.update.Update("230.186.136.in-addr.arpa.", keyring=key) 
			ip_last_octet = get_last_octet_number(ip)
			pdate2 = reverse_zone.delete(ip_last_octet, dns.rdatatype.PTR) 
			response2 = dns.query.tcp(reverse_zone, '127.0.0.1')
			
		#Add new record to Zone
		
		new_full_fqdn_name = sub_domain + '.' + parentZone
		
		#DNSPython query. Will add the record.
		zone = dns.update.Update(parentZone, keyring=key)
		update = zone.add(sub_domain, 86400, data_type, new_ip)	
		response = dns.query.tcp(zone, '127.0.0.1')
		
		#Check if IP address in Swinburne IP range, if is, add new record to it.
		if (IPAddress(ip) in IPNetwork("136.186.230.0/24")):
			zone2 = dns.update.Update("230.186.136.in-addr.arpa.", keyring=key) 
			ip_last_octet = get_last_octet_number(new_ip)
			update2 = zone2.add(ip_last_octet, 86400, dns.rdatatype.PTR, new_full_fqdn_name) 
			response2 = dns.query.tcp(zone2, '127.0.0.1')
			
			
	except Exception as e:
		print(e)
	


if __name__ == '__main__':
	main()
