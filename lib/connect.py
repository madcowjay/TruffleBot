"""
Updated 2018/05/02
  -kill_processes now takes a file instead of an ip list. It will kill all copies
   of that program on all ips in PiManager's ip list that were launched from
   connect.py (by matching 'python3 -u <client_file>')
									-JW
Updated 2018/05/01
  -moved ip_list to host.py and made it an argument to PiManager
									-JW

Updated 2018/04/28
  -log file includes errors now
  -python3 called with -u to flush output
  -log file back to appending
									-JW

Updated 2018/04/25
  -File/Directory synchronizing removed for now
  -ip addresses hard coded
  -board numbers removed (use serial number)
  -log file overwrites now instead of appending
									-JW
"""

import os, subprocess, time, re, select
import paramiko, bidict
from   lib.debug_print import *


class PiManager:
	def __init__(self, client_dir, ip_list):
		#init global variables
		self.client_dir = client_dir
		self.ip_list = ip_list

		debug_print('PiManager initializing with:')
		debug_print('   client_dir      = {}'.format(self.client_dir))
		debug_print('   ip_list         = {}'.format(self.ip_list))

		#init paramiko
		self.ssh = paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


	def identifpi(self):
		debug_print('identifpi started')
		ip_serial=bidict.bidict()
		#get serial number for each pi, tie to ip address
		for ip in self.ip_list:
			self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
			command = "cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2"
			stdin,stdout,stderr = self.ssh.exec_command(command)
			ip_serial[ip] = stdout.read().decode().replace('\n','')
		self.ssh.close()
		debug_print('ip_serial: {}'.format(ip_serial))
		return ip_serial


	#executes a command on each client
	def exec_command(self, command, addr=None):
		debug_print('exec_command started')
		try:
			if addr:
				self.ssh.connect(addr, username='pi', password='raspberryB1oE3')
				self.ssh.exec_command(command)
				debug_print('%s: executed "%s"'%(addr,command))
				self.ssh.close()
			else:
				for ip in self.ip_list:
					self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
					self.ssh.exec_command(command)
					debug_print('%s: executed "%s"'%(ip,command))
				self.ssh.close()
		except Exception as e:
			print(e)


	#executes multiple commands on each client
	def exec_commands(self, commands, addr=None):
		debug_print('exec_commands started')
		try:
			if addr:
				for command in commands:
					self.ssh.connect(addr, username='pi', password='raspberryB1oE3')
					self.ssh.exec_command(command)
					debug_print('%s: executed "%s"'%(addr,command))
				self.ssh.close()
			else:
				for ip in self.ip_list:
					for command in commands:
						self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
						self.ssh.exec_command(command)
						debug_print('%s: executed "%s"'%(ip,command))
					self.ssh.close()
		except Exception as e:
			print(e)


	#takes the file to to run as argument, and runs it on each client as sudo
	def run_script(self, client_file, log_file=None):
		debug_print('run_script started')
		try:
			for ip in self.ip_list:
				self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
				if log_file:
					command = 'cd %s && python3 -u %s &>> log/%s'%(self.client_dir,client_file,log_file)
					debug_print(command)
					stdin, stdout, stderr = self.ssh.exec_command(command)
					debug_print('%s: starting client file, writing stdout and stderr to %s'%(ip,log_file))
				else:
					command = 'cd %s && python3 %s'%(self.client_dir,client_file)
					self.ssh.exec_command(command)
					debug_print('%s: starting client file'%ip)
			self.ssh.close()
		except Exception as e:
			print(e)


	#takes a dictionary of form: ip:PID and iterates through it, killing each PID
	def kill_processes(self, client_file):
		debug_print('kill_processes started')
		killed = {}
		try:
			for ip in self.ip_list:
				self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
				stdin,stdout,stderr = self.ssh.exec_command('pgrep -f "python3 -u %s"'%(client_file))
				pids = stdout.read().decode()
				for pid in pids.split('\n'):
					if pid != '':
						self.ssh.exec_command('sudo kill %s'%pid)
						debug_print('%s: killed "%s"'%(ip,pid))
			self.ssh.close()
		except Exception as e:
			print(e)
