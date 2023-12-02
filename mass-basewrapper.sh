#!/bin/bash

conf_file_name="mass-baseline.conf"
conf_file_default="mass-baseline-default.conf"
progress_file_name="mass-progress.conf"
date=`date +%F-%H-%M-%S`

### mass-baseline.sh call parameters
###   $1  - Dir to save result file to in '/zap/wrk' dir, e.g.: 'r_<work-dir-slug>'
###   $2  - Target url, like 'www.example.com'. With '$3' forms target for './zap-baseline.py' as '-t https://$2$3'
###   $3  - URL path, like '/' or a longer path if required. With '$2' forms target for './zap-baseline.py' as '-t https://$2$3'
###   $4  - List of emails separated by commas or 'null' if there is no need to send notifications
###   $5  - (Optional) Link to form friendly URL for target. Required if EXTRA is used
###   $6+ - (Optional) EXTRA params to pass on to './zap-baseline.py'
### example:
###   ./mass-basewrapper.sh r_mytseOSqv3WfUqZ1jCatVD8OgaTqsC9J9P30C4SS example.com / security@example.com,infosec@example.com https://example.com

# echo -e "== log: [$0] called as:\n>>>>>>: $0 ${@}"

if test -d '/zap/wrk/' ; then

  progress_file="/zap/wrk/$1/$progress_file_name"
  test ! -s $progress_file || with_progress_file="-p $progress_file"

  conf_file="/zap/wrk/$1/$conf_file_name"
  test -s $conf_file || conf_file="/zap/wrk/$conf_file_default"

  if test -s $conf_file ; then
    test -d /zap/wrk/$1/data || mkdir /zap/wrk/$1/data

    if test ! -s /zap/wrk/$1/data/$date.md ; then
      cmd="./zap-baseline.py -t https://$2$3 -d -c ${conf_file##/zap/wrk/} $with_progress_file \"${@:6} \""

      echo -e "== log: [$0] run:\n>>>>>>: $cmd > /zap/wrk/$1/data/$date.tmp"
      $cmd > /zap/wrk/$1/data/$date.tmp

      # ensure ZAP has completely shut down, otherwise it can corrupt the DB of the next run
      sleep 10

      if test -s /zap/wrk/$1/data/$date.tmp ; then
        cat > /zap/wrk/$1/data/$date.md <<- _EOF
		Alert Id | Description | Status | Status Tag
		---------|-------------|--------|----------
		$(cat /zap/wrk/$1/data/$date.tmp | \
		  sed -e 's%^\([^: ]\+\): \([^[]\+\) \[\([0-9]\+\)\].*%🔴|\1|[\3](https://www.zaproxy.org/docs/alerts/\3/)|\2%' | \
		  grep "^🔴" | \
		  grep -v "^🔴|PASS" | \
		  sed -e 's/^🔴|IGNORE/🟢|IGNORE/' | \
		  sed -e 's/^🔴|FAIL-IN_PROGRESS/🟢|FAIL-IN_PROGRESS/' | \
		  sed -e 's/^🔴|WARN-IN_PROGRESS/🟢|WARN-IN_PROGRESS/' | \
		  awk -F"|" '{printf("%s | %s | %s | %s\n",$3,$4,$1,$2);}' | \
		  sort -t "|" -k1)

		<details>

		<summary><b>Raw Report</b> - click to open/close</summary>

		\`\`\`
		DATE: $date
		TARGET: https://$2$3
		EMAILS: $4
		LINK: $5
		EXTRA: ${@:6}
		CONFIG: ${conf_file##/zap/wrk/}

		$(cat /zap/wrk/$1/data/$date.tmp)
		\`\`\`

		</details>
		_EOF
      else
        echo "== wrn: the command (./zap-baseline.py) output for site ($2$3) is empty"
      fi
      rm /zap/wrk/$1/data/$date.tmp
    else
      echo "== log: file (/zap/wrk/$1/data/$date.md) exists and not empty; skiping"
    fi

  else
    echo "== wrn: no baseline configuration file present for site ($2$3); skiping"
    echo "======: place it in the report dir (as /zap/wrk/$1/$conf_file_name) or in the 'wrk' dir (as /zap/wrk/$conf_file_default)"
  fi

else
  echo "== err: no 'wrk' dir (/zap/wrk/) mounted into container; skiping"
fi

# echo "== log: [$0] finished"
