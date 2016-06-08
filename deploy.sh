#!/bin/bash

CLEAN_GIT="nothing to commit, working directory clean"
SELF=`md5sum deploy.sh`
HOST_NAME=`hostname`
END_C='\033[39m'
BLUE='\033[34m'
RED='\033[31m'
YELLOW='\033[33m'
CYAN='\033[36m'

version=$(<.version)
((version++))
echo ${version}>.version

if [ "$HOST_NAME" = breeze.giu.fi ]; then
	echo "${BLUE}ON PROD (${HOST_NAME})${END_C}"
	ENVIRONMENT='production'
	echo "${CYAN}git status${END_C}"
	git status
	echo "${CYAN}git checkout${END_C}"
	git checkout
	if [ $(git checkout|tail -n1) != "$CLEAN_GIT" ];
	then
		echo "${RED}WARNING:${END_C} Non committed local changes will be discarded."
		read -p "Are you sure you want to proceed (y/n) ?" -n 1 -r
		echo # move to a new line
		if [[ $REPLY =~ ^[Yy]$ ]];
		then
			echo "discarding any local changes..."
		    git status|egrep "modified:|added:|deleted:|renamed:"|awk '{print "\033[36mgit checkout -- "$2"\033[39m"; system("git checkout -- "$2)}' # discard any local changes
		    echo "done !"
		else
			exit 0
		fi
    fi
    if [ $(git checkout|tail -n1) != "$CLEAN_GIT" ];
	then
		echo "${RED}ERROR:${END_C} ambiguous git status, please check git co manually !"
		exit 1
    fi
	echo "${CYAN}git pull${END_C}"
	git pull
else
	if [ "$HOST_NAME" = breeze-dev.giu.fi ]; then
		echo "${BLUE}ON DEV (${HOST_NAME})${END_C}"
		ENVIRONMENT='development'
	fi
fi

NEW_SELF=`md5sum deploy.sh`
if [ "$NEW_SELF" != "$SELF" ]; then
	echo "${BLUE}Deploy script has been changed${END_C}, re-starting..."
	./deploy.sh &
	exit $?
fi

ACCESS_TOKEN=00f2bf2c84ce40aa96842622c6ffe97d
LOCAL_USERNAME=`whoami`
REVISION=`git log -n 1 --pretty=format:"%H"`
echo "${BLUE}Registering deploy version "${version}", git "${REVISION}" ...${END_C}"

curl https://api.rollbar.com/api/1/deploy/ \
  -F access_token=${ACCESS_TOKEN} \
  -F environment=${ENVIRONMENT} \
  -F revision=${REVISION} \
  -F local_username=${LOCAL_USERNAME}

echo
killall autorun.sh > /dev/null 2>&1
killall autorun_sub.sh > /dev/null 2>&1
echo "Reloading BREEZE..."
./autorun.sh &
