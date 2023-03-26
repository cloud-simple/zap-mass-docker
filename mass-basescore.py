#!/usr/bin/python

from __future__ import print_function
import os
import re
import sys
import traceback

import smtplib
from email.message import EmailMessage

######### ######### ######### ######### ######### ######### ######### ######### ######### 
env_email_addr_from = os.getenv('EMAIL_ADDR_FROM', 'noreply@example.com')
env_smtp_host       = os.getenv('SMTP_HOST', 'example.com')
env_smtp_port       = os.getenv('SMTP_PORT', '25')
env_http_scheme     = os.getenv('HTTP_SCHEME', 'http')
env_http_domain     = os.getenv('HTTP_DOMAIN', 'example.com')

######### ######### ######### ######### ######### ######### ######### ######### ######### 
def sent_notification (emails, subject, text):
  
  msg = EmailMessage()
  msg.set_content(text)
  msg['Subject'] = subject
  msg['From'] = env_email_addr_from
  msg['To'] = ", ".join(emails.split(','))
  
  s = smtplib.SMTP(env_smtp_host + ':' + env_smtp_port)
  s.send_message(msg)
  s.quit()

######### ######### ######### ######### ######### ######### ######### ######### ######### 
def parse_results (site, date_file_name, is_summary_file, file_w, history_file_name):
  schema_host_name = env_http_scheme + '://' + env_http_domain
  date = os.path.basename(date_file_name).removesuffix(".md")

  # print ("== log (parse_results): site: " + site + " | date: " + date + " | date_file_name: " + date_file_name + " | summary: " + str(is_summary_file) + " | history_file_name: " + history_file_name)

  date_file_link = '/reports/' + os.path.basename(os.path.dirname(os.path.dirname(date_file_name))) + '/data/' + os.path.basename(date_file_name).removesuffix(".md")
  history_file_link = '/reports/' + os.path.basename(os.path.dirname(history_file_name)) + '/' + os.path.basename(history_file_name).removesuffix(".md")

  link = ''
  email = ''
  ok = ''
  fail = ''
  warn = ''

  re_res_weekly = re.compile(r'^FAIL-NEW: (\d+)\tFAIL-INPROG: (\d+)\tWARN-NEW: (\d+)\tWARN-INPROG: (\d+)\tINFO: (\d+)\tIGNORE: (\d+)\tPASS: (\d+)')
  re_res_other = re.compile(r'^FAIL: (\d+)\tWARN: (\d+)\tINFO: (\d+)\tIGNORE: (\d+)\tPASS: (\d+)')
  re_link = re.compile(r'^LINK: (\S+)')
  re_emails = re.compile(r'^EMAILS: (\S+)')

  with open(date_file_name, 'r') as f:
    for line in f:
      if bool(re_res_weekly.search(line)):
        scores = re_res_weekly.findall(line)
        if len(scores) == 1:
          ok = scores[0][6]
          fail = str(int(scores[0][0]) + int(scores[0][1]))
          warn = str(int(scores[0][2]) + int(scores[0][3]))
        continue

      if bool(re_res_other.search(line)):
        scores = re_res_other.findall(line)
        if len(scores) == 1:
          ok = scores[0][4]
          fail = scores[0][0]
          warn = scores[0][1]
        continue

      if bool(re_link.search(line)):
        links = re_link.findall(line)
        if len(links) == 1:
          link = links[0]
        continue

      if bool(re_emails.search(line)):
        emails = re_emails.findall(line)
        if len(emails) == 1:
          email = emails[0]
        continue

    ### for end ###

    try:
      if len(link) > 0:
        file_w.write ('| [' + site + '](' + link + ')')
      else:
        file_w.write ('| ' + site)
        
      if len(ok) > 0:
        if int(fail) > 0:
          file_w.write ('| [![Score](https://img.shields.io/badge/baseline-fail%20' + fail + '-red.svg)]')
        elif int(warn) > 0:
          file_w.write ('| [![Score](https://img.shields.io/badge/baseline-warn%20' + warn + '-yellow.svg)]')
        else:
          file_w.write ('| [![Score](https://img.shields.io/badge/baseline-pass-green.svg)]')
      else:
        file_w.write ('| [N/A]')

      file_w.write ('(' + date_file_link + ')')

      if len(ok) > 0:
        file_w.write ('| ' + ok + ' | ' + warn + ' | ' + fail)
      else:
        file_w.write ('| N/A | N/A | N/A')

      if is_summary_file:
        file_w.write ('| [' + date + '](' + history_file_link + ') |')
      else:
        file_w.write ('| [' + date + '](' + date_file_link + ') |')

      file_w.write ('\n')
    except:
      traceback.print_exc()

    if is_summary_file and len(email) > 0 and email != "null":
      if len(ok) > 0:
        if int(fail) > 0 or int(warn) > 0:
          subject = f'The scanning result score are: fails={fail}, warns={warn}'
          text = f'There are fails or warns in the last scanning report:\n\t{schema_host_name}{date_file_link}\nSee historical details at:\n\t{schema_host_name}{history_file_link}'
          sent_notification (email, subject, text)
          print ("== log: notification sent: warns or fails")
      else:
        subject = f'The scanning result report has wrong formant'
        text = f'The given scanning report does not correspond to appropriate format:\n\t{schema_host_name}{date_file_link}\nSee historical details at:\n\t{schema_host_name}{history_file_link}'
        sent_notification (email, subject, text)
        print ("== log: notification sent: wrong report")

