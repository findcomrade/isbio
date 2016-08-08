##### TAG: $tag_name #####

# This script is to be run explicitly in R3
# special R3 bootstrap
if(R.Version()$$major < 3){
	# saving environement	
	save.image()
	# lauching sub-script
	print("Running $tag_name from R3...")
	#system('$sub_script_path')
	system('$r3_path $r3_cmd $sub_script_path')
	print("DONE !")
	# restoring modified environement
	load(".RData")
}else{ # normal execution if current version of R is already R3
	$full_script_code
}
