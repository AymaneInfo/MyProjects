from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QMessageBox, QInputDialog, QPushButton, QDialog, QDialogButtonBox, QMenu, QAction, QFileDialog
from PyQt5.QtGui import QTextCursor, QStandardItemModel
from fenetre import Ui_TchatDNC
from client import Client
from conndialog import ConnDialog

import threading, time

class Tchat(QMainWindow, Ui_TchatDNC):

    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)
        connexion = ConnDialog()

        if connexion.exec_() == QDialog.Accepted:
            val = connexion.getVal()
        self.user = Client(val["nickname"], val["address"], val["port"])
        self.user.connect()

        self.file_to_send = ""

        self.setupUi(self)
        self.setWindowTitle("DNC Chat")
        self.msgArea.returnPressed.connect(self.chat)

        self.butChat.clicked.connect(self.chat)
        self.butState.clicked.connect(self.change_state)
        self.butHelp.clicked.connect(lambda: self.use_command("HELP"))
        self.butEdit.clicked.connect(self.new_nickname)

        self.listUser.installEventFilter(self)
        self.threadRec = threading.Thread(target = self.receive)
        self.threadRec.start()

    def use_command(self, command, *args):
        message = command
        for arg in args:
            message += " " + arg
        self.user.client.send(message.encode())

    def update_list(self):
        self.use_command("LIST")
        reponse = self.user.client.recv(1024).decode('ascii')
        message = reponse.split(":",1)[1].strip()

        self.listUser.clear()

        self.sendTo.clear()
        self.sendTo.addItem("Everyone")
        self.sendTo.setCurrentIndex(0)

        for user in message.split(","):
            self.listUser.addItem(user.strip())
            if(user.strip() != self.user.nickname):
                self.sendTo.addItem(user)

    def new_nickname(self):
        newNick, ok = QInputDialog.getText(self,"New nickname","Please enter your new nickname :")
        if ok:
            self.use_command("EDIT", newNick)
            self.user.nickname = newNick

    def chat(self):
        msg = self.msgArea.text().strip()
        if( len(msg) != 0):
            if(self.sendTo.currentText() == "Everyone"):
                self.use_command("CHAT", msg)
            else:
                self.use_command("TELL", self.sendTo.currentText(), msg)
            self.msgArea.clear()

    def change_state(self):
        if(self.butState.text()=="Online"):
            self.butState.setText("AFK")
            self.use_command("ABS")
            self.butEdit.setEnabled(False)
        else:
            self.butState.setText("Online")
            self.butEdit.setEnabled(True)
            self.use_command("BACK")
            
    def receive(self):
        gaveNick = False
        while True:
            self.chatbox.moveCursor(QTextCursor.End)
            try:
                reponse = self.user.client.recv(1024).decode('ascii')

                if not gaveNick:
                    self.user.client.send(self.user.nickname.encode('utf-8'))
                    gaveNick = True

                else:
                    code = reponse.split(":",1)[0].strip()
                    message = '<p style= "color: white">' + reponse.split(":",1)[1].strip() + '</p>'

                    if (code.startswith("2")):
                        if(code == "210" and "accepted the download" in reponse):
                            argument = reponse.split(":")[2].split(",")
                            self.user.send_file(argument[0].strip(), int(argument[1].strip()), self.file_to_send)

                        if(code == "207" and reponse.split(":",1)[1].strip().startswith("you")):
                            break

                        if(code == "206" or code == "207" or code == "208"):
                            self.update_list()
                        
                        if (code == "205"):
                            message = '<p style= "color: purple">' + reponse.split(":",1)[1].strip() + '</p>'

                        self.chatbox.append(message)

                    if (code.startswith("1")):
                        request = QMessageBox()
                        request.setText(message)
                        request.setWindowTitle("Request")
                        request.exec()

                    if (code.startswith("4")):
                        alert = QMessageBox()
                        alert.setText(message)
                  
                        alert.setWindowTitle("Error")
                        alert.setIcon(QMessageBox.Critical)
                        alert.exec()

            except:
                print(reponse)
                print("an error has occured!")
                self.use_command("QUIT")
                break

    #Gestion fermeture de la fenêtre
    def closeEvent(self , event):
        self.use_command("QUIT")
        for thread in threading.enumerate():
            if thread != threading.main_thread(): thread.join()
        self.close()

    #Gestion sous-menu de la liste des utilisateurs
    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.ContextMenu and source is self.listUser:
            menu = QMenu()
            privatechatAction = QAction("Send private chat request")
            acceptAction = QAction("Accept a private chat")
            refuseAction = QAction("Refuse a private chat")
            stopAction = QAction("Stop a private chat")
            sendfileAction = QAction("Send file request")
            acceptfileAction = QAction("Accept a file download")
            refusefileAction = QAction("Refuse a file download")


            menu.addAction(privatechatAction)
            menu.addAction(acceptAction)
            menu.addAction(refuseAction)
            menu.addAction(stopAction)
            menu.addAction(sendfileAction)
            menu.addAction(acceptfileAction)
            menu.addAction(refusefileAction)

            action = menu.exec(event.globalPos())
            
            userclicked = source.itemAt(event.pos())
            
            if userclicked != None:
                receiver = userclicked.text().strip()

                if action == privatechatAction:
                    self.use_command("SEND", receiver)
                
                if action == acceptAction:
                    self.use_command("ACCEPT", receiver)

                if action == refuseAction:
                    self.use_command("REFUSE", receiver)
                
                if action == stopAction:
                    self.use_command("STOP", receiver)

                if action == sendfileAction:
                    filename, _ = QFileDialog.getOpenFileName(None, "Open File", "", "All Files (*.*)", options=QFileDialog.DontUseNativeDialog)
                    
                    if filename:
                        self.file_to_send = filename.split("/")[-1]
                        self.use_command("SFIC", receiver, self.file_to_send)
                    
                if action == acceptfileAction:
                    connexion = ConnDialog()
                    connexion.labNick.setText("File name")
                    if connexion.exec_() == QDialog.Accepted:
                        val = connexion.getVal()
    
                    self.use_command("ACCEPTFILE", receiver, val["nickname"], str(val["port"]), val["address"])
                    self.user.accept_file(val["address"], val["port"], val["nickname"])

                if action == refusefileAction:
                    self.use_command("REFUSEFILE", receiver)
                
                return True
        return super().eventFilter(source,event)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = Tchat()
    win.show()
    sys.exit(app.exec())    
    
