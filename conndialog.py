from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLineEdit, QLabel
import socket

class ConnDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Connexion")

        QBtn = QDialogButtonBox.Cancel | QDialogButtonBox.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.verifyVal)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()

        self.labNick = QLabel("Nickname :")
        self.labAdr = QLabel("Address :")
        self.labPort = QLabel("Port :")

        self.txtNick = QLineEdit()
        self.txtAdr = QLineEdit("127.0.0.1")
        self.txtPort = QLineEdit()

        self.layout.addWidget(self.labNick)
        self.layout.addWidget(self.txtNick)

        self.layout.addWidget(self.labAdr)
        self.layout.addWidget(self.txtAdr)

        self.layout.addWidget(self.labPort)
        self.layout.addWidget(self.txtPort)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def verifyVal(self):
        nick = self.txtNick.text().strip()
        addr = self.txtAdr.text().strip()
        port = self.txtPort.text().strip()

        valid = True

        if (port.isdigit() and len(port) > 0):
            port = int(port)
            if ( port <= 1 or port >= 65535):
                valid = False
        else:
            valid = False

        if ( ',' in nick != 0 or len(nick) == 0):
            valid = False
        
        if ( not self.verifyAddr(addr) ):
            valid = False

        if (valid):
            self.accept()
        
    def verifyAddr(self, addr):
        try:
            socket.inet_aton(addr)
            return True
        except:
            return False

    def getVal(self):
        val = {"nickname" : self.txtNick.text().strip(), "address" : self.txtAdr.text(), "port" : int(self.txtPort.text())}
        return val
