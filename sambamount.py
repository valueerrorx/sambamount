#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, string, ipaddress
from PyQt5 import QtCore, uic, QtWidgets
from PyQt5.QtGui import *
import configparser
import subprocess
from subprocess import PIPE, run
import time 


USER = subprocess.check_output("logname", shell=True).rstrip().decode()
UID = subprocess.check_output(f"id -u {USER}", shell=True).rstrip().decode()
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
            print ("You need root access in order to mount a network folder")
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
        if not pw.isspace() and not (' ' in pw) == True and pw != "":
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

    def checkUsername(self,pw):
        if not pw.isspace() and not (' ' in pw) == True and pw != "":
            palettedefault = self.ui.benutzer.palette()
            palettedefault.setColor(QPalette.Active, QPalette.Base, QColor(255, 255, 255))
            self.ui.benutzer.setPalette(palettedefault)
            return True
        else:
            palettewarn = self.ui.benutzer.palette()
            palettewarn.setColor(self.ui.benutzer.backgroundRole(), QColor(200, 80, 80))
            self.ui.benutzer.setPalette(palettewarn)
            self.ui.status.setText("Der Benutzername enthält ungültige Zeichen")
            return False


    def normalize(self):
        palettedefault = self.ui.passwort.palette()
        palettedefault.setColor(QPalette.Active, QPalette.Base, QColor(255, 255, 255))
        self.ui.passwort.setPalette(palettedefault)




    def verbinden(self):

        self.ui.status.setText("Anmeldedaten holen")
        server = self.ui.server.text()
        benutzername = self.ui.benutzer.text()
        passwort = self.ui.passwort.text()
        mountpoint = self.ui.mountpoint.text()
        mountpoint = os.path.join(USER_HOME_DIR, mountpoint)
        freigabename = self.ui.freigabe.text()
        result = False
        
        if not os.path.isdir(mountpoint):
            os.makedirs(mountpoint)
        
   
        if self.checkUsername(benutzername) and self.checkPW(passwort):
            
            if self.ui.radioButton1.isChecked():
                freigabename = benutzername
            elif self.ui.radioButton2.isChecked():
                freigabename = "%s$" %(benutzername)
            elif self.ui.radioButton3.isChecked(): #ohne benutzerkennung
                freigabename = self.ui.freigabe.text()
        
            #connect
            self.ui.status.setText("Verbindung angefordert")
            command = ["sudo","mount", "-t", "cifs","-o",f"rw,user={benutzername},password='{passwort}',uid={UID},gid={UID}",f"//{server}/{freigabename}", f"/{mountpoint}"] 
            result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
            
        else:
            self.ui.status.setText("Bitte überprüfen sie die Anmeldedaten")
    
        
        

        if result:
            print(result.stderr)

            if ( "error" in  result.stderr):
                self.ui.status.setText("Fehlerhafte Anmeldedaten")
            else:
                self.ui.status.setText("Verbindung hergestellt")
                time.sleep(2)
                self.openFilemanager(mountpoint)
            






    def openFilemanager(self, mountpoint):
        command="sudo -H -u %s dolphin %s > /dev/null 2>&1" %(USER, mountpoint)
        os.system(command)



    def onAbbrechen(self):    # Exit button
        print("GUI closed")
        self.ui.close()




app = QtWidgets.QApplication(sys.argv)
dialog = MeinDialog()
dialog.ui.show()
sys.exit(app.exec_())
