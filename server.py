import select
import socket
import json
import os
import shutil
import sys
import time

class ConfigFileContainer(object):#TODO:It is not complete

    def __init__(self, json_str):
        ConfigFileContainer.users = json_str["users"]
        ConfigFileContainer.accounting_data = json_str["accounting"]
        ConfigFileContainer.auth = json_str["authorization"]

    @classmethod
    def user_check(cls, user_name) -> bool:
        for account in cls.users:
            if(account["user"] == user_name):
                return True
        return False

    @classmethod
    def pass_check(cls, user_name, password):
        for account in cls.users:
            if(account["user"] == user_name):
                if(account["password"] == password):
                    return True
                else:
                    return False
        return False

    @classmethod
    def file_auth_check(cls, file_name):
        for file in cls.auth["files"]:
            if(file == file_name):
                return True
        return False

    @classmethod
    def admin_check(cls, user_name):
        for name in cls.auth["admins"]:
            if(name == user_name):
                return True
        return False

    @classmethod
    def process_accounting(cls, user_name, data_size):
        if(cls.accounting_data["enable"] == False):
            return True
        else:
            account = ""
            for account_ in cls.accounting_data["users"]:
                if account_["user"] == user_name:
                    account = account_
                    break

            if not account:
                return True
            else:
                if(account["size"] > data_size):
                    account["size"] -= data_size
                    if account["size"] <= cls.accounting_data["threshold"] and account["alert"] == True:
                        cls.send_email(user_name, account["size"])
                    return True
                else:
                    if account["size"] <= cls.accounting_data["threshold"] and account["alert"]== True:
                        cls.send_email(user_name, account["size"])
                    return False

    @classmethod
    def send_email(cls, username, current_size):
        mail_socket = socket.socket()
        mail_socket.connect(("mail.ut.ac.ir", 25))

        for account in cls.accounting_data["users"]:
            if(account["user"] == username):
                break

        if(account["user"] != username):
            print(f"couldnt find email for {username}")
            return

        #response to login
        recv_msg = mail_socket.recv(2048)
        if(recv_msg.decode().split()[0] == "220"):
            print("mail server is okay")
        else:
            print(f"mail server is not okay : {recv_msg}")
            mail_socket.close()
            return

        #send hello msg
        mail_socket.sendall('helo mail\r\n'.encode("utf-8"))
        #resp
        recv_msg = mail_socket.recv(2048)
        if(recv_msg.decode().split()[0] == "250"):
            print("Hello response is okay")
        else:
            print(f"Hello response is not okay : {recv_msg}")
            mail_socket.close()
            return



        #send auth login
        mail_socket.sendall('auth login\r\n'.encode("utf-8"))
        #resp
        recv_msg = mail_socket.recv(2048)
        if (recv_msg.decode().split()[0] == "334"):
            print("auth login response is okay")
        else:
            print(f"auth login response is not okay : {recv_msg}")
            mail_socket.close()
            return

        #send username
        mail_socket.sendall('*****************'.encode("utf-8"))#TODO:username
        #resp
        recv_msg = mail_socket.recv(2048)
        if (recv_msg.decode().split()[0] == "334"):
            print("username response is okay")
        else:
            print(f"username response is not okay : {recv_msg}")
            mail_socket.close()
            return


        #send pass
        mail_socket.sendall('*******************'.encode("utf-8"))#TODO:pass
        #resp
        recv_msg = mail_socket.recv(2048)
        if (recv_msg.decode().split()[0] == "235"):
            print("pass response is okay")
        else:
            print(f"pass response is not okay : {recv_msg}")
            mail_socket.close()
            return

        #mail from
        mail_socket.sendall("mail from: <amin.mohaghegh@ut.ac.ir>\r\n".encode("utf-8"))
        #resp
        recv_msg = mail_socket.recv(2048)
        if (recv_msg.decode().split()[0] == "250"):
            print("mail from response is okay")
        else:
            print(f"mail from response is not okay : {recv_msg}")
            mail_socket.close()
            return


        #rcpt to
        mail_socket.sendall(f'rcpt to: <{account["email"]}>\r\n'.encode("utf-8"))
        #resp
        recv_msg = mail_socket.recv(2048)
        if (recv_msg.decode().split()[0] == "250"):
            print("rcpt response is okay")
        else:
            print(f"rcpt response is not okay : {recv_msg}")
            mail_socket.close()
            return


        #data
        mail_socket.sendall(f'data\r\n'.encode("utf-8"))
        #resp
        recv_msg = mail_socket.recv(2048)
        if (recv_msg.decode().split()[0] == "354"):
            print("data response is okay")
        else:
            print(f"data response is not okay : {recv_msg}")
            mail_socket.close()
            return


        #enter data from
        mail_socket.sendall(f'salam, remaining size = {current_size}\r\n.\r\n'.encode("utf-8"))
        #resp
        recv_msg = mail_socket.recv(2048)
        if (recv_msg.decode().split()[0] == "250"):
            print("sending response is okay")
        else:
            print(f"sending data response is not okay : {recv_msg}")
            mail_socket.close()
            return

        #Quit data from
        mail_socket.sendall(f'quit\r\n'.encode("utf-8"))
        #Quit
        recv_msg = mail_socket.recv(2048)
        if (recv_msg.decode().split()[0] == "221"):
            print("quit response is okay")
        else:
            print(f"quit data response is not okay : {recv_msg}")

        mail_socket.close()

