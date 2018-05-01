"""
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

import subprocess
import re
import os
import paramiko
import time
import bidict

class PiManager:
    def __init__(self, client_project_dir):
        #init global variables
        #self.ip_list = ['10.0.0.201','10.0.0.202'] #manual entries -JW
        #self.ip_list = ['10.0.0.202']
        self.ip_list = ['192.168.1.212']
        self.client_project_dir = client_project_dir

        #init paramiko
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


    def identifpi(self):
        ip_serial=bidict.bidict()
        #get serial number for each pi, tie to ip address
        for ip in self.ip_list:
            self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
            stdin,stdout,stderr = self.ssh.exec_command("cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2")
            ip_serial[ip] = stdout.read().decode().replace('\n','')
        self.ssh.close()
        return ip_serial


    #executes a command on each client
    def exec_command(self,command, addr=None):
        try:
            if addr:
                self.ssh.connect(addr, username='pi', password='raspberryB1oE3')
                self.ssh.exec_command(command)
                print('%s: executed "%s"'%(addr,command))
                self.ssh.close()
            else:
                for ip in self.ip_list:
                    self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
                    self.ssh.exec_command(command)
                    print('%s: executed "%s"'%(ip,command))
                self.ssh.close()
        except Exception as e:
            print(e)


    #executes multiple commands on each client
    def exec_commands(self,commands, addr=None):
        try:
            if addr:
                for command in commands:
                    self.ssh.connect(addr, username='pi', password='raspberryB1oE3')
                    self.ssh.exec_command(command)
                    print('%s: executed "%s"'%(addr,command))
                self.ssh.close()
            else:
                for ip in self.ip_list:
                    for command in commands:
                        self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
                        self.ssh.exec_command(command)
                        print('%s: executed "%s"'%(ip,command))
                    self.ssh.close()
        except Exception as e:
            print(e)


    #takes the file to to run as argument, and runs it on each client as sudo
    def run_script(self,client_file,log_file=None):
        try:
            for ip in self.ip_list:
                self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
                if log_file:
                    self.ssh.exec_command('cd %s && python3 -u %s &>> log/%s'%(self.client_project_dir,client_file,log_file))
                    print('%s: starting client file, writing stdout and stderr to %s'%(ip,log_file))
                else:
                    self.ssh.exec_command('cd %s && python3 %s'%(self.client_project_dir,client_file))
                    print('%s: starting client file'%ip)
            self.ssh.close()
        except Exception as e:
            print(e)


    #takes a dictionary of form: ip:PID and iterates through it, killing each PID
    def kill_processes(self,pid_dict):
        try:
            for ip in pid_dict.keys():
                pid = pid_dict[ip]
                self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
                self.ssh.exec_command('sudo kill %s'%pid)
                print('%s: killed "%s"'%(ip,pid))
            self.ssh.close()
        except Exception as e:
            print(e)