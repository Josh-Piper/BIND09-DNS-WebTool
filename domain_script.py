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
import signal
from dns.exception import DNSException
from netaddr import IPNetwork, IPAddress, valid_ipv4
from subprocess import call


#Class to create user accounts
class Account():
	def __init__(self, username, password):
		self._username = username
		self._password = password
		self._zones = []

	#Getter and Setter properties
	@property
	def username(self):
		return self._username

	@property
	def password(self):
		return self._password

	@property
	def zones(self):
		return self._zones
	
	def addZone(self, zone):
		self._zones.append(zone)



#Login process
def login(accounts):
	
	#Load loop to continue the login process unless user is logged in
	loop = True
	login = False

	while loop == True:
		username = input("Enter your username:\n")
		password = input("Enter your password:\n")
		
		for account in accounts:
			#If the user account is correct. Login.
			if (username == account.username and password == account.password):
				print('You are logged in as: ' + username)
				login = True
				loop = False
				
				#Return user account that is logged in.
				return account
				break
				
		#Continue the loop if login failed		
		if (login == False):
			print('Incorrect Details!!!')
			continue

#All user account details to login along with their zones (this will allow dnssec to be used, each user/zone can have an identified key)
def defineAccounts():
	Lemonade = Account("Lemonade", "Stand")
	Juice = Account("Juice", "Boost")

	Lemonade.addZone("unix.")
	Lemonade.addZone("minecraft.com.")
	Juice.addZone("bigbrick.com.")
	Juice.addZone("littleegg.net.")
	accounts = [Lemonade, Juice]

	return accounts
	
#Reusable method to print a list of options for a user to select
def iteratePrint(options, ask, username):
	while True:
		i = 0
		for o in options:
			print('Enter ' + str(i) + ' for ' + o)
			i += 1
		print('Enter -1 for exiting')	
		choose = input("Please choose a " + ask + '\n')
		try:
			if (0 <= int(choose) <= i):
				return int(choose)
			elif (int(choose) == -1):
				os.kill(os.getppid(), signal.SIGHUP)
			else:
				print('invalid option')
				continue
		except Exception as e:
			print('Only numbers are allowed')
			continue 

#Get last hectet from a IP address
def get_last_octet_number(ipaddress):
	octets = ipaddress.split('.')
	return octets[-1]
			
#All main datatypes. string to datatype for DNSPython			
def get_datatype():

	choices = {'cname':dns.rdatatype.CNAME, 'a':dns.rdatatype.A, 'mx':dns.rdatatype.MX}
	type = input('Valid Types include (CNAME, A, and MX)... Please select a data type: ')
	key = type.lower()

	return choices.get(key, 'default')

#Datatype to String		
def get_datatype_string(getType):

	choices = {dns.rdatatype.CNAME:'CNAME', dns.rdatatype.A:'A', dns.rdatatype.MX:'MX'}
	return choices.get(getType, 'default')	

