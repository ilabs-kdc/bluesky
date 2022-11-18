"""
LVNL TID Gui

Created by: Bob van Dillen
Date: 29-10-2022
"""

import socket
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QPushButton
from PyQt5.QtGui import QFont
from PyQt5 import uic
import xml.etree.ElementTree as ET
import os
import pickle

import bluesky as bs
from bluesky.tools import cachefile
from bluesky.ui.qtgl import console

tiddb_version = 'v20221030'


class TIDGui(QDialog):
    """
    Definition: LVNL TID Gui
    Methods:
        start():            Start the TID
        change_tid():       Change the TID layout
        set_layout:         Set the TID layout
        set_buttons():      Set the TID buttons
        eval_function():    Evaluate the button function
        load_layouts():     Load the TID layouts
        read_layout():      Read the TID layout file

    Created by: Bob van Dillen
    Date: 29-10-2022
    """

    def __init__(self, name):
        self.running = False

        self.name = name
        self.layoutname = ''

        self.layouts = dict()
        self.load_layouts()

        self.ac_selected = ''
        self.rwy = ''

        if name == 'Function-TID':
            bs.Signal('idselect').connect(self.TID_refresh)

        QDialog.__init__(self)

        # Create Dialog
        uic.loadUi(os.path.join(bs.settings.gfx_path, 'TID_Base.ui'), self)

        # Window settings
        self.setWindowTitle(self.name)
        self.setWindowModality(Qt.WindowModal)

        # PC specific settings
        host = socket.gethostbyname(socket.gethostname())
        if self.name == 'Function-TID' and host in ['192.168.0.6']:
            self.setGeometry(500, 200, 300, 250)
            self.move(2500, 2500)
            self.showMaximized()
            self.setWindowFlags(Qt.WindowMinMaxButtonsHint | Qt.FramelessWindowHint)
        elif self.name == 'Display-TID' and host in ['192.168.0.6']:
            self.setGeometry(500, 200, 300, 250)
            self.move(0, 2500)
            self.showMaximized()
            self.setWindowFlags(Qt.WindowMinMaxButtonsHint | Qt.FramelessWindowHint)
        else:
            self.setWindowFlag(Qt.WindowMinMaxButtonsHint)

    def start(self, layoutname):
        """
        Function: Start the TID
        Args:
            layoutname: Layout name [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 29-10-2022
        """

        # Check if alread opened
        if self.running:
            bs.scr.echo("TID: '"+self.name+"' already opened")
            print("TIDGui: '"+self.name+"' already opened")
            return

        # Set layout
        dlgbuttons = self.set_layout(layoutname)
        if not dlgbuttons:
            return

        # Set buttons
        self.set_buttons(dlgbuttons)

        # Start
        self.running = True
        self.exec()
        self.close()

    def close(self) -> bool:
        """
        Function: Close the TID
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 30-10-2022
        """

        super().close()

        self.running = False

    def change_tid(self, layoutname, **kwargs):
        """
        Function: Change the TID layout
        Args:
            layoutname: Layout name [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 29-10-2022
        """

        if 'rwy' in kwargs:
            if kwargs['rwy'] == '18R':
                self.rwy = 'apphdg18R'
            elif kwargs['rwy'] == '18C':
                self.rwy = 'apphdg18C'

        if self.rwy != '' and layoutname == 'apphdg':
            layoutname = self.rwy


        # Set layout
        dlgbuttons = self.set_layout(layoutname)
        if not dlgbuttons:
            return

        # Set buttons
        self.set_buttons(dlgbuttons)

    def set_layout(self, layoutname):
        """
        Function: Set the TID layout
        Args:
            layoutname: Layout name [str]
        Returns:
            False:      Layout not found [bool]
            dlgbuttons: Buttons information [list]

        Created by: Bob van Dillen
        Date: 30-10-2022
        """

        # Get buttons information
        dlgbuttons = self.layouts.get(layoutname)

        # Check if successfully
        if dlgbuttons is None:
            bs.scr.echo("TID: Layout '" + layoutname + "' not found")
            print("TIDGui: Layout '" + layoutname + "' not found")
            return False
        else:
            self.layoutname = layoutname
            return dlgbuttons

    def set_buttons(self, dlgbuttons):
        """
        Function: Set the TID buttons
        Args:
            dlgbuttons: Buttons information [list]
        Returns: -

        Created by: Bob van Dillen
        Date: 29-10-2022
        """

        for i in range(len(dlgbuttons)):
            button = eval('self.pushButton_' + str(dlgbuttons[i][0]))

            # Reset button variables
            try:
                button.clicked.disconnect()
            except TypeError:
                pass

            button.setStyleSheet("color: rgb(180, 200, 139);"
                                 "border: 4px solid red;"
                                 "border-color: rgb(180, 200, 139);"
                                 "background-color: rgb(17, 12, 12);")

            button.setFont(QFont("Arial Black", 28))

            # Set the button text
            if dlgbuttons[i][1] != "":
                button.setText(dlgbuttons[i][1])
            else:
                button.setText("")
                button.setStyleSheet("border: 0px solid red;")
                continue

            # Set the button function
            for func in dlgbuttons[i][2]:
                button = self.eval_function(button, func)

    def eval_function(self, button, func):
        """
        Function: Evaluate the button function
        Args:
            button: Button attribute [QPushButton]
            func:   Function [str]
        Returns:
            button: Button attribute [QPushButton]

        Created by: Bob van Dillen
        Date: 30-10-2022
        """

        if func.startswith('change_tid'):
            layoutname = func.replace('change_tid(', '').replace(')', '').replace('"', '').replace("'", "")
            button.clicked.connect(lambda: self.change_tid(layoutname))
        else:
            button.clicked.connect(eval('lambda: '+func))

        return button

    def TID_refresh(self, acid):
        """
        Function: that is executed when a different aircraft is selected. Required for the refresh of the Function-TID
                  when a different aircraft is selected.
        Args:
            acid: new selected aircraft

        Created by: Bob van Dillen & Lars Dijkstra
        Date: 17-11-2022
        """

        if self.ac_selected != acid and acid != '':
            actdata = bs.net.get_nodedata()
            index = actdata.acdata.id.index(acid)
            rwy = actdata.acdata.rwy[index]
            self.change_tid('appmain', rwy=rwy)

        self.ac_selected = acid

    def load_layouts(self):
        """
        Function: Load the TID layouts
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 29-10-2022
        """

        folder = os.path.join(bs.settings.gfx_path, 'tids')

        # with cachefile.openfile('tidlayouts.p', tiddb_version) as cache:
        #     try:
        #         self.layouts = cache.load()
        #     except (pickle.PickleError, cachefile.CacheError) as e:
        #         print(e.args[0])
        #
        #         # Loop over files
        #         for root, dirs, files in os.walk(folder):
        #
        #             for file in files:
        #                 # Skip README
        #                 if file == 'README.md':
        #                     continue
        #
        #                 self.read_layout(root, file)
        #
        #         cache.dump(self.layouts)
        for root, dirs, files in os.walk(folder):
                for file in files:
                    # Skip README
                    if file == 'README.md':
                        continue

                    self.read_layout(root, file)

    def read_layout(self, folder, file):
        """
        Function: Read the TID layout file
        Args:
            folder: Path to the folder [str]
            file:   file name [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 29-10-2022
        """

        # Parse file
        tree = ET.parse(os.path.join(folder, file))
        root = tree.getroot()

        # Loop over layouts
        for layout in root:
            layoutlst = []

            # Loop over buttons
            for btn in layout:
                btnlst = [btn.attrib['id']]

                # New line and tab
                btn.attrib['text'] = btn.attrib['text'].replace('*n*', '\n').replace('*t*', '\t')
                # > and <
                btn.attrib['text'] = btn.attrib['text'].replace('*gt*', '>').replace('*lt*', '<')
                # Ampersand
                btn.attrib['text'] = btn.attrib['text'].replace('*amp*', '&')

                btnlst.append(btn.attrib['text'])

                # Functions
                funclst = []
                for i in range(len(btn.attrib)-2):
                    funclst.append(btn.attrib['function'+str(i)])
                btnlst.append(funclst)

                layoutlst.append(btnlst)

            self.layouts[layout.tag] = layoutlst
