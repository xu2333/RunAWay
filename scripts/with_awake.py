#!/usr/bin/env python3
"""Run one command under a temporary macOS idle-sleep assertion.

No permanent settings, display assertion, deadline extension, retry or service
call is added. Other platforms run the command directly. Manual sleep and lid
closure are not prevented by the macOS idle assertion.
"""
import argparse
import os
import platform
import shutil
import sys


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',nargs=argparse.REMAINDER);args=parser.parse_args();command=args.command
 if command[:1]==['--']:command=command[1:]
 if not command:parser.error('Provide a command after --')
 if platform.system()=='Darwin':
  guard=shutil.which('caffeinate')
  if guard is None:parser.error('macOS caffeinate unavailable; command not started')
  command=[guard,'-i']+command;print('RunAWay: temporary idle-sleep guard for this command; no permanent settings changed.',file=sys.stderr,flush=True)
 os.execvp(command[0],command)

if __name__=='__main__':main()