######### ######### ######### ######### ######### ######### ######### ######### ######### 
def handle_site (history_file_name, summary_file_w):
  names = re.findall(r'^(.+)_history\.md$', os.path.basename(history_file_name))
  if len(names) != 1:
    print ("== wrn: wrong site_name within '<site_name>_history.md' filename")
    return

  name = names[0]

  history_file_w = open(history_file_name, 'w')
  history_file_w.write('#### ' + name + '\n\n')
  history_file_w.write('| Site | Status | Pass | Warn | Fail | Date |\n')
  history_file_w.write('| ---- | ------ | ---- | ---- | ---- | ---- |\n')

  data_dir = os.path.dirname(history_file_name) + '/data'
  data_files = sorted(os.listdir(data_dir), reverse=True)
  if len(data_files) > 0:
    parse_results(name, data_dir + '/' + data_files[0], True, summary_file_w, history_file_name)
    for file in data_files:
      parse_results(name, data_dir + '/' + file, False, history_file_w, history_file_name)

  history_file_w.close()
######### ######### ######### ######### ######### ######### ######### ######### ######### 

# print ("== log: [" + sys.argv[0] + "] called as:")
# print (">>>>>>: " + " ".join(sys.argv))

# there should be one argument: working_directory
# working_directory should contain links with names like '<SITE>_history.md' pointing to '../r_<REPORT_ID>/<SITE>_history.md'
if len(sys.argv) != 2:
  print ("== err: wrong usage, should be: " + sys.argv[0] + " <work_dir>")
  sys.exit(1)

if not os.path.isdir(sys.argv[1]):  
  print ("== err: wrong usage, should be: " + sys.argv[0] + " <work_dir>")
  sys.exit(1)

work_dir = sys.argv[1]

# print ("== log: current_dir: " + os.getcwd())
# print ("== log: work_dir: " + work_dir)

summary_file_w = open(work_dir + '/baseline-summary.md','w')
summary_file_w.write('Switch to [Target URLs List](mailings)\n\n')
summary_file_w.write('| Site | Status | Pass | Warn | Fail | History |\n')
summary_file_w.write('| ---- | ------ | ---- | ---- | ---- | ------- |\n')

history_links = sorted(os.listdir(work_dir), reverse=True)

if len(history_links) > 0:
  for link in history_links:
    full_link = work_dir + '/' + link
    if os.path.islink(full_link) and bool(re.search(r'^.+_history\.md$', link)):
      handle_site(work_dir + '/' + os.readlink(full_link), summary_file_w)

summary_file_w.close()
# print ("== log: [" + sys.argv[0] + "] finished")
