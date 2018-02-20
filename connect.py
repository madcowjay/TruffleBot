import subprocess
import re
import os
import paramiko
import time

"""
Any python script that calls this module must be in a directory above the host_project_dir or in the host_project_dir.
host_project_dir = the folder that contains all the necessary files for the code to run (client.py, adc&dac libraries, etc.)
client_project_dir = the folder on the pi that will be populated with necessary files, where the code runs from
Cannot be inside a folder in the host_project_dir, unlikely anyone would do that.

"""
class PiManager:
    def __init__(self, host_project_dir, client_project_dir):
        #init global variables
        self.ip_list = []
        self.client_dir_files = {}
        self.host_dir_files = []
        self.host_project_dir = host_project_dir
        self.client_project_dir = client_project_dir

        #init paramiko
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        #run some functions to fill global variables
        try:
            self.get_ips()
        except Exception as e:
            print(e)
            print('populating arp table - might take a second')
            self.wake_network()
            self.get_ips()

    # scans the network for raspberry pis and constructs a list of their ip addresses
    def get_ips(self):
        #poll the network for pis
        pi_table = subprocess.check_output('arp -na | grep -i b8:27:eb', shell=True)
        self.ip_list = re.findall('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',str(pi_table))
        return self.ip_list

    #call this if the arp table is not seeing anything
    def wake_network(self):
        for i in range(20):
            subprocess.run(['nc -z -w1 10.0.0.%s 22'%i], shell=True)
            # print("checking 10.0.0.%s"%i)



    def identifpi(self):
        ip_serial={}
        #get serial number for each pi, tie to ip address
        for ip in self.ip_list:
            self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
            stdin,stdout,stderr = self.ssh.exec_command("cat /proc/cpuinfo | grep Serial | egrep -o '([0-9]+.+)'")
            ip_serial[ip] = stdout.read().decode().replace('\n','')
        serial_ip = {serial:ip for ip,serial in ip_serial.items()}
        #static table tying serial to boardnum
        serial_boardnum = {'0000000064cd9be5' : 1,
                        '000000005be2dc56' : 2,
                        '000000004d2375a3' : 3,
                        '0000000033405839' : 4,
                        '000000003dcc2e03' : 5,
                        '0000000068c200c3' : 6,
                        '0000000090f4632f' : 7,
                        '000000005844d5ef' : 8
                      }

        ip_boardnum={serial_ip[serial]:boardnum for serial,boardnum in serial_boardnum.items() if serial in serial_ip.keys()}
        boardnum_ip={boardnum:ip for ip, boardnum in ip_boardnum.items()}

        self.ssh.close()
        return ip_serial,serial_ip,ip_boardnum,boardnum_ip,serial_boardnum




    #returns a tuple (list of the host_dir files, and a dictionary with ip: list of client_dir files)
    def list_files(self):
        #walk the host directory and list all contents
        list_of_files = []
        host_dirs =[]
        exclude = ['.git']
        for root, dirs, files in os.walk(self.host_project_dir,topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude]
            fl = [os.path.join(root, f).replace(self.host_project_dir,'') for f in files]
            list_of_files.append(fl)
            host_dirs.append(root.replace(self.host_project_dir,''))
        hfile_list = [n for sublist in list_of_files for n in sublist]
        self.host_dir_files = hfile_list

        for ip in ip_list:
            self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
            sftp = self.ssh.open_sftp()
            print('connected to %s'%ip)

            file_list=[]
            client_dirs = []
            stdin,stdout,stderr = self.ssh.exec_command('ls -Ra %s'%self.client_project_dir)
            for n in [i.replace('\n','') for i in stdout.readlines()]:
                if re.search(':',n):
                    root = n.replace(':','')
                    client_dirs.append(root.replace(self.client_project_dir,''))
                else:
                    file_list.append(os.path.join(root,n).replace(self.client_project_dir,''))
            self.client_dir_files[ip] = file_list
            self.ssh.close()
            sftp.close()

        return self.host_dir_files, self.client_dir_files


    #uploads a file from the host to the client project directory on the remote machines
    def upload_file(self,file_path, addr=None):
        try:
            if addr:
                self.ssh.connect(addr, username='pi', password='raspberryB1oE3')
                sftp = self.ssh.open_sftp()
                client_path = '%s/%s'%(self.client_project_dir,file_path)
                sftp.put(file_path,client_path)
                print("%s: transferred - %s"%(addr,file_path))
                self.ssh.close()
                sftp.close()
            else:
                for ip in self.ip_list:
                    self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
                    sftp = self.ssh.open_sftp()
                    client_path = '%s/%s'%(self.client_project_dir,file_path)
                    sftp.put(file_path,client_path)
                    print("%s: transferred - %s"%(ip,file_path))
                    self.ssh.close()
                sftp.close()
        except Exception as e:
            print(e)


    # syncs only files that are not on the clients
    def conditional_dir_sync(self):
        working_dir = os.getcwd()

        #walk the host directory and list all contents
        list_of_files = []
        host_dirs =[]
        exclude = ['.git']
        for root, dirs, files in os.walk(self.host_project_dir,topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude]
            fl = [os.path.join(root, f).replace(self.host_project_dir,'') for f in files]
            list_of_files.append(fl)
            host_dirs.append(root.replace(self.host_project_dir,''))
        hfile_list = [n for sublist in list_of_files for n in sublist]
        print('got list of host files')

        #check contents of project folders, update if necessary
        for ip in self.ip_list:
            try:
                #init ssh session over paramiko
                self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
                sftp = self.ssh.open_sftp()
                print('connected to %s'%ip)

                #check if project folder exists
                stdin,stdout,stderr = self.ssh.exec_command('ls ~')
                ls= stdout.readlines()

                #if it doesn't, make it
                if not self.client_project_dir.split('/')[-1] in [n.replace('\n','') for n in ls]:
                    stdin,stdout,stderr = self.ssh.exec_command('mkdir %s'%self.client_project_dir)
                    print("%s: Created %s"%(ip,self.client_project_dir))

                #if it does, list ALL the contents: -R flag and make a list of all the files
                file_list=[]
                client_dirs = []
                stdin,stdout,stderr = self.ssh.exec_command('ls -Ra %s'%self.client_project_dir)
                for n in [i.replace('\n','') for i in stdout.readlines()]:
                    if re.search(':',n):
                        root = n.replace(':','')
                        client_dirs.append(root.replace(self.client_project_dir,''))
                    else:
                        file_list.append(os.path.join(root,n).replace(self.client_project_dir,''))
                # print(client_dirs)

                #check if there are files in the root directory that aren't on the pi
                missingf = set(hfile_list) - {f for f in file_list if f in hfile_list}
                missingd = set(host_dirs) - {d for d in client_dirs if d in host_dirs}
                # print(missingd)

                if len(missingf):
                    # check if directories exist and make them if they are missing
                    for d in missingd:
                        dirpath = self.client_project_dir+d
                        print(dirpath)
                        stdin,stdout,stderr = self.ssh.exec_command('mkdir -p '+dirpath)
                        print('%s: made directory %s - %s'%(ip,dirpath, stderr.read()))

                    for f in missingf:
                        host_path = (self.host_project_dir+f).replace(working_dir+'/','')
                        client_path = self.client_project_dir+f
                        sftp.put(host_path, client_path)
                        print('Transferring: %s - %s' %(f,stderr.read()))

                else: print('%s: up to date'%ip)

                #close sessions
                sftp.close()
                self.ssh.close()
            except Exception as e:
                print(e)


    # deletes the client_dir, resyncs everything
    def dir_sync(self):
        #pass these later
        working_dir = os.getcwd()

        try:
            # get list of files in host directory
            list_of_files = []
            host_dirs =[]
            exclude = ['.git']
            for root, dirs, files in os.walk(self.host_project_dir,topdown=True):
                dirs[:] = [d for d in dirs if d not in exclude]
                fl = [os.path.join(root, f).replace(self.host_project_dir,'') for f in files]
                list_of_files.append(fl)
                host_dirs.append(root.replace(self.host_project_dir,''))
            hfile_list = [n for sublist in list_of_files for n in sublist]

            for ip in self.ip_list:
                self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
                sftp = self.ssh.open_sftp()

                #delete directory
                stdin,stdout,stderr = self.ssh.exec_command('rm -rf %s'%self.client_project_dir)
                print(stderr.read())

                #transfer all files
                for d in host_dirs:
                    dirpath = self.client_project_dir+d
                    print(dirpath)
                    stdin,stdout,stderr = self.ssh.exec_command('mkdir -p '+dirpath)
                    print('%s: made directory %s - %s'%(ip,dirpath, stderr.read()))

                for f in hfile_list:
                    host_path = (self.host_project_dir+f).replace(working_dir+'/','')
                    client_path = self.client_project_dir+f
                    sftp.put(host_path, client_path)
                    print('Transferring: %s - %s' %(f,stderr.read()))
                print('done!')

                #close sessions
                self.ssh.close()
                sftp.close()

        except Exception as e:
            print(e)

    def update(self):
        # # this function should use sftp.stat() to get info on file modification times
        # # only update files that have been modified on the host computer more recently than on
        # # the clients
        # try:
        #     # get list of files in host directory
        #     list_of_files = []
        #     host_dirs =[]
        #     exclude = ['.git']
        #     for root, dirs, files in os.walk(self.host_project_dir,topdown=True):
        #         dirs[:] = [d for d in dirs if d not in exclude]
        #         fl = [os.path.join(root, f).replace(self.host_project_dir,'') for f in files]
        #         list_of_files.append(fl)
        #         host_dirs.append(root.replace(self.host_project_dir,''))
        #     hfile_list = [n for sublist in list_of_files for n in sublist]
        #
        #     for ip in self.ip_list:
        #         self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
        #         sftp = self.ssh.open_sftp()
        # except Exception as e:
        #     print(e)
        pass

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
    def run_script(self,client_file,log=None):
        try:
            for ip in self.ip_list:
                self.ssh.connect(ip, username='pi', password='raspberryB1oE3')
                if log:
                    self.ssh.exec_command('cd %s && sudo python %s >> %s/%s'%(self.client_project_dir,client_file,self.client_project_dir,log))
                    print('%s: starting client file, writing stdio to %s'%(ip,log))
                else:
                    self.ssh.exec_command('cd %s && sudo python %s'%(self.client_project_dir,client_file))
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
