#!$r3_path
# set the current folder to the work folder, just to be sure.
setwd("$loc")
# load saved environement
load(".RData")

$full_script_code
##### END OF TAG #####

# saves the environnement
save.image()
