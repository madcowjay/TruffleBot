import os, subprocess, time, re, select
import paramiko, bidict
from   lib.debug_print import *


class PiManager:
	def __init__(self, client_dir, client_log_dir, config_file, log_file, ip_list, username, password):
		#init global variables
		self.client_dir     = client_dir
		self.client_log_dir = client_log_dir
		self.config_file    = config_file
		self.log_file       = log_file
		self.ip_list        = ip_list
		self.username       = username
		self.password       = password

		debug_print('PiManager initializing with:')
		debug_print('   client_dir      = {}'.format(self.client_dir))
		debug_print('   client_log_dir  = {}'.format(self.client_log_dir))
		debug_print('   config_file     = {}'.format(self.config_file))
		debug_print('   log_file        = {}'.format(self.log_file))
		debug_print('   ip_list         = {}'.format(self.ip_list))
		debug_print('   username        = {}'.format(self.username))
		debug_print('   password        = {}'.format(self.password))
		#init paramiko
		self.ssh = paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


	def identifpi(self):
		#get serial number for each pi, tie to ip address
		debug_print('identifpi started')
		ip_serial=bidict.bidict()
		for ip in self.ip_list:
			self.ssh.connect(ip, username=self.username, password=self.password)
			command = "cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2"
			stdin,stdout,stderr = self.ssh.exec_command(command)
			ip_serial[ip] = stdout.read().decode().replace('\n','')
		self.ssh.close()
		debug_print('ip_serial: {}'.format(ip_serial))
		return ip_serial

	def exec_command(self, command, addr=None):
		#executes a command on each client
		debug_print('exec_command started')
		try:
			if addr:
				self.ssh.connect(addr, username=self.username, password=self.password)
				self.ssh.exec_command(command)
				debug_print('%s: executed "%s"'%(addr,command))
				self.ssh.close()
			else:
				for ip in self.ip_list:
					self.ssh.connect(ip, username=self.username, password=self.password)
					self.ssh.exec_command(command)
					debug_print('%s: executed "%s"'%(ip,command))
				self.ssh.close()
		except Exception as e:
			print('Error in exec_command: ' + str(e))

	def exec_commands(self, commands, addr=None):
		#executes multiple commands on each client
		debug_print('exec_commands started')
		try:
			if addr:
				for command in commands:
					self.ssh.connect(addr, username=self.username, password=self.password)
					self.ssh.exec_command(command)
					debug_print('%s: executed "%s"'%(addr, command))
				self.ssh.close()
			else:
				for ip in self.ip_list:
					for command in commands:
						self.ssh.connect(ip, username=self.username, password=self.password)
						self.ssh.exec_command(command)
						debug_print('%s: executed "%s"'%(ip, command))
					self.ssh.close()
		except Exception as e:
			print('Error in exec_commands: ' + str(e))

	def run_script(self, client_file):
		#takes the file to to run as argument, and runs it on each client as sudo
		debug_print('run_script started')
		try:
			for ip in self.ip_list:
				self.ssh.connect(ip, username=self.username, password=self.password)
				command = 'cd %s && python3 -u %s -c %s &> %s/%s'%(self.client_dir,client_file,self.config_file,self.client_log_dir,self.log_file)
				debug_print(command)
				stdin, stdout, stderr = self.ssh.exec_command(command)
				debug_print('%s: starting client file, writing stdout and stderr to %s'%(ip,self.log_file))
			self.ssh.close()
		except Exception as e:
			print('Error in run_script: ' + str(e))

	def kill_processes(self, client_file):
		#takes a dictionary of form: ip:PID and iterates through it, killing each PID
		debug_print('kill_processes started')
		killed = {}
		try:
			for ip in self.ip_list:
				self.ssh.connect(ip, username=self.username, password=self.password)
				stdin,stdout,stderr = self.ssh.exec_command('pgrep -f "python3 -u %s"'%(client_file))
				pids = stdout.read().decode()
				for pid in pids.split('\n'):
					if pid != '':
						self.ssh.exec_command('sudo kill %s'%pid)
						print('%s: killed "%s"'%(ip,pid))
			self.ssh.close()
		except Exception as e:
			print('Error in kill_processes: ' + str(e))

	def upload_file(self, file_path, addr=None):
		#uploads a file from the host to the client project directory on the remote machines
		try:
			if addr:
				self.ssh.connect(addr, username=self.username, password=self.password)
				sftp = self.ssh.open_sftp()
				client_path = '%s/%s'%(self.client_dir,file_path)
				sftp.put(file_path,client_path)
				debug_print("%s: transferred - %s"%(addr,file_path))
				self.ssh.close()
				sftp.close()
			else:
				for ip in self.ip_list:
					self.ssh.connect(ip, username=self.username, password=self.password)
					sftp = self.ssh.open_sftp()
					client_path = '%s/%s'%(self.client_dir,file_path)
					sftp.put(file_path,client_path)
					debug_print("%s: transferred - %s"%(ip,file_path))
					self.ssh.close()
				sftp.close()
		except Exception as e:
			print('Error in upload_file: ' + str(e))
