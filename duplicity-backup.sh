#!/bin/bash

SOURCES="/home/HET2.git \
         /home/AUXIL_SOURCES.git \
         /home/hetdex/Wiki \
         /home/hetdex/foswiki \
         /var/lib/jenkins/jobs/HET2_build/config.xml \
         /var/lib/jenkins/jobs/HET2_Build_Then_Test/config.xml \
         /etc/sysconfig/jenkins"

DESTINATIONS="file:///media/HETDEX_BACK/duplicity \
              s3+http://HETDEX"

SECRETS=/etc/cron.daily/secrets
GPGKEY=1DB0E000

EMAILS="moreira@astro.as.utexas.edu"

# ---- end of config

export LANG=en_US.UTF8
DUPLICITY="duplicity --archive-dir $SECRETS/.cache/duplicity"
export PASSPHRASE=$(cat $SECRETS/passphrase)
export AWS_ACCESS_KEY_ID=$(cat $SECRETS/accesskey)
export AWS_SECRET_ACCESS_KEY=$(cat $SECRETS/secretaccesskey)

function backup {

    INCLUDE=$(for src in $SOURCES; do echo "--include $src"; done)
    GPG_OPTIONS="--encrypt-key $GPGKEY"

    for DEST in $DESTINATIONS; do
        ( (echo ;
            echo "************************";
            echo "* $(date)";
            echo "************************";
            echo "Sending to $DEST...";
            $DUPLICITY $GPG_OPTIONS --full-if-older-than 30D $INCLUDE --exclude '**' / $DEST;
            echo "Removing old backups from $DEST...";
            $DUPLICITY $GPG_OPTIONS remove-older-than 30D --force $DEST) >> /var/log/duplicity.log ) 2>&1 | $PYTHON $SENDMAIL -f hetdex@hetdex-pr.as.utexas.edu -t $EMAILS;
    done

}

function restore {
    export AWS_ACCESS_KEY_ID=$(cat $SECRETS/accesskey)
    export AWS_SECRET_ACCESS_KEY=$(cat $SECRETS/secretaccesskey)

    export GNUPGHOME=/etc/gnupg/.gnupg
    GPG_OPTIONS='--sign-key C3B3CCAD --encrypt-key 2E29335A'

    $DUPLICITY $GPG_OPTIONS $1 ./HET2_restore;

    export AWS_ACCESS_KEY_ID=
    export AWS_SECRET_ACCESS_KEY=
}

function check_destination {
    export AWS_ACCESS_KEY_ID=$(cat $SECRETS/accesskey)
    export AWS_SECRET_ACCESS_KEY=$(cat $SECRETS/secretaccesskey)

    export GNUPGHOME=/etc/gnupg/.gnupg
    GPG_OPTIONS='--sign-key C3B3CCAD --encrypt-key 2E29335A'

    $DUPLICITY $GPG_OPTIONS collection-status $1;

    export AWS_ACCESS_KEY_ID=
    export AWS_SECRET_ACCESS_KEY=
}

function raw_duplicity {
    export AWS_ACCESS_KEY_ID=$(cat $SECRETS/accesskey)
    export AWS_SECRET_ACCESS_KEY=$(cat $SECRETS/secretaccesskey)

    export GNUPGHOME=/etc/gnupg/.gnupg
    GPG_OPTIONS='--sign-key C3B3CCAD --encrypt-key 2E29335A'

    shift;
    $DUPLICITY $GPG_OPTIONS $*;

    export AWS_ACCESS_KEY_ID=
    export AWS_SECRET_ACCESS_KEY=
}

function list_destinations {
    for DEST in $DESTINATIONS; do
        echo $DEST;
    done
}

function usage {
    cat <<EOF
${red}usage${rst}: $0 [options]

HET2 Backup Utility.

With no options, just assume -b (backup).

${blu}OPTIONS:${rst}
 ${grn}-h${rst}       Show this message
 ${grn}-l${rst}       List all possible destinations
 ${grn}-c dest${rst}  Check status of backup on a given destination
 ${grn}-r dest${rst}  Restore from a given destination to the directory ./HET2_restore
 ${grn}-d cmds${rst}  Pass raw commands to duplicity
 ${grn}-b${rst}       Backup to all destinations
 ${grn}-f${rst}       Force full backup to all destinations
EOF
}

if [ ! $TERM ]; then
    $TERM="xterm-color";
fi

# Text color variables
und=$(tput -T$TERM sgr 0 1)    # Underline
bld=$(tput -T$TERM bold)       # Bold
red=$(tput -T$TERM setaf 1)    # Red
grn=$(tput -T$TERM setaf 2)    # Green
ylw=$(tput -T$TERM setaf 3)    # Yellow
blu=$(tput -T$TERM setaf 4)    # Blue
pur=$(tput -T$TERM setaf 5)    # Purple
cyn=$(tput -T$TERM setaf 6)    # Cyan
wht=$(tput -T$TERM setaf 7)    # White
rst=$(tput -T$TERM sgr0)       # Text reset

set -e

while getopts 'lc:r:bfhd' OPTION
do
    case $OPTION in
        l)
            list_destinations;
            exit 0;
            ;;
        c)
            check_destination $OPTARG;
            exit 0;
            ;;
        r)
            restore $OPTARG;
            exit 0;
            ;;
        b)
            backup regular;
            exit 0;
            ;;
        f)
            backup full;
            exit 0;
            ;;
        d)
            raw_duplicity $*;
	    exit 0;
            ;;
        ?|h)
            usage
            exit 1
            ;;
    esac
done

backup regular;

export PASSPHRASE=
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=

exit 0;
