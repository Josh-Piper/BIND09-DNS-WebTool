<html>
	<head>
		<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
		<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
        <link rel="stylesheet" type="text/css" href="styles.css">
	</head>
	<body>
<?php
	////////////////////////////////////
	// The following file is used for CRUD actions
	// of the BIND09 server via. a web application.
	////////////////////////////////////
	//Include details required for Database Connection
	include("config.php"); 

	//Variables used for drawing a specific form
	$logged_in = FALSE;
	$draw_zones = FALSE;
	$draw_records = FALSE;
	$draw_add_records = FALSE;
	$draw_lookup = FALSE;
	$draw_all_records = FALSE;
	
	$username = "";

	//Each form submit, save the form action.
	$formAction = $_POST['form'];
	
	//Connect to the database with details from include statement
	$db = mysqli_connect(dbsvr, dbuser, dbpasswd, dbdb);
	//Log connection to the Console of the browser.
	if ($db) { 
		echo("<script>console.log('Connected to Database');</script>"); 
	} else { 
		echo("<script>console.log('Error Connecting to Database');</script>"); 
	}
	
	//When LOGIN pressed
	if ($formAction == 'login' && isset($_POST['submit'])) {
		//When Submit button pressed, attempt to login.
		$username=$_POST['username'];
		$password=$_POST['password'];
		
		//Compare form inputs to the username and passwords located in the database. 
		$query = "SELECT * FROM users WHERE username = '$username' and password = '$password'";
		$result = mysqli_query($db, $query);
		$row = mysqli_fetch_array($result);

		//If the inputted account details match any account in the database. Login.
		if ($row['username'] == $username && $row['password'] == $password) { 
			$logged_in = TRUE;
			$login = "<h4 class='logged'>Logged in as: " . $username . "</h4>";
		} else {
			$logged_in = FALSE;
			$login = "<h4 class='logged'>Incorrect Details</h4>";
		}
		echo $login;

		
	//When a specified zone is pressed
	//OR perform a NSLookup
	} elseif ($formAction == 'record' && isset($_POST['submit'])) {
		$logged_in = TRUE;
		$username = $_POST['username'];
		$draw_this_zone = $_POST['submit'];
		
		$draw_records = FALSE;
		$draw_add_records = FALSE;
		$draw_all_records = FALSE;
		
		if ($draw_this_zone == "Perform Lookup") {
			$draw_zones = FALSE;
			$draw_lookup = TRUE;
		} else {
			$draw_zones = TRUE;
			$draw_lookup = FALSE;
		}
		
		
	//When form submitted in the viewing all zones records page
	} elseif ($formAction == 'add-record' && isset($_POST['submit'])) {
		$action = $_POST['submit'];
		$logged_in = TRUE;
		$username = $_POST['username'];
		$draw_this_zone = $_POST['parent'];

		//Add New Record	
		if ($action == "ADD RECORD") {

			$draw_zones = FALSE;
			$draw_lookup = FALSE;
			$draw_records = FALSE;
			$draw_add_records = TRUE;
			$draw_all_records = FALSE;

		//Print All Records in Zone
		} elseif ($action == "PRINT ALL RECORDS") {

			$draw_zones = FALSE;
			$draw_lookup = FALSE;
			$draw_records = FALSE;
			$draw_add_records = FALSE;
			$draw_all_records = TRUE;

			//Print select zones records
			$command = escapeshellcmd('./site-list-record.py ' . $draw_this_zone);
			shell_exec($command);
			
			$file = file('/usr/local/www/access/list_records.txt');
			$result = $file[0];
			echo "<h2 class='logged'>" . $result . "</h2>";

		} else {	

			//Update a preexisting Record
			$update_parent = $_POST['parent'];
			$update_domain = $_POST['submit'];
			$data = 'data_type_of_' . $update_domain;
			$update_datatype = $_POST[$data];
			$update_ip = $_POST[$update_domain];

			$draw_zones = FALSE;
			$draw_add_records = FALSE;
			$draw_lookup = FALSE;
			$draw_records = TRUE;
			$draw_all_records = FALSE;
	}
		
	//When ADD clicked for add record to add into SQL and DNS database	
	} elseif ($formAction == 'completed-adding-record' && isset($_POST['submit'])) {
		
		//declare all used variables
		$draw_this_zone = $_POST['parent'];
		$ip = $_POST['ip'];
		$fqdn = $_POST['fqdn'];
		$record_type = $_POST['data_type'];

		//VALIDATION FOR IP 
		$isCNAME = "CNAME" == $record_type;
		$isValidIP = filter_var($ip, FILTER_VALIDATE_IP);
		$isFQDNcontainNoSpaces = (strpos($fqdn, ' ') == 0);
		$isName = "CNAME" == $record_type;
		
		//Check that current Record Does Not Exist in the Specified Zone
		$command = escapeshellcmd('./doesRecordExist ' . $fqdn . ' ' . $record_type . ' ' . $draw_this_zone);
		shell_exec($command);
		$checkRecordExists = file_get_contents("./getRecordsFromZoneContainsKey.txt");
		$pos = strpos($checkRecordExists, "True");

		#Not current activating shell command?
		if (strlen($ip) == 0 || strlen($fqdn) == 0) {
			echo "<h2 class='logged'> Valid Data Must be Inputted. </h2>"; #Incase the HTML required field becomes depricated
		} elseif ($pos !== false) {
			echo "<h2 class='logged'> Record Currently Exists in that Zone. </h2>";
		} elseif (!($isFQDNcontainNoSpaces)) {
			echo "<h2 class='logged'> Incorrect Details, Spaces not Allowed </h2>";
		} elseif ($record_type != 'CNAME' && !$isValidIP) {
			echo "<h2 class='logged'> Incorrect Details, ONLY IP's for A and MX records </h2>";
		} else {
			//ADD INTO SQL SERVER
			$add_sql_query = "INSERT INTO record (Domain, IP, DataType, parentZone) VALUES (?, ?, ?, ?)";
			$stmt = mysqli_prepare($db, $add_sql_query);
			$stmt->bind_param("ssss", $fqdn, $ip, $record_type, $draw_this_zone);
			$stmt->execute();
			
			//ADD INTO DNS BIND09 SERVER via. DNS Python Script.
			$command = escapeshellcmd('./site-add-record.py ' . $fqdn . ' ' . $ip . ' ' . $draw_this_zone . ' ' . $record_type);
			shell_exec($command);
			echo "<h2 class='logged'> Added Record to Database!, domain is " . $fqdn . "." . $draw_this_zone . " </h2>";
		}
		
		$draw_zones = FALSE;
		$draw_records = FALSE;
		$draw_lookup = FALSE;
		$draw_add_records = FALSE;
		$draw_all_records = FALSE;
		$logged_in= TRUE;
		$username = $_POST['username'];


	} elseif ($formAction == 'update-current-record' && isset($_POST['submit'])) { 
		$action = $_POST['submit'];
		$old_fqdn = $_POST['original_fqdn'];
		$new_fqdn = $_POST['new-fqdn'];
		$old_ip = $_POST['original_ip'];
		$old_datatype = $_POST['original_data_type'];
		$new_ip = $_POST['new-ip'];
		$draw_this_zone = $_POST['parent'];

		if ($action == "UPDATE RECORD") {

			//UPDATE RECORD
			$update_sql_query = "UPDATE record SET Domain = ?, IP = ? WHERE Domain = ? and IP = ?";
			$stmt = mysqli_prepare($db, $update_sql_query);
			$stmt->bind_param("ssss", $new_fqdn, $new_ip, $old_fqdn, $old_ip);
			$stmt->execute();
			
			$command = escapeshellcmd('./site-delete-record.py ' . $old_fqdn . " " . $draw_this_zone . " " . $old_datatype);
			shell_exec($command);
			$command2 = escapeshellcmd('./site-add-record.py ' . $new_fqdn . ' ' . $new_ip . ' ' . $draw_this_zone . " " . $old_datatype);
			shell_exec($command2);
			
			echo "<h2 class='logged'> Updated Record! </h2>";
			
		} elseif ($action == "DELETE RECORD") {

			//Get Record Type from MYSQL server
			$query = "SELECT * FROM record WHERE Domain = '$old_fqdn' and IP = '$old_ip'";
			$result = mysqli_query($db, $query);
			$row = mysqli_fetch_array($result);
			$get_data_type = $row['DataType'];
			
			//DELETE RECORD FROM SQL SERVER
			$delete_query = "DELETE FROM record WHERE Domain = ? and IP = ?";
			$stmt = mysqli_prepare($db, $delete_query);
			$stmt->bind_param("ss", $old_fqdn, $old_ip);
			$stmt->execute();

			$command = escapeshellcmd('./site-delete-record.py ' . $old_fqdn . " " . $draw_this_zone . " " . $get_data_type);
			shell_exec($command);
			 
			echo "<h2 class='logged'> Deleted Record! </h2>";
		}
		
		$draw_zones = FALSE;
		$draw_add_records = FALSE;
		$draw_lookup = FALSE;
		$draw_records = FALSE;
		$draw_all_records = FALSE;
		$logged_in= TRUE;
		$username = $_POST['username'];
		
	} elseif ($formAction == 'lookup-record' && isset($_POST['submit'])) {
		$logged_in = TRUE;
		$username = $_POST['username'];
		$draw_this_zone = $_POST['submit'];
		$draw_add_records = FALSE;
		$draw_records = FALSE;
		$draw_zones = FALSE;
		$draw_lookup = FALSE;
		$draw_all_records = FALSE;
		
		//Perform lookup using external python script
		$value_to_lookup = $_POST['lookup'];

		$command = escapeshellcmd('./site-lookup.py ' . $value_to_lookup);
		shell_exec($command);
		
		$file = file('/usr/local/www/access/lookup_result.txt');
		
		foreach ($file as $line) {
			echo "<h2 class='logged'>" . $line . "</h2>";
		}


	} elseif ($formAction == "go-home" && isset($_POST['submit'])) {
		$logged_in = TRUE;
		$username = $_POST['username'];

		$draw_add_records = FALSE;
		$draw_records = FALSE;
		$draw_zones = FALSE;
		$draw_lookup = FALSE;
		$draw_all_records = FALSE;
	}
	
	//Create Login form when user not logged in
	if ($logged_in == FALSE) {
		echo "<form method = 'POST' action = " . htmlspecialchars($_SERVER['PHP_SELF']) . ">"; 
		echo "<h1>Login</h1>";
		echo "<table>";
		echo "<tr>";
		echo "<td>Username: </td>";
		echo "<td class='clean'><input type = 'text' name = 'username' required></td>";
		echo "</tr>";
		echo "<tr>";
		echo "<td>Password: </td>";
		echo "<td><input type = 'password' name = 'password' required>";
		echo "</td>";
		echo "</tr>";
		echo "</table>";
		//send saved data
		echo "<input type='hidden' name='form' value='login'>";
		echo "<input type = 'submit' name = 'submit' value = 'Login'>";
		echo "</form>";
	} else { //If logged_in == true
	
		//Draw all the Zones. When no other option is selected.
		if (($draw_zones == FALSE) && ($draw_records == FALSE) && ($draw_add_records == FALSE) && ($draw_lookup == FALSE) && ($draw_all_records == FALSE)) {
			//Define Table header for zones
			echo "<form method='POST' action= " . htmlspecialchars($_SERVER['PHP_SELF']) . " id='zones-form'";
			echo "<div class='container'>";
			echo "<h2>Zones</h2>";
			echo "<table class='table table-striped'>";
			echo "<thead>";
			echo "<tr>";
			echo "<th>Zone Named</th>";
			echo "<th>Edit Zone</th>";
			echo "</tr>";
			echo "</thead>";

			//Iterate through query from 'Zones table' and print a Table row
			$query_zones = "SELECT * FROM zone WHERE parentUser = '$username'";
			$result_zones = mysqli_query($db, $query_zones);
			
			while($row = mysqli_fetch_assoc($result_zones)) {
				echo "<tr>";
				echo "<td>" . $row['name'] . "</td>";
				echo "<td> <input type='submit' name='submit' value='" . $row['name'] . "'/></td>";
				echo "</tr>";
			}
			
			echo "</table>";
			echo "</div>";
			//send saved data
			echo "<input type='hidden' name='username' value='" . $username . "'>";
			echo "<input type='hidden' name='form' value='record'>";
			echo "<input type='submit' name='submit' class='gray-btn' value='Perform Lookup'/>";
			echo "</form>";
		}
		
		//Draw a specific zone when clicked. Display all records
		if ($draw_zones) {
			echo "<form method='POST' action= " . htmlspecialchars($_SERVER['PHP_SELF']) . " id='zones-form'";
			echo "<div class='container'>";
			echo "<h2> Zone: " . $draw_this_zone . "</h2>";
			echo "<table class='table table-striped'>";
			echo "<thead>";
			echo "<tr>";
			echo "<th>Sub-Domain</th>";
			echo "<th>IP</th>";
			echo "<th>DataType</th>";
			echo "<th>Edit Record</th>";
			echo "</tr>";
			echo "</thead>";
			
			//Iterate through query from 'Zones table' and print all records
			$query_records = "SELECT * FROM record WHERE parentZone = '$draw_this_zone'";
			$result_records = mysqli_query($db, $query_records);
			
			while($row = mysqli_fetch_assoc($result_records)) {
				$domain = $row['Domain']; $ip = $row['IP']; $datatype = $row['DataType'];
				echo "<tr>";
				echo "<td>" . $domain . "</td>";
				echo "<td>" . $ip . "</td>";
				echo "<td>" . $datatype . "</td>";
				echo "<input type='hidden' name='" . $domain . "' value='" . $ip . "'/>";
				echo "<td> <input type='submit' name='submit' value='" . $domain . "'/></td>";
				echo "<td> <input type='hidden' name='data_type_of_" . $domain . "' value='" . $datatype . "'> </td>";
				echo "</tr>";
			}
			
			echo "</table>";
			echo "</div>";
			//send saved data
			echo "<input type='hidden' name='parent' value='" . $draw_this_zone . "'>";
			echo "<input type='hidden' name='username' value='" . $username . "'>";
			echo "<input type='hidden' name='form' value='add-record'>";

			//other submit buttons, redirects to different webpages
			echo "<td> <input type='submit' name='submit' value='ADD RECORD'/></td>";
			echo "<input type='submit' name='submit' class='gray-btn' value='PRINT ALL RECORDS'/>";
			echo "</form>";
		}
		
		//Add Record page
		if ($draw_add_records) {
			echo "<form method = 'POST' action = " . htmlspecialchars($_SERVER['PHP_SELF']) . ">"; 
			echo "<h1>ADD RECORD!</h1>";
			echo "<table>";
			echo "<tr>";
			echo "<td>DataType:</td>";
			echo "<td>";
			echo "<select name='data_type'>";
			echo "<option value='A'>A</option>";
			echo "<option value='CNAME'>CNAME</option>";
			echo "<option value='MX'>MX</option>";
			echo "</select>";
			echo "</td>";
			echo "</tr>";
			echo "<tr>";
			echo "<td>Sub-domain:</td>";
			echo "<td><input type = 'text' name = 'fqdn' required></td>";
			echo "</tr>";
			echo "<tr>";
			echo "<td>IP: </td>";
			echo "<td><input type = 'text' name = 'ip' required>";
			echo "</td>";
			echo "</tr>";
			echo "</table>";
			//send saved data
			echo "<input type='hidden' name='username' value='" . $username . "'>";
			echo "<input type='hidden' name='parent' value='" . $draw_this_zone . "'>";
			echo "<input type='hidden' name='form' value='completed-adding-record'>";
			echo "<input type = 'submit' name = 'submit' value = 'ADD RECORD'>";
			echo "</form>";
		}
		
		//Update records page
		//Allows user to either update a record or delete it
		if ($draw_records) {


			echo "<form method='POST' action= " . htmlspecialchars($_SERVER['PHP_SELF']) . " id='zones-form'";
			echo "<div class='container'>";
			echo "<h2> Zone: Update Record!</h2>";
			echo "<table class='table table-striped'>";
			echo "<thead>";
			echo "<tr>";
			echo "<th>Sub-Domain</th>";
			echo "<th>IP</th>";
			echo "</tr>";
			echo "</thead>";
			echo "<tr>";
			echo "<td> <input type='text' name='new-fqdn' value='" . $update_domain . "'/> </td>";
			echo "<td> <input type='text' name='new-ip' value='" . $update_ip . "' /> </td>";
			echo "</tr>";
			echo "</table>";
			echo "</div>";
			//send saved data
			echo "<input type='hidden' name='parent' value='" . $update_parent . "'>";
			echo "<input type='hidden' name='username' value='" . $username . "'>";
			echo "<input type='hidden' name='original_fqdn' value='" . $update_domain . "'>";
			echo "<input type='hidden' name='original_data_type' value='" . $update_datatype . "'>";
			echo "<input type='hidden' name='original_ip' value='" . $update_ip . "'>";
			echo "<input type='hidden' name='form' value='update-current-record'>";
			echo "<td> <input type='submit' name='submit' value='UPDATE RECORD'/></td>";
			echo "<td> <input type='submit' name='submit' id='delete-btn' value='DELETE RECORD'/></td>";
			echo "</form>";
		}
	}
	
	//Drawing lookup form, allow user to lookup a specific hostname
	if ($draw_lookup) {
		echo "<form method='POST' action= " . htmlspecialchars($_SERVER['PHP_SELF']) . " id='zones-form'";
		echo "<div class='container'>";
		echo "<h2> Perform Lookup </h2>";
		echo "<table class='table table-striped'>";
		echo "<thead>";
		echo "<tr>";
		echo "<th>Domain</th>";
		echo "</tr>";
		echo "</thead>";
		echo "<tr>";
		echo "<td> <input type='text' name='lookup' placeholder='eeyore.bigbrick.com'/> </td>";
		echo "</tr>";
		echo "</table>";
		echo "</div>";
		//send saved data
		echo "<input type='hidden' name='username' value='" . $username . "'>";
		echo "<input type='hidden' name='form' value='lookup-record'>";
		echo "<td> <input type='submit' name='submit' value='Perform Lookup'/></td>";
		echo "</form>";
	}

	if ($draw_all_records) {
		echo "<form method='POST' action= " . htmlspecialchars($_SERVER['PHP_SELF']) . " id='zones-form'";
		echo "<div class='container'>";
		
		//output all records
		foreach ($file as $line) {
			echo $line . "<br>";
		}

		echo "</div>";
		//send saved data
		echo "<input type='hidden' name='username' value='" . $username . "'>";
		echo "<input type='hidden' name='form' value='go-home'>";
		echo "<td> <input type='submit' name='submit' value='Go Home'/></td>";
		echo "</form>";

	}

	
?>
	</body>
</html>