class ClientRecord(object):
    def __init__(self, client_socket_cmd, root_dir, log_file):
        self.client_socket_cmd = client_socket_cmd
        self.client_socket_data = None
        self.conn_data = None
        self.cwd = root_dir
        self.root_dir = root_dir
        self.cmd = ""
        self.user_name = ""
        self.login_process = 0
        self.log_file = log_file
        self.help =''''214
        USER [name], Its argument is used to specify the user's string. It is used for user authentication.
        PASS [password], Its argument is used to specify the user's password. It is used for user authentication.
        PASV, Return open port on server and wait until client establish data channel via this port.
        PWD, Return current work directory
        MKD[-i], Make directory or file(default is directory)
        \t -i make file 
        RMD[-f], Remove file or directory(default is file)
        \t -f remove directory
        LIST, Return current directory list via data channel
        CWD [path], change directory to path
        DL [name], download file and send it through data channel
        QUIT, Logout the user and close connections'''

    def send_by_cmd_channel(self, data_to_send : str, encoding_type = "UTF-8"):
        try:
            self.client_socket_cmd.sendall(data_to_send.encode(encoding_type))
        except:
            print(f'Something is wrong with cmd channel : {self.client_socket_cmd.getsockname()}')#TODO:print


    def send_by_data_channel(self, data_to_send : str, encoding_type = "UTF-8"):
        if not self.conn_data:
            print(f'There is no data channel : {self.client_socket_cmd.getsockname()}')#TODO:print
            return False
        else:
            try:
                data_size = sys.getsizeof(data_to_send)
                if(ConfigFileContainer.process_accounting(self.user_name, data_size)):
                    if not data_to_send:
                        self.conn_data.sendall("EMPTY".encode(encoding_type))
                    else:
                        self.conn_data.sendall(data_to_send.encode(encoding_type))
                    print(f'send successfully {data_to_send}')
                    self.write_log(f'DATA : send data to {self.conn_data.getsockname()}')
                    return True

            except:
                print(f'can not send from data port : {self.client_socket_cmd.getsockname()}') #TODO:print
                return False

    def decode_user_cmd(self):
        self.login_process = 0
        self.user_name = ""
        is_valid = ConfigFileContainer.user_check(self.cmd[1])

        if(is_valid == True):
            self.user_name = self.cmd[1]
            self.send_by_cmd_channel("331 User name okay, need password.")
            self.write_log(f'Enter user name : {self.cmd[1]}, SUCCESSFULL')

        else:
            self.send_by_cmd_channel("430 Invalid username or password.")
            self.write_log(f'Enter user name : {self.cmd[1]}, FAILED')

    def decode_password_cmd(self):
        if self.user_name == "":
            self.write_log(f'Enter Password , Befor User Name : FAILED')
            self.send_by_cmd_channel("503 Bad sequence of commands.")

        else:
            is_valid = ConfigFileContainer.pass_check(self.user_name, self.cmd[1])
            if(is_valid == True):
                self.login_process = 1
                self.send_by_cmd_channel("230 User logged in, proceed.")
                self.write_log(f'Enter Password : SUCCESSFULL')

            else:
                self.write_log(f'Enter Password , FAILED')
                self.user_name = ""
                self.login_process = 0
                self.send_by_cmd_channel("430 Invalid username or password.")


    def decode_pwd_cmd(self):
        head, tail = os.path.split(self.cwd)
        relative_path = tail
        while(tail != "ftp_root_dir"):
            head, tail = os.path.split(head)
            relative_path = tail + "/" + relative_path
        self.send_by_cmd_channel(f"257 {relative_path}")

    def decode_mkd_cmd(self):
        if(len(self.cmd) > 2):
            if(self.cmd[1] == "-i"):
                open(self.cmd[2], "a").close()
                self.send_by_cmd_channel(f"257 {self.cmd[2]} created")
                self.write_log(f'file : {self.cmd[2]} created')
            else:
                self.send_by_cmd_channel("501 Syntax error in parameters or arguments.")
                self.write_log(f'couldnt create file:  {self.cmd[2]}')
        else:
            os.makedirs(f"{self.cmd[1]}", exist_ok=True)
            self.send_by_cmd_channel(f"257 {self.cmd[1]} created")
            self.write_log(f'dir {self.cmd[1]} created')

    def decode_rmd_cmd(self):
        if(len(self.cmd) > 2):
            if(self.cmd[1] == "-f"):
                if(os.path.isdir(f'{self.cmd[2]}')):
                    shutil.rmtree(self.cmd[2])
                    self.send_by_cmd_channel(f'250 {self.cmd[2]} deleted.')
                    self.write_log(f'dir : {self.cmd[2]} deleted')
                else:
                    self.send_by_cmd_channel("501 Syntax error in parameters or arguments.")
                    self.write_log(f'couldnt delete dir : {self.cmd[2]}')
            else:
                self.send_by_cmd_channel("501 Syntax error in parameters or arguments.")
                self.write_log(f'couldnt delete dir : {self.cmd[2]}')
        else:
            if(os.path.isfile(self.cmd[1])):
                if(ConfigFileContainer.auth["enable"] == False):
                    os.remove(self.cmd[1])
                    self.send_by_cmd_channel(f'250 {self.cmd[1]} deleted.')
                    self.write_log(f'file : {self.cmd[1]} deleted')
                else:
                    if(ConfigFileContainer.file_auth_check(self.cmd[1])):
                        if(ConfigFileContainer.admin_check(self.user_name)):
                            os.remove(self.cmd[1])
                            self.send_by_cmd_channel(f'250 {self.cmd[1]} deleted.')
                            self.write_log(f'file : {self.cmd[1]} deleted')
                        else:
                            self.send_by_cmd_channel("550 File unavailable.")
                            self.write_log(f'couldnt access file : {self.cmd[1]}')
                    else:
                        os.remove(self.cmd[1])
                        self.send_by_cmd_channel(f'250 {self.cmd[1]} deleted.')
                        self.write_log(f'file : {self.cmd[1]} deleted')
            else:
                self.send_by_cmd_channel("501 Syntax error in parameters or arguments.")
                self.write_log(f'couldnt delete file : {self.cmd[1]}')



    def decode_list_cmd(self):
        dir_list = os.listdir(self.cwd)
        transmit_is_finish = self.send_by_data_channel(", ".join(dir_list))#TODO:data_channel
        if(transmit_is_finish == True):
            self.send_by_cmd_channel("226 List transfer done.")
        else:
            self.send_by_cmd_channel("500 Error.")

    def decode_cwd_cmd(self):
        if(len(self.cmd) == 1):
            os.chdir(self.root_dir)
            self.send_by_cmd_channel("250 Successful Change.")
            self.write_log(f'dir changed to {self.root_dir}')
        else:
            if(os.path.isdir(self.cmd[1])):
                os.chdir(self.cmd[1])
                self.send_by_cmd_channel("250 Successful Change.")
                self.write_log(f'dir changed to {self.cwd}')
            else:
                self.send_by_cmd_channel("501 Syntax error in parameters or arguments.")
                self.write_log(f'couldnt change dir to {self.cwd}')
        self.cwd = os.getcwd()


    def decode_dl_cmd(self):#TODO:data_channel
        if(os.path.isfile(self.cmd[1])):
            if(ConfigFileContainer.auth["enable"] == False):
                content = open(self.cmd[1], "r+b").read()
                transmit_is_finish = self.send_by_data_channel(str(content))
                if(transmit_is_finish == True):
                    self.send_by_cmd_channel("226 Successful Download.")
                    print(f'download : data size = {sys.getsizeof(str(content))}')
                    self.write_log(f'file : {self.cmd[1]} downloaded')
                    return
            else:
                if(ConfigFileContainer.file_auth_check(self.cmd[1])):
                    if(ConfigFileContainer.admin_check(self.user_name)):
                        content = open(self.cmd[1], "r+b").read()
                        transmit_is_finish = self.send_by_data_channel(str(content))
                        if(transmit_is_finish == True):
                            self.send_by_cmd_channel("226 Successful Download.")
                            print(f'download : data size = {sys.getsizeof(str(content))}')
                            self.write_log(f'file : {self.cmd[1]} downloaded')
                            return
                    else:
                        self.send_by_cmd_channel("550 File unavailable.")
                        self.write_log(f'can not access file : {self.cmd[1]}')
                else:
                    content = open(self.cmd[1], "r+b").read()
                    transmit_is_finish = self.send_by_data_channel(str(content))
                    if(transmit_is_finish == True):
                        self.send_by_cmd_channel("226 Successful Download.")
                        print(f'download : data size = {sys.getsizeof(str(content))}')
                        self.write_log(f'file : {self.cmd[1]} downloaded')
                        return
        else:
            self.send_by_cmd_channel("501 Syntax error in parameters or arguments.")
            self.write_log(f'could not download the file: {self.cmd[1]}')


    def decode_help_cmd(self):
        self.send_by_cmd_channel(f'{self.help}')

    def decode_pasv_cmd(self):
        if not self.client_socket_data:
            self.client_socket_data = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            self.client_socket_data.bind(("0.0.0.0", 0))
            self.client_socket_data.listen()
            self.send_by_cmd_channel(f'227 Entering Passive mode'
                                     f' {self.client_socket_data.getsockname()[0]} '
                                     f'{self.client_socket_data.getsockname()[1]}')
            conn, addr = self.client_socket_data.accept()
            self.conn_data = conn
            self.write_log(f'make data channel at port {self.conn_data.getsockname()}')
        else:
            self.send_by_cmd_channel(f'227 Entering Passive mode'
                                     f' {self.client_socket_data.getsockname()[0]} '
                                     f'{self.client_socket_data.getsockname()[1]} .')
            self.write_log(f'data channel at port {self.conn_data.getsockname()} is already exists')



    def decode_quit_cmd(self):
        if(self.client_socket_data != None):
            self.client_socket_data.close()
        if self.conn_data:
            self.conn_data.close()

        self.write_log(f'Quit')
        self.send_by_cmd_channel("221 Successful Quit.")
        self.client_socket_cmd.close()

    def decode_not_login_cmd(self):
        self.send_by_cmd_channel("332 Need account for login.")

    def write_log(self, log_str : str):
        if(self.log_file == None):
            return
        header = f'USER : {self.user_name}, month:{time.localtime().tm_mon}, day:{time.localtime().tm_mday},' \
            f' hour:{time.localtime().tm_hour}, min:{time.localtime().tm_min}'
        self.log_file.write(header + "," + log_str + "\n")

    def decode_cmd(self):
        self.cmd = self.client_socket_cmd.recv(1024).decode("UTF-8").split()


        if(self.cmd[0] == "USER"):
            self.decode_user_cmd()

        elif(self.cmd[0] == "PASS"):
            self.decode_password_cmd()
            self.write_log(f'Enter pass')

        elif(self.login_process != 1):
            self.decode_not_login_cmd()

        else:
            os.chdir(self.cwd)
            self.write_log(f'CMD : {" ".join(self.cmd)}')

            if(self.cmd[0] == "PWD"):
                self.decode_pwd_cmd()

            elif(self.cmd[0] == "MKD"):
                self.decode_mkd_cmd()

            elif(self.cmd[0] == "RMD"):
                self.decode_rmd_cmd()

            elif(self.cmd[0] == "LIST"):
                self.decode_list_cmd()

            elif(self.cmd[0] == "CWD"):
                self.decode_cwd_cmd()

            elif(self.cmd[0] == "DL"):
                self.decode_dl_cmd()

            elif(self.cmd[0] == "HELP"):
                self.decode_help_cmd()

            elif(self.cmd[0] == "PASV"):
                self.decode_pasv_cmd()

            elif(self.cmd[0] == "QUIT"):
                self.decode_quit_cmd()
                return True

            else:
                self.send_by_cmd_channel("500 Error")

        return False


