# Scanning multiple web sites with OWASP `ZAP Mass Baseline` and serving result reports as markdown with `Caddy`

* Here we have scripts to run OWASP [ZAP Baseline Scanning](https://www.zaproxy.org/docs/docker/baseline-scan/) against a series of target URLs
* The list of target URLs is maintained as markdown file (`mailings.md`) served with help of [Caddy](https://caddyserver.com/)
* The results of scanning are stored as markdown files and also served with help of Caddy

## Prerequisites

### `Caddy` container configuration and static data

* See Caddy container configuration and static data in `caddy/{etc,data}`
* Copy the directory `caddy` with its content to `/srv/docker/`. As a result you should have `/srv/docker/caddy/{etc,data}` directory structures
* There should be a directory `/srv/docker/caddy/data/src/reports/markdown/m_<ID>` with file `mailings.md` containing a list of target URLs to scan
* Edit the mentioned file (`mailings.md`) to add your targets according to its structure
* The following is an example of `mailings.md` content. Lines which start with `🟢` symbol are parsed. Fields of columns **Site**, **Report URL**, and **Notification Emails** are extracted and used to scan targets and store the results

```
On/Off | Site | HTTP Req Status | HTTPS Req Status | Report URL | Notification Emails
------ | ---- | --------------- | ---------------- | ---------- | -------------------
🟢 | [example.com](https://example.com) |` 301 => https://example.com/ `|` 200 `| [show...](/reports/r_mytseOSqv3WfUqZ1jCatVD8OgaTqsC9J9P30C4SS/example.com_history) |security@example.com
🔴 | [www.example.com](https://www.example.com) |` ❗ no DNS record `|` ❗ no DNS record `| - | -
```

* The name of the directory where the mentioned file located (`m_<ID>`) contains the ID passed thereafter to the OWASP **ZAP Mass Baseline** container (its `mass-baseline` command)
* In the following example the ID is `wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x`, and the directory name is `m_wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x`

```
/srv/docker/caddy/data/src/reports/markdown/m_wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x/mailings.md
```

* Edit `Caddyfile` (located at `/srv/docker/caddy/etc/Caddyfile`) to correct web server `hostname:port` according to your configuration

```
example.com:80 # => replace to your web server name, port

root * /srv/src

file_server
templates
encode gzip

try_files {path}.html {path}

redir   /reports          /
redir   /reports/         /
rewrite /reports/*        /reports/index.html

...
```

### `Caddy` container deployment

* Run Caddy container with the following command

```
docker run --rm -d --name caddy -p 80:80 \
  -v /srv/docker/caddy/etc/Caddyfile:/etc/caddy/Caddyfile \
  -v /srv/docker/caddy/data/src/:/srv/src \
  caddy
```

* You can specify the following environment variables, to be different of their following default values, with `-e` flag

```
EMAIL_ADDR_CONTACT=contact@example.com # contact email address used on index page
```

* For examplle, to specify a contact email address used on index page use the following command

```
docker run --rm -d --name caddy -p 80:80 \
  -e "EMAIL_ADDR_CONTACT=infosec@example.com" \
  -v /srv/docker/caddy/etc/Caddyfile:/etc/caddy/Caddyfile \
  -v /srv/docker/caddy/data/src/:/srv/src \
  caddy
```

## OWASP `ZAP Mass Baseline` usage

### Build OWASP `ZAP Mass Baseline` container image

* To build local OWASP **ZAP Mass Baseline** container image run the following command
 
```
docker build -t local/mass-baseline .
```

### Run OWASP `ZAP Mass Baseline` container

* To scan target URLs maintained in `mailings.md` file of the corresponding directory run the following command (where `wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x` is the ID of the directory of name `m_<ID>` with `mailings.md` file)

```
docker run --rm -d --name mass-baseline -u zap \
  -v /srv/docker/caddy/data/src/reports/markdown:/zap/wrk/:rw \
  local/mass-baseline mass-baseline.sh wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x
```

* You can specify the following environment variables, to be different of their following default values, with `-e` flag

```
EMAIL_ADDR_FROM=noreply@example.com # email address from which email notifications will be sent
SMTP_HOST=example.com               # SMTP host used to send email notifications
SMTP_PORT=25                        # port on SMTP host used to send email notifications
HTTP_SCHEME=http                    # HTTP scheme used to form HTTP URLs
HTTP_DOMAIN=example.com             # HTTP domain used to form HTTP URLs
```

* For examplle, to specify an email address from which email notifications will be sent use the following command

```
docker run --rm -d --name mass-baseline -u zap \
  -e "EMAIL_ADDR_FROM=infosec@example.com" \
  -v /srv/docker/caddy/data/src/reports/markdown:/zap/wrk/:rw \
  local/mass-baseline mass-baseline.sh wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x
```

* OWASP **ZAP Mass Baseline** container stores scanning results to the directories `/r_*` under `/srv/docker/caddy/data/src/reports/markdown`, where particular directories' names are specified in `mailings.md` file

### Access result reports (and list of target URLs)

* The following URLs can be used to access result reports and list of target URLs (here is the ID `wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x` which corresponds to the described above directory structure)
  * `http://example.com/reports/m_wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x/baseline-summary` - result reports, available as OWASP **ZAP Mass Baseline** container finishes
  * `http://example.com/reports/m_wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x/mailings` - list of configured target URLs

## Automation

### Use `make`

* You can create the following `Makefile` to help with deployment automation

```
all: none

none:
	echo This is general Makefile, create specific one for build and deploy using this file as an example

build:
	docker build -t local/mass-baseline .

run: caddy
	docker run --rm -d --name mass-baseline -u zap -e "EMAIL_ADDR_FROM=xxx@xxxx.xx" -e "SMTP_HOST=xxxxx.xxx" -e "SMTP_PORT=25" -e "HTTP_SCHEME=http" -e "HTTP_DOMAIN=xxxxxxxx.xxx" -v /srv/docker/caddy/data/src/reports/markdown:/zap/wrk/:rw local/mass-baseline mass-baseline.sh wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x

caddy: caddy_mount
	test -n "`docker ps -a -q -f name=caddy -f status=running`" || docker run --rm -d -e "EMAIL_ADDR_CONTACT=xxx@xxxx.xx" --name caddy -p 80:80 -v /srv/docker/caddy/etc/Caddyfile:/etc/caddy/Caddyfile -v /srv/docker/caddy/data/src/:/srv/src caddy

caddy_mount:
	test -d /srv/docker || sudo mkdir -p /srv/docker
	test -d /srv/docker/caddy || test ! -d caddy || sudo cp -p -r caddy /srv/docker/
	test -d /srv/docker/caddy/etc || echo "no /srv/docker/caddy/etc directory found, running container will fail" || false
	test -d /srv/docker/caddy/data || echo "no /srv/docker/caddy/data directory found, running container will fail" || false

caddy_clear:
	test ! -n "`docker ps -a -q -f name=caddy -f status=running`" || docker stop caddy
	sudo mv /srv/docker/caddy /srv/docker/caddy-`date +%F-%s`

cron_install:
	{ echo '49 3 * * 3 docker run --rm -d --name mass-baseline -u zap -e "EMAIL_ADDR_FROM=xxx@xxxx.xx" -e "SMTP_HOST=xxxxx.xxx" -e "SMTP_PORT=25" -e "HTTP_SCHEME=http" -e "HTTP_DOMAIN=xxxxxxxx.xxx" -v /srv/docker/caddy/data/src/reports/markdown:/zap/wrk/:rw local/mass-baseline mass-baseline.sh wiho6vrjbt68gemclnfj9we4azv8eobfrfcfv34x' ; crontab -l | grep -v "^#" ; } | crontab -

cron_show:
	crontab -l | grep -v "^#"
```

* Using the above `Makefile` you can follow the below steps to build and deploy the project
  * `git clone https://github.com/cloud-simple/zap-mass-docker`
  * `cd zap-mass-docker`
  * `vi caddy/data/src/reports/markdown/m_*/mailings.md` # change the list of target URLs according to your setup
  * `vi caddy/etc/Caddyfile` # change web server name and port according to your setup
  * `vi Makefile` # use the content of the above example and change values for environment variables and crontab fields according to your setup
  * `make build`
  * `make run`
  * `make cron_install`
  
## Details for template variables in `caddy/data/src/reports/index.html` file

See [example](https://github.com/caddyserver/website/blob/master/src/docs/index.html)

* `$pathParts`: `[ reports r_test01abcdefgh site.example.com_history]`
* `$markdownFilename`: `r_test01abcdefgh/site.example.com_history`
* `$markdownFile`: `{map[] #### site.example.com | Site | Status | Pass | Warn | Fail | Date | | ---- | ------ | ---- | ---- | ---- | ---- | | [site.example.com](https://site.example.com)| [![Score](https://img.shields.io/badge/baseline-fail%202-red.svg)](/reports/r_test01abcdefgh/data/2023-12-02-20-44-32)| 50 | 10 | 2| [2023-12-02-20-44-32](/reports/r_test01abcdefgh/data/2023-12-02-20-44-32) | | [site.example.com](https://site.example.com)| [![Score](https://img.shields.io/badge/baseline-fail%202-red.svg)](/reports/r_test01abcdefgh/data/2023-12-02-20-12-27)| 50 | 10 | 2| [2023-12-02-20-12-27](/reports/r_test01abcdefgh/data/2023-12-02-20-12-27) | }`
* `$title`: `r_test01abcdefgh/data/2023-12-02-20-44-32`
