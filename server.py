import socket
import threading
import configparser
import logging,time

logging.basicConfig(filename="serveur.log", filemode="w", format='%(asctime)s: %(message)s',
                        datefmt="%Y/%m/%d %H:%M:%S", level=logging.INFO)

class Server:
    #constructeur
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("dncserver.conf")
        self.address = config.get("settings", "address")
        self.port = int(config.get("settings", "port"))
        self.clients=dict()
        self.private=dict()
        self.request=dict()
        self.files_request = dict()
        self.away=[]
        self.commandes = {"QUIT":"Logout to the server","CHAT":"Helps you send message to all connected clients","ABS":"Changes the state of the user to away(means you can't send messages but you can receive)","BACK":"changes the state of the user from away to active","LIST":"display every user connected","EDIT new nickname":"changes the user's nickname if new one is not already taken","REFUSE nickname":"Helps to refuse a request of having a private chat with the user who sent it","SEND nickname" : "sends a request of having a private chat with another user","TELL nickname message": "sends a private message to the other user once they accepted to have a private chat","STOP nickname": "Stops a private chat between two users","SFIC nickname file":"sends a file once the other user accepts to receive ","ACCEPT nickname.. port... address ...": "accepts a request of having a private chat if its only the nickname of the user that is given in arguments and if the port and the address are also given it will accept to receive a file from the user","HELP":"displays a list of all commands and their definitions"}
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #démarrer le serveur
    def server_start(self):
        print("Server started on :" + self.address + ", " + str(self.port))
        self.server.bind((self.address,self.port))
        self.server.listen()

    #envoyer les messages à tout le monde
    def broadcast(self,message):
        for client in self.clients:
            client.send(message.encode())

    #traitement des messages des clients
    def handle(self,client):
        boo = True
        while boo:
            try:
                message = client.recv(1024).decode("ascii")
                logging.info(f'{self.clients[client]} : {message}')
                commande = message.split(" ",1)
                commande_de_tell = message.split(" ",2)
                commande_de_sfic = message.split(" ",5)
                if commande[0] == 'QUIT':
                    if len(commande) > 1:
                        client.send("420 ! this command takes no parameter")
                        logging.info("420 ! this command takes no parameter")
                    else:
                        self.quit(client)
                        boo = False
                elif commande[0] == 'LIST':
                    self.liste_clients(client)

                elif commande[0] == 'HELP':
                    if len(commande) > 1:
                       client.send("420 ! this command takes no parameter")
                       logging.info("420 ! this command takes no parameter")
                    else:
                        self.liste_commandes(client)

                elif commande[0] == 'EDIT':
                    if len(commande) < 2:
                        client.send("418 ! Missing parameter".encode())
                        logging.info("418 ! Missing parameter")
                    elif commande[1] == ' ':
                        client.send("418 ! Missing parameter".encode())
                        logging.info("418 ! Missing parameter")
                    else:
                        self.verify_nickname(commande[1],client)

                elif commande[0] == 'CHAT':
                    if len(commande) < 2:
                        client.send("418 ! Missing parameter".encode())
                        logging.info("418 ! Missing parameter")
                    elif commande[1] == ' ':
                        client.send("418 ! Missing parameter".encode())
                        logging.info("418 ! Missing paramater")
                    else:
                        self.broadcast("200 : " + self.clients[client] + " : " + commande[1])

                elif commande[0] == 'STOP':
                    if len(commande) < 2:
                        client.send("418 ! Missing parameter".encode())
                        logging.info("418 ! Missing parameter")
                    elif commande[1] == ' ':
                        client.send("418 ! Missing parameter".encode())
                        logging.info("418 ! Missing parameter")
                    else:
                        self.stop(commande[1],client)

                elif commande[0] == 'SEND':
                    print(f'mon tableau: {commande} et sa taille: {len(commande)}')
                    if len(commande) < 2:
                        client.send("418 ! Missing parameter".encode())
                        logging.info("418 ! Missing parameter")
                    elif commande[1] == " ":
                        client.send("418 : Missing parameter".encode())
                        logging.info("418 : Missing parameter")
                    else:
                        self.send(client,commande[1])
                elif commande_de_tell[0] == 'TELL':
                    self.tell(commande_de_tell[1],commande_de_tell[2],client)

                elif commande[0] == 'REFUSE':
                    if len(commande) < 2:
                        client.send("418 ! Missing parameter".encode())
                        logging.info("418 !  Missing parameter")
                    elif commande[1] == '':
                        client.send("418 ! Missing parameter".encode())
                        logging.info("418 Missing parameter")
                    else:
                        self.refuse(client,commande[1])
                        
                elif commande_de_sfic[0] == 'REFUSEFILE':
                    self.refuseFile(commande_de_sfic[1],client)
                 
                elif commande_de_sfic[0] == 'ACCEPTFILE' and len(commande_de_sfic)>3:
                    self.acceptFile(commande_de_sfic[1],commande_de_sfic[2],commande_de_sfic[3],commande_de_sfic[4],client)

                elif commande[0] == 'ABS':
                    self.absent(client)

                elif commande[0] == 'BACK':
                    message="418 : You are already online"
                    logging.info(message)
                    client.send(message.encode())
                    
                elif commande[0] == 'ACCEPT':
                    if len(commande) < 2:
                        client.send("Missing parameter".encode())
                        logging.info("418 Missing parameter")
                    elif commande[1] == '':
                        client.send("Missing parameter".encode())
                        logging.info("418 Missing parameter")
                    else:
                        self.accept(client,commande[1])


                elif commande[0] == 'SFIC':
                    argument = commande[1].split(" ")
                    self.send_file(argument[0], argument[1], client)

                else:
                    client.send('404 : the command was not found'.encode('ascii'))
                    logging.info("404 : Command was not found")
            except:
                client.close()
                nickname = self.clients[client]
                self.broadcast(f'{nickname} left the chat !')                                                                                        
                del self.clients[client]
                break

    #recevoir la connexion
    def receive(self):
        while True:
            client, address = self.server.accept()
            print(f'Connected with {str(address)}')
            client.send('nickname?'.encode('ascii'))
            nickname = client.recv(1024).decode('ascii')
            self.clients[client] = nickname
            print(f'Nickname of the client is {nickname} !')
            self.broadcast(f'206: {nickname} joined the chat! ')
            logging.info(f'206 {nickname} joined the chat! ')
            thread = threading.Thread(target=self.handle,args=(client,))
            thread.start()

    #passer en mode absent
    def absent(self,client):
        self.broadcast(f'200 : {self.clients[client]} is now away')
        logging.info(f'200 : {self.clients[client]} is now away')
        self.away.append(self.clients[client])
        while True:
            try:
                next_msg = client.recv(1024).decode("ascii")
                nxt = next_msg.split(" ",1)
                if nxt[0] == 'BACK':
                    self.broadcast(f'200 : {self.clients[client]} is back')
                    logging.info(f'200 : {self.clients[client]} is back')
                    break
                elif nxt[0] == "ABS":
                    message="417 : You are already away"
                    logging.info(message)
                    client.send(message.encode())
                elif nxt[0] == "CHAT":
                    message="403 : you can't send messages"
                    logging.info(message)
            except:
                print("an error")
    
    #envoyer une requête de messages privées
    def send(self,client,receiver):
        if receiver in self.clients.values():
            if receiver == self.clients[client]:
                message = f"419 : {self.clients[client]} you can't have a private chat with yourself"
                logging.info(message)
                client.send(message.encode())
            else:
                for key, valeur in self.clients.items(): 
                    if receiver == valeur: 
                        receiver_sock = key
                        thread = threading.Thread(target=self.handle,args=(receiver_sock,))
                        thread.start()
                        message = f"100 : {self.clients[client]} wants to have a private a chat with you."
                        logging.info(message)
                        receiver_sock.send(message.encode())
                self.request[client] = self.clients[client]
                self.request[receiver_sock] = self.clients[receiver_sock]

        else:
            print(f"408 : {receiver} doesn't exist")
            message = f"408 : {receiver} doesn't exist"
            logging.info(message)
            client.send(message.encode())
        
    #refuser la requête de messages privés 
    def refuse(self,client_to_respond,client_receiving_response):
        if client_receiving_response in self.clients.values():
            if client_receiving_response in self.request.values():
                if client_receiving_response == self.clients[client_to_respond]:
                    message = f"419 : {self.clients[client_to_respond]} you can't use this command to yourself"
                    logging.info(message)
                    client_to_respond.send(message.encode())
                else:
                    message = f"200 : {self.clients[client_to_respond]} refused to have a private chat with you."
                    logging.info(message)
                    message2 = f"200 : you refused the request of {client_receiving_response}"
                    logging.info(message2)
                    for key, valeur in self.clients.items(): 
                        if client_receiving_response == valeur: 
                            client_receiving_response_sock = key
                            del self.request[client_receiving_response_sock]
                            del self.request[client_to_respond]
                    client_receiving_response_sock.send(message.encode())
                    client_to_respond.send(message2.encode())
            else:
                msg = "400 : you don't have any resquest to refuse"
                logging.info(msg)
                client_to_respond.send(msg.encode())
        else:
            print(f"408 {client_receiving_response} doesn't exist")
            message = f"408 {client_receiving_response} doesn't exist"
            logging.info(message)
            client_to_respond.send(message.encode())
            

        
    #accepter la requête de messages privées
    def accept(self,client_to_respond,client_receiving_response):
        if client_receiving_response in self.clients.values():
            if client_receiving_response in self.request.values():
                if client_receiving_response == self.clients[client_to_respond]:
                    message = f"419 : {self.clients[client_to_respond]} you can't use this command to yourself"
                    logging.info(message)
                    client_to_respond.send(message.encode())
                    
                else:
                    message = f"200 : {self.clients[client_to_respond]} accepted to have a private chat with you."
                    logging.info(message)
                    message2 = f"200 : you accepted the private chat of {client_receiving_response}"
                    for key, valeur in self.clients.items(): 
                        if client_receiving_response == valeur: 
                            client_receiving_response_sock = key
                            self.private[client_to_respond] = self.clients[client_to_respond]
                            self.private[client_receiving_response_sock] = self.clients[client_receiving_response_sock]
                            del self.request[client_receiving_response_sock]
                            del self.request[client_to_respond]

                    client_receiving_response_sock.send(message.encode())
            else:
                msg = "400 : you don't have any resquest to accept"
                logging.info(msg)
                client_to_respond.send(msg.encode())

        else:
            print(f"408 : {client_receiving_response} doesn't exist")
            message = f"408 : {client_receiving_response} doesn't exist"
            logging.info(message)
            client_to_respond.send(message.encode())

    #envoyer des messages privées 
    def tell(self,client_to_respond,message,client):
        if client_to_respond in self.clients.values():
            if client_to_respond in self.private.values():
                for key, valeur in self.private.items(): 
                    if client_to_respond == valeur: 
                        client_receiving_response_sock = key
                        if client_receiving_response_sock == client:
                            msg = "419 : you cant send a message to yourself"
                            logging.info(msg)
                            client_receiving_response_sock.send(msg.encode())
                        else:
                            msg = f"205 : {self.private[client]} : {message}"
                            logging.info(msg)
                            client_receiving_response_sock.send(msg.encode())
            elif self.clients[client] == client_to_respond:
                msg = "419 : you cant send a message to yourself"
                logging.info(msg)
                client.send(msg.encode())
            else:
                msg = "400 : you need to send a request first"
                logging.info(msg)
                client.send(msg.encode())
        else:
            msg = "408 : client doesnt exist"
            logging.info(msg)
            client.send(msg.encode())

    #arrêter les messages privées
    def stop(self,sender,client):
        if sender in self.clients.values():
            if sender in self.private.values():
                if self.clients[client] == sender:
                        message = "419 : you can't use this command to yourself"
                        logging.info(message)
                        client.send(message.encode())
                elif sender in self.private.values() and self.clients[client] in self.private.values():
                    message=f'206 : you stopped the private chat with {sender}'
                    logging.info(message)
                    client.send(message.encode())
                    del self.private[client]
                    for key, valeur in self.private.items(): 
                            if sender == valeur: 
                                sender_sock = key
                    message2=f'206 : {self.clients[client]} stopped the private chat with you'
                    logging.info(message2)
                    sender_sock.send(message2.encode())
                    del self.private[sender_sock]
                else:
                    message=f'410 : There is no private chat between you and {sender}'
                    logging.info(message)
                    client.send(message.encode())
            else:
                msg = "400 : the execution failed"
                logging.info(msg)
                client.send(msg.encode())
        else:
            msg = "408 : client doesnt exist"
            logging.info(msg)
            client.send(msg.encode())

    #envoyer une requête d'envoie de fichier
    def send_file(self,receiver,fichier,client):
        if receiver in self.clients.values():
            if receiver == self.clients[client]:
                message = f"419 : you can't send a file to yourself"
                client.send(message.encode())
            else:
                for key, valeur in self.clients.items(): 
                    if receiver == valeur : 
                        receiver_sock = key
                        message = f"100 : {self.clients[client]} wants to send you a file."
                        receiver_sock.send(message.encode())
                self.files_request[client] = self.clients[client]
                self.files_request[receiver_sock] = self.clients[receiver_sock]

        else:
            print(f"408 : {receiver} doesn't exist")
            message = f"408 : {receiver} doesn't exist"
            client.send(message.encode())

    #modifier le pseudo
    def verify_nickname(self,newNick,client):
        if newNick in self.clients.values():
            message=f'409 : {newNick} is already taken'
            logging.info(message)
            client.send(message.encode())
        else:   
            oldNick = self.clients[client]
            self.broadcast(f'208 : {self.clients[client]} is now {newNick}')
            logging.info('208 : {self.clients[client]} is now {newNick}')
            for key in self.clients:
                if key == client:
                    self.clients[client]=newNick
                    
                    
            if oldNick in self.request.values():
                print("je suis entrée dans le if des request")
                for key in self.request:
                    if key == client:
                        self.request[client] = newNick
                        
            if oldNick in self.private.values():
                 for key in self.private:
                    if key == client:
                        self.private[client] = newNick         
              

    #afficher la liste des commandes
    def liste_commandes(self,client):
        for key,value in self.commandes.items():
            client.send(f"202 {key}: {value} \n".encode())
            logging.info(f"202 {key}: {value} \n".encode())
            
    #accepter le fichier      
    def acceptFile(self,client_receiving_response,filename,port,address,client):
        if client_receiving_response in self.clients.values():
            if client_receiving_response in self.files_request.values():
                if client_receiving_response == self.clients[client]:
                    message = f"419 : you can't use this command to yourself"
                    client.send(message.encode())

                else:
                    message = f"210 : {self.clients[client]} accepted the download : {address} , {port} , {filename}"
                    message2 = f"210 : you accepted the file of {client_receiving_response}"
                    for key, valeur in self.clients.items(): 
                        if client_receiving_response == valeur: 
                            client_receiving_response_sock = key
                            del self.files_request[client_receiving_response_sock]
                            del self.files_request[client]


                    client_receiving_response_sock.send(message.encode())
                    client.send(message2.encode())
            else:
                msg = "400 : you don't have any request to refuse"
                client.send(msg.encode())

        else:
            print(f"408 {client_receiving_response} doesn't exist")
            message = f"408 {client_receiving_response} doesn't exist"
            client.send(message.encode())

    #refuser le fichier       
    def refuseFile(self,client_receiving_response,client):
        if client_receiving_response in self.clients.values():
            if client_receiving_response in self.files_request.values():
                if client_receiving_response == self.clients[client]:
                    message = f"419 : you can't use this command to yourself"
                    client.send(message.encode())
                else:

                    message = f"200 : {self.clients[client]} refused your request"
                    message2 = f"200 : you refused the file  of {client_receiving_response}"
                    for key, valeur in self.clients.items(): 
                        if client_receiving_response == valeur: 
                            client_receiving_response_sock = key
                            del self.files_request[client_receiving_response_sock]
                            del self.files_request[client]


                    client_receiving_response_sock.send(message.encode())
            else:
                msg = "400 : you don't have any resquest to refuse"
                client.send(msg.encode())

        else:
            print(f"408 {client_receiving_response} doesn't exist")
            message = f"408 {client_receiving_response} doesn't exist"
            client.send(message.encode())


    #liste des clients connectés
    def liste_clients(self,client):
        x = list(self.clients.values())
        x.sort()
        s=" ,".join(x)
        message=f'203 : {s}'
        logging.info(message)
        client.send(message.encode())

    #quitter le serveur
    def quit(self,client):
        message="207 : you have been disconnected"
        client.send(message.encode())
        name = self.clients[client]
        del self.clients[client]
        self.broadcast(f'207 : {name} disconnected')
        logging.info(f'207 : {name} disconnected')
        client.close()
        
    #créer un fichier de configuration
    def create_config(self):
        config = configparser.ConfigParser()
        config["settings"] = {"address":self.address,
        "port":self.port}
        with open("config.ini", "w") as fic:
            config.write(fic)
        return config


serveur = Server()
serveur.server_start()
print("server is listening ...")
serveur.receive()