if __name__ == "__main__":

    with open("config.json") as config_file:
        config_data = json.load(config_file)
    if config_data["logging"]["enable"] == True:
        log_file = open(config_data["logging"]["path"], "a")
    else:
        log_file = None

    config_container = ConfigFileContainer(config_data)

    os.makedirs("ftp_root_dir", exist_ok=True)
    try:
        os.chdir("ftp_root_dir")
    except:
        print("ftp Root directory didn't found!")
        os.abort()
    root_dir = os.getcwd()

    server_ip = "0.0.0.0"
    server_cmd_port = 0

    server_cmd_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

    server_cmd_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_cmd_socket.bind((server_ip, server_cmd_port))

    server_cmd_socket.listen(10)
    print(f"Server IP = {server_cmd_socket.getsockname()[0]}, Server cmd Port = {server_cmd_socket.getsockname()[1]}")
    print("Server is Listening...")

    cmd_sockets_list = [server_cmd_socket]
    clients = {}

    while(1):
        read_sockets, _, exception_sockets = select.select(cmd_sockets_list, [], cmd_sockets_list)

        for notified_socket in read_sockets:
            if(notified_socket != server_cmd_socket):
                socket_name = notified_socket.getpeername()
                is_quit = clients[notified_socket].decode_cmd()
                if is_quit:
                    print(f'client {socket_name} closed the connection')
                    del clients[notified_socket]
                    cmd_sockets_list.remove(notified_socket)

            else:
                client_socket, client_addr = server_cmd_socket.accept()
                cmd_sockets_list.append(client_socket)
                clients[client_socket] = ClientRecord(client_socket, root_dir, log_file)
                print(f'Accept connection from {client_addr[0]}:{client_addr[1]}')
        for exc_socket in exception_sockets:
            print(f'Something wrong has happened with {exc_socket.getsockname()[0]}:{exc_socket.getsockname()[1]}')
            cmd_sockets_list.remove(exc_socket)
            if(exc_socket != server_cmd_socket):
                cmd_sockets_list.remove(exc_socket)
            else:
                print(f'Something is wrong with server')
                os.abort()




