import socket
import select
s_cmd = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
s_data = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
s_cmd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
cmd_port = int(input("Server port number(for command) is : "))
s_cmd.connect(("0.0.0.0", cmd_port))
print(f"client_cmd channel addr {s_cmd.getsockname()}, server addr is : {s_cmd.getpeername()}")
msg = ""
s_data.settimeout(5)
while(msg != "QUIT"):
	msg = input("Enter message : ")
	s_cmd.sendall(msg.encode("utf-8"))
	recv_msg = s_cmd.recv(1024).decode()
	if(msg == "PASV"):
		print(f'recv msg for PASV command {recv_msg}')
		data_port = int(recv_msg.split()[5])
		print(f'******{data_port}******')
		s_data.connect(("0.0.0.0", data_port))
	print(f'c> {recv_msg}')
	if(msg == "LIST" or msg.split()[0] == "DL"):
		if(recv_msg.split()[0] == "226"):
			# print("Debug message = Enter to if")
			recv_msg = s_data.recv(1024).decode()
			print(f'd> {recv_msg}')