#Adding a record, both for a designated zone and if applicable, the PTR zone.	
def add_record(zone, key):
	
	#Collect basic details needed to add the record type.
	data_type = get_datatype()
	if (data_type != dns.rdatatype.CNAME):
		name = input('Enter the subdomain wanted ([THIS].domain.tld.): ')
		ip = input('Enter the designated IP address wanted: ')
	else:
		name = input('Enter the alias you wanted: ')
		ip = input('Enter the subdomain of the wanted alias, i.e. [ns1]: ')
	
		
	og_zone = zone
	full_fqdn_name = name + '.' + og_zone

	#Validation - Check for spaces in subdomain, ensure IP is IPAddress and check if subdomain exists in Domain.

	#Check if subdomain exists
	call(["./doesRecordExist", name, get_datatype_string(data_type), og_zone])
	f = open("./getRecordsFromZoneContainsKey.txt", "r")
	canAddRecord = f.read()
	
	if (len(name) == 0 or len(ip) == 0):
		print('Valid Data must be Inputted')
	elif ("True" in canAddRecord):
		print('The record you wish to add already exists in that domain.\n')
	#Check IP is IPAddress
	elif (valid_ipv4(ip) != True):
		print('Invalid IP address.\n')
	#Check for spaces in name
	elif (' ' in name):
		print('Spaces can not be in the subdomain.\n')
	else:
		#DNSPython query. Will add the record.
		zone = dns.update.Update(zone, keyring=key)
		update = zone.add(name, 86400, data_type, ip)	
		response = dns.query.tcp(zone, '127.0.0.1')
		
		#UPDATE ACCORDING TO THE REVERSE LOOKUP ZONE HERE
		if (data_type != dns.rdatatype.CNAME):
			if (IPAddress(ip) in IPNetwork("136.186.230.0/24")):
				zone2 = dns.update.Update("230.186.136.in-addr.arpa.", keyring=key) 
				ip_last_octet = get_last_octet_number(ip)
				update2 = zone2.add(ip_last_octet, 86400, dns.rdatatype.PTR, full_fqdn_name) 
				response2 = dns.query.tcp(zone2, '127.0.0.1')
				
				print('\nAdded PTR recorded for the deligated domain')
			print('-----------------------------------')
		print('Completed Adding Record! \n')

			
		
#Deleting a record, both for a designated zone and if applicable, the PTR zone.		
def del_record(zone, key):	
	
	
	data_type = get_datatype()
	name = input('Enter the subdomain you want to delete: ')
	og_zone = zone
	
	#Check if subdomain exists
	call(["./doesRecordExist", name, get_datatype_string(data_type), og_zone])
	f = open("./getRecordsFromZoneContainsKey.txt", "r")
	canAddRecord = f.read()

	if ("False" in canAddRecord):
		print('Record Doesnt exist in the Zone, nothing to delete')
	else:	
		#Get last octet number for deleting the PTR record
		full_fqdn_name = name + '.' + og_zone
		ip = socket.gethostbyname(full_fqdn_name)
		
		zone = dns.update.Update(zone, keyring=key) 
		update = zone.delete(name, data_type)
		response = dns.query.tcp(zone, '127.0.0.1')
		
		
		#UPDATE ACCORDING TO THE REVERSE LOOKUP ZONE
		if (IPAddress(ip) in IPNetwork("136.186.230.0/24")):
			
			ip_last_octet = get_last_octet_number(ip)
			zone2 = dns.update.Update("230.186.136.in-addr.arpa.", keyring=key) 
			update2 = zone2.delete(ip_last_octet, dns.rdatatype.PTR) 
			response2 = dns.query.tcp(zone2, '127.0.0.1')
			print('\nDeleted PTR recorded for the deligated domain')
			
		print('-----------------------------------')
		print('Completed Deleting Record! \n')
	
