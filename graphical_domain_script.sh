#!/usr/local/bin/bash
############################
# The following script is used for a GUI interface
# built upon the previous CLI version.
#############################
#Import user account details
source "account_details"

#Login Loop
LOGIN=false
while [ $LOGIN = false ]
do
	username=$(zenity --entry --text="Enter Username")
	password=$(zenity --entry --text="Enter Password")
	
	#Test login details against existing accounts
	if [ "$username" = "$FIRST_ACCOUNT_USERNAME" ] && [ "$password" = "$FIRST_ACCOUNT_PASSWORD" ]
	then
		LOGIN=true
	elif [ "$username" = "$SECOND_ACCOUNT_USERNAME" ] && [ "$password" = "$SECOND_ACCOUNT_PASSWORD" ]
	then
		LOGIN=true
	else
		zenity --info --text "Incorrect Details..."
		continue
	fi
done

#Select a Zone depending on the user chosen.
while : 
do
	if [ "$username" == "$FIRST_ACCOUNT_USERNAME" ]
	then
		zone=$(zenity --list --title="Choose Your Zone" --column="0" "minecraft.com." "unix." --width=100 --height=200 --hide-header)
	else
		zone=$(zenity --list --title="Choose Your Zone" --column="0" "bigbrick.com." "littleegg.net." --width=100 --height=200 --hide-header)
	fi
		option=$(zenity --list --title="Pick Your Command" --column="0" "Add Record" "Delete Record" "Update Record" "Nslookup" "List All Records" --width=100 --height=200 --hide-header)

	#CRUD actions of records, different details required depending on action
	#Utilises Python scripts as DNSPython is required
	#
	# Add a Record.
	# Simple validation implemented, -> Check record does not current exist, no spaces in subdomain and IP is valid IP if MX or A record.
	#
	regex_pattern=" |'"
	if [ "$option" = "Add Record" ]
	then
		type=$(zenity --list --title="Choose the Type of Record" --column="0" "A" "CNAME" "MX" --width=100 --height=200 --hide-header)
		fqdn=$(zenity --entry --text="Enter the subdomain wanted")

		#Ask different questions depending on the type of Record created
		if [ "$type" = "CNAME" ]
		then
			ip=$(zenity --entry --text="Enter Subdomain To Point To: ")
		else
			ip=$(zenity --entry --text="Enter IP")
		fi	

		#Validation, first, check if record exists
		python3 doesRecordExist "$fqdn" "$type" "$zone"
		containsRecord="`cat ./getRecordsFromZoneContainsKey.txt`"
		if [ ${#fqdn} -eq 0 ] || [ ${#ip} -eq 0 ]
		then
			zenity --info --text "Valid Data must be Inputted" --width=800
		#Add to namedb database if validation is completed and passed.
		elif [[ "$type" = "A" ]] || [[ "$type" = "MX" ]] && [[ ! $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
		then
			zenity --info --text "IP was not a valid IP" --width=800
		elif [[ "$containsRecord" = "False" ]] && [[ ! $fqdn =~ $regex_pattern ]]
		then
			python3 site-add-record.py "$fqdn" "$ip" "$zone" "$type"
			zenity --info --text "Successfully added $fqdn to $zone" --width=800
		else 	
			zenity --info --text "Record already Exists, OR, spaces are in subdomain." --width=800
		fi	
	elif [ "$option" = "Delete Record" ]
	then
	#
	# Delete a Record.
	#
	#
	#
		type=$(zenity --list --title="Choose the Type of Record That You wish To Delete" --column="0" "A" "CNAME" "MX" --width=200 --height=200 --hide-header)
		fqdn=$(zenity --entry --text="Enter the subdomain you want deleted")

		#Validation, first, check if record exists
		python3 doesRecordExist "$fqdn" "$type" "$zone"
		containsRecord="`cat ./getRecordsFromZoneContainsKey.txt`"

		if [[ "$containsRecord" = "False" ]] || [[ ${#fqdn} -eq 0 ]] 
		then
			zenity --info --text "No Record no Remove from the Zone" --width=800
		else
			python3 site-delete-record.py "$fqdn" "$zone" "$type"
			zenity --info --text "Successfully deleted $fqdn from $zone" --width=800
		fi	
	elif [ "$option" = "Update Record" ]
	then
	#
	# Update a Record,
	# 
	#
	#
		type=$(zenity --list --title="Choose the Type of Record" --column="0" "A" "CNAME" "MX" --width=100 --height=200 --hide-header)
		old_fqdn=$(zenity --entry --text="Enter the current subdomain")
		fqdn=$(zenity --entry --text="Enter the new subdomain")
		ip=$(zenity --entry --text="Enter New IP")

		#Validation, first, check if record exists
		python3 doesRecordExist "$old_fqdn" "$type" "$zone"
		containsOldRecord="`cat ./getRecordsFromZoneContainsKey.txt`"

		python3 doesRecordExist "$fqdn" "$type" "$zone"
		containsNewRecord="`cat ./getRecordsFromZoneContainsKey.txt`"
		
		
		#Add to namedb database if validation is completed and passed.
		if [[ "$containsOldRecord" = "False" ]]
		then
			zenity --info --text "No Record to Update" --width=800
		elif [[ "$type" = "A" ]] || [[ "$type" = "MX" ]] && [[ ! $ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
		then
			zenity --info --text "IP was not a valid IP" --width=800
		elif [[ "$containsNewRecord" = "True" ]] && [[ "$old_fqdn" = "$fqdn" ]] || [[ $containsNewRecord == *"False"* ]]
		then
			python3 site-update-record.py "$old_fqdn" "$fqdn" "$ip" "$zone" "$type"
			zenity --info --text "Successfully updated $fqdn from $zone" --width=800
		else 	
			zenity --info --text "Record already Exists, OR, spaces are in subdomain." --width=800
		fi	
	elif [ "$option" = "Nslookup" ]
	then
	#
	# Lookup a Hostname via. nslookup
	#
	#
	#
		hostname=$(zenity --entry --text="Enter Full Hostname")
		python3 site-lookup.py "$hostname"
		result=`cat ./lookup_result.txt`
		zenity --info --text="$result" --width=800
	else
	#
	# List the Records existing in the current zone.
 	# Relies on a CGI script made in Python as DNSPython was required
	# 

		python3 site-list-record.py "$zone"
		result=`cat ./list_records.txt`
		zenity --info --text="$result" --height=500 --width=800
	fi
	# Allowing exiting the application
	#
	#
		#Exit the terminal (parent process) if user does not wish to continue
		ans=$(zenity --list --title="Do you Wish to Continue" --column="0" "No" "Yes" --width=100 --height=200 --hide-header)
		if [ "$ans" = "No" ]
		then
			kill -9 $PPID
		else
			:
		fi
done