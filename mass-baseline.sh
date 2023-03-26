#!/bin/bash

mail_file_name="mailings.md"

### mass-baseline.sh call parameters
###   $1  - <work-dir-slug> # dir 'm_<work-dir-slug>' should contain 'mailings.md' file
### example:
###   ./mass-baseline.sh wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x

# echo -e "== log: [$0] called as:\n>>>>>>: $0 ${@}"

test -n "$1" || { echo "== err: the 1-st arg is empty, should be slug of working directory; exiting" ; exit -1 ; }
test -d "/zap/wrk/m_$1" || { echo "== err: no directory present (/zap/wrk/m_$1) for the specified slug dir; exiting" ; exit -1 ; }
test -s "/zap/wrk/m_$1/$mail_file_name" || { echo "== err: no file present (/zap/wrk/m_$1/$mail_file_name) in the specified slug dir; exiting" ; exit -1 ; }

list_dir="/zap/wrk/m_$1"
list_file="/zap/wrk/m_$1/$mail_file_name"

rm -fr $list_dir/*_history.md

awk -F"|" '/^🟢/ {
  line=$0

  gsub(/.*\[/, "", $2)
  gsub(/\].*/, "", $2)
  if($2 !~ /^(([a-zA-Z0-9][a-zA-Z0-9]?)|([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]))(\.(([a-zA-Z0-9][a-zA-Z0-9]?)|([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9])))*$/) {
    printf "== wrn: parsed site value is not valid domain name:\n>>>>>>: %s\n======: skiping\n", line > "/dev/stderr"
    fflush("/dev/stderr")
    next
  }

  gsub(/.*\(\/reports\/r_/, "r_", $5)
  gsub(/\).*/, ".md", $5)
  if($5 !~ /^r_[0-9a-zA-Z]+\/[^\/]+$/) {
    printf "== wrn: parsed file_path value is not valid path:\n>>>>>>: %s\n======: skiping\n", line > "/dev/stderr"
    fflush("/dev/stderr")
    next
  }

  gsub(/ /, "", $6)
  if (length($6) == 0 || $6 == "-") {
    emails="null"
  } else {
    emails=$6
  }

  printf("%s:%s=%s\n", $2, $5, emails)
}' $list_file | \
while read line ; do
  site=${line%%:*}
  file_emails=${line##*:}
  file=${file_emails%%=*}
  emails=${file_emails##*=}

  dir=$(dirname "$file")
  test ! -d /zap/wrk/$dir && mkdir /zap/wrk/$dir
  ./mass-basewrapper.sh $dir $site / $emails https://$site

  touch /zap/wrk/$file
  ( cd $list_dir/ ; ln -s ../$file ./ ; )
done

./mass-basescore.py $list_dir

# echo "== log: [$0] finished"