def update_record(zone, key):
	data_type = get_datatype()
	del_name = input('Enter the subdomain of current record to update: ')
	add_name = input('Enter the subdomain of new record to update: ')
	add_ip = input('Enter the ip address of new record to update: ')
	
	#Required declarations for pointer addresses.
	og_zone = zone
	
	#Check if old subdomain exists - can't update what doesn't exist
	call(["./doesRecordExist", del_name, get_datatype_string(data_type), og_zone])
	f = open("./getRecordsFromZoneContainsKey.txt", "r")
	oldRecord = f.read()

	if ("False" in oldRecord):
		print('No Record to Update in this Zone')
	else:	
		#Needed variables to delete old subdomain
		del_full_fqdn_name = del_name + '.' + og_zone
		del_ip = socket.gethostbyname(del_full_fqdn_name)

		#Check if new subdomain exists
		call(["./doesRecordExist", add_name, get_datatype_string(data_type), og_zone])
		f = open("./getRecordsFromZoneContainsKey.txt", "r")
		canAddRecord = f.read()

		
		if ("True" in canAddRecord and str(del_name) != str(add_name)):
			print('The record you wish to add already exists in that domain.\n')
		#Check IP is IPAddress
		elif (valid_ipv4(add_ip) != True):
			print('Invalid IP address.\n')
		#Check for spaces in name
		elif (' ' in add_name):
			print('Spaces can not be in the new subdomain.\n')
		else:
			#Delete old DNS Record
			zone = dns.update.Update(zone, keyring=key) 
			update = zone.delete(del_name, data_type)
			response = dns.query.tcp(zone, '127.0.0.1')
			
			if (IPAddress(del_ip) in IPNetwork("136.186.230.0/24")):
				del_ip_last_octet = get_last_octet_number(del_ip)
				zone2 = dns.update.Update("230.186.136.in-addr.arpa.", keyring=key) 
				update2 = zone2.delete(del_ip_last_octet, dns.rdatatype.PTR) 
				response2 = dns.query.tcp(zone2, '127.0.0.1')
				
			#Add Record into Namedb
			update2 = zone.add(add_name, 86400, data_type, add_ip)	
			response2 = dns.query.tcp(zone, '127.0.0.1')

				
			if (IPAddress(add_ip) in IPNetwork("136.186.230.0/24")):
				zone2 = dns.update.Update("230.186.136.in-addr.arpa.", keyring=key) 
				new_ip_last_octet = get_last_octet_number(add_ip)
				add_full_fqdn_name = add_name + '.' + og_zone
				update2 = zone2.add(new_ip_last_octet, 86400, dns.rdatatype.PTR, add_full_fqdn_name) 
				response2 = dns.query.tcp(zone2, '127.0.0.1')

			print('\nCompleted Updating Record!\n')	
				

	
#Print all records existing in a domain
def print_records(zone):
	record_types = ['A', 'MX', 'CNAME', 'NS']

	#get all name servers
	soa_answer = dns.resolver.resolve(zone, 'SOA')
	
	for i in record_types:
	
		print('\nPrinting all Record Types: ' + i + '\n')
		#get primary name server #dns.resolver.query
		master_answer = dns.resolver.resolve(soa_answer[0].mname, i)
		
		#get list of records
		z = dns.zone.from_xfr(dns.query.xfr(master_answer[0].address, zone))
		
		#print all records in valid type
		for n in sorted(z.nodes.keys()):
			print(z[n].to_text(n))
		
	
			
#Main Program.
def main():
	#Welcome Message
	print("\n\n\n" + "Welcome to the BIND9 Configuration Script!" + "\nExiting this script will terminate your stay here." + "\n\n")
		
	#Define loop and options
	exit = False
	options = ["Add Records", "Update Records", "Remove Records", "Current Records", "nslookup"]
	
	
	#Login Sequence
	logged_user = login(defineAccounts())
	
	#constant ring used.
	key = dns.tsigkeyring.from_text({
            'ddns.key': 'vgwHU16TVZaG6o57OdnMqJGaQf89Rd6/FCfBjEFKQTg='
    })

	#Script Allocation depending on user
	while exit == False: 
	
		print('\n' + '--==Logged in as: ' + logged_user.username + '==--\n')
		
		choose_zone = iteratePrint(logged_user.zones, 'zone', logged_user.username)
		zone = logged_user.zones[choose_zone]
		record_specified = iteratePrint(options, 'mode', logged_user.username)	
	
		#Adding/Deleting/Modifying Records
		try:
			if (record_specified == 0):
				add_record(zone, key)
			elif (record_specified == 1):
				update_record(zone, key)
			elif (record_specified == 2):
				del_record(zone, key)
			elif (record_specified == 3):
				print_records(zone)
			elif (record_specified == 4):
				#Perform nslookup.
				domain_search = input('Enter the Domain you want to query: ')
				print(os.system('nslookup ' + domain_search))
			else:
				print('Please select an option')
				continue
		except Exception as e:
			print(e)

#Start Main
if __name__ == '__main__':
    main()
