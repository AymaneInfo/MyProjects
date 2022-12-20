import socket
import threading


class Client():
    def __init__(self,nickname,address,port):
        self.nickname = nickname
        self.address = address
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_to_send = ""

    #se connecter
    def connect(self):
        self.client.connect((self.address,self.port))

    #traitement des messages recus du serveur
    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('ascii')
                commande = message.split(":")
                if message == "nickname?":
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                    print(message)
                    if commande[0].startswith("210"):
                        if "accepted the download" in commande[1].strip():
                            argument = commande[2].split(",")
                            self.send_file(argument[0].strip(), int(argument[1].strip()), self.file_to_send)
                        
                            
            except:
                print("an error has occured!")
                self.client.close()
                break

    #traitement des messages du clients
    def write(self):
        while True:
            message = input("")
            self.client.send(message.encode('ascii'))

            commande = message.split(" ")

            if commande[0] == "ACCEPTFILE" and len(commande) == 5:
                self.accept_file(commande[4].strip(), int(commande[3].strip()), commande[2].strip())   

            if commande[0] == "SFIC" and len(commande) == 3:
                self.file_to_send = commande[2]


    #accepter le fichier
    def accept_file(self, addr, port, filename):
        recvSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        recvSocket.bind((addr, port))
        recvSocket.listen()
        while True:
            client, address = recvSocket.accept()
            f = open(filename, "wb")

            while True:
                data = client.recv(1024)
                f.write(data)
                if not data:
                    f.close()
                    break
            
            break
            
            f.close()
            client.close()
        recvSocket.close()       
    
    #envoyer le fichier
    def send_file(self, addr, port, filename):
        sendSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sendSocket.connect( (addr,port) )

        f = open(filename, "rb")

        while True:
            data = f.read(1024)
            sendSocket.send(data)
            if not data:
                f.close()
                break

        sendSocket.close()
        print("le fichier a été bien envoyé")

if __name__ == "__main__":
           
    nickname = input("choose a nickname:")
    port = int(input("choose a port:"))
    host = input("choose a host:")

    client = Client(nickname,host,port)
    client.connect()
    receive_thread = threading.Thread(target=client.receive)
    receive_thread.start()

    write_thread = threading.Thread(target=client.write)
    write_thread.start()
