##!$r3_path
# set the current folder to the work folder, just to be sure.
setwd("$loc")
# load saved environement
load(".RData")
saving_libpath <- .libPaths()

$full_script_code

.libPaths(saving_libpath)
# saves the environnement
save.image()
