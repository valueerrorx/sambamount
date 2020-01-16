#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, string, ipaddress
from PyQt5 import QtCore, uic, QtWidgets
from PyQt5.QtGui import *
import configparser
import subprocess


USER = subprocess.check_output("logname", shell=True).rstrip().decode()
USER_HOME_DIR = os.path.join("/home", str(USER));


class MeinDialog(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        # load UI
        scriptdir=os.path.dirname(os.path.abspath(__file__))
        uifile=os.path.join(scriptdir,'winshare.ui')
        winicon=os.path.join(scriptdir,'blue.png')
        self.ui = uic.loadUi(uifile)        # load UI
        self.ui.setWindowIcon(QIcon(winicon))
     
        # setup Slots
        self.ui.exit.clicked.connect(self.onAbbrechen)
        self.ui.verbinden.clicked.connect(self.verbinden)
        self.ui.passwort.textChanged.connect(self.normalize)
        self.ui.speichern.clicked.connect(self.saveConfig)
   
        #init config
        self.sambastore = os.path.join(scriptdir,'SAMBA.DB')
        self.config = configparser.ConfigParser()
        self.config.read(self.sambastore)
        
        #setup ui
        self.ui.server.setText(self.config['default']['server']);
        self.ui.freigabe.setText(self.config['default']['customshare'])
        self.ui.mountpoint.setText(self.config['default']['mountpoint'])
        
        if (self.config['default']['sharetype'] == "1"):
            self.ui.radioButton1.setChecked(True)
        elif (self.config['default']['sharetype'] == "2"):
            self.ui.radioButton2.setChecked(True)
        elif (self.config['default']['sharetype'] == "3"):      
            self.ui.radioButton3.setChecked(True)
            self.ui.freigabe.setEnabled(True)
      
        #check for root permissions 
        if os.geteuid() != 0:
            print ("You need root access in order to create a live USB device")
            command = "pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY KDE_FULL_SESSION=true  %s" % (os.path.abspath(__file__))
            self.ui.close()
            os.system(command)
            os._exit(0)
      
      
      
    def saveConfig(self):
        if self.ui.radioButton1.isChecked():
            self.config['default']['sharetype'] = "1"
        elif self.ui.radioButton2.isChecked():
            self.config['default']['sharetype'] = "2"
        elif self.ui.radioButton3.isChecked():
            self.config['default']['sharetype'] = "3"
     
     
        self.config['default']['server'] = self.ui.server.text()
        self.config['default']['customshare'] = self.ui.freigabe.text()
        self.config['default']['mountpoint'] = self.ui.mountpoint.text()
      
        with open(self.sambastore, 'w') as configfile:
            self.config.write(configfile)
            self.ui.status.setText("Konfiguration gespeichert")
      

    def checkPW(self,pw):
        if not pw.isspace() and not (' ' in pw) == True:
            palettedefault = self.ui.passwort.palette()
            palettedefault.setColor(QPalette.Active, QPalette.Base, QColor(255, 255, 255))
            self.ui.passwort.setPalette(palettedefault)
            return True
        else:
            palettewarn = self.ui.passwort.palette()
            palettewarn.setColor(self.ui.passwort.backgroundRole(), QColor(200, 80, 80))
            self.ui.passwort.setPalette(palettewarn)
            self.ui.status.setText("Das Passwort enthält ungültige Zeichen")
            return False

    def normalize(self):
        palettedefault = self.ui.passwort.palette()
        palettedefault.setColor(QPalette.Active, QPalette.Base, QColor(255, 255, 255))
        self.ui.passwort.setPalette(palettedefault)




    def verbinden(self):
        print("verbinden")
        self.ui.status.setText("Verbindung angefordert")
        server = self.ui.server.text()
        benutzername = self.ui.benutzer.text()
        passwort = self.ui.passwort.text()
        mountpoint = self.ui.mountpoint.text()
        mountpoint = os.path.join(USER_HOME_DIR, mountpoint)
        
        if not os.path.isdir(mountpoint):
            os.makedirs(mountpoint)
        
        
        freigabename = ""
        if self.ui.radioButton1.isChecked() and self.checkPW(benutzername) and benutzername:
                freigabename = "%s$" %(benutzername)
        elif self.ui.radioButton2.isChecked():
            if self.checkPW(benutzername):
                freigabename = benutzername
        elif self.ui.radioButton3.isChecked():
            freigabename =  self.ui.freigabe.text()
            
            
        if self.checkPW(passwort):
            #connect
            if self.checkPW(benutzername) and benutzername:
                #command="exec dolphin smb://%s:%s@%s/%s &" %(benutzername,passwort,server,freigabename)
                
                command="sudo mount -t cifs -o user=%s,password=%s //%s/%s /%s"   %(benutzername, passwort, server, freigabename, mountpoint )

                print(command)
               # os.system(command)
               # self.ui.close()

   
    



    def onAbbrechen(self):    # Exit button
        print("GUI closed")
        self.ui.close()




app = QtWidgets.QApplication(sys.argv)
dialog = MeinDialog()
dialog.ui.show()
sys.exit(app.exec_())
