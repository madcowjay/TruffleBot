import subprocess
import re
import os
import paramiko
import time
import bidict

class PiManager:
    def __init__(self, client_project_dir):
        #init global variables
        self.ip_list = ['10.0.0.201','10.0.0.202'] #manual entries -JW
        self.client_dir_files = {}
        self.client_project_dir = client_project_dir

        #init paramiko
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


    def identifpi(self):
        ip_serial=bidict.bidict()
        #get serial number for each pi, tie to ip address
        for ip in self.ip_list:
            self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
            stdin,stdout,stderr = self.ssh.exec_command("cat /proc/cpuinfo | grep Serial | egrep -o '([0-9]+.+)'",get_pty=True)
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
                    self.ssh.exec_command('cd %s && python3 -u %s > %s'%(self.client_project_dir,client_file,log_file))
                    print('%s: starting client file, writing stdio to %s'%(ip,log_file))
                else:
                    self.ssh.exec_command('cd %s && python3 %s'%(self.client_project_dir,client_file))
                    print('%s: starting client file'%ip)
            self.ssh.close()
        except Exception as e:
            print(e)
