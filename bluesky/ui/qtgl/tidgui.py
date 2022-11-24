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
from bluesky.tools import cachefile, misc
from bluesky.ui.qtgl import console

tiddb_version = 'v20221030'


"""
TID GUI
"""


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

        bs.net.actnodedata_changed.connect(self.actdata_changed)

        QDialog.__init__(self)

        # Create Dialog
        uic.loadUi(os.path.join(bs.settings.gfx_path, 'TID_Base.ui'), self)

        # Window settings
        self.setWindowTitle(self.name)
        self.setWindowModality(Qt.WindowModal)

        # PC specific settings
        host = socket.gethostbyname(socket.gethostname())
        if self.name == 'Function-TID' and host in ['192.168.0.6', '192.168.0.8']:
            self.setGeometry(500, 200, 300, 250)
            self.move(2500, 2500)
            self.showMaximized()
            self.setWindowFlags(Qt.WindowMinMaxButtonsHint | Qt.FramelessWindowHint)
        elif self.name == 'Display-TID' and host in ['192.168.0.6', '192.168.0.8']:
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
            elif kwargs['rwy'] == '06':
                self.rwy = 'apphdg06'
            elif kwargs['rwy'] == '36R':
                self.rwy = 'apphdg36R'
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
        elif func.split('(')[0] in ['exq', 'exqcmd', 'exqaccmd', 'clr', 'cor', 'setcmd',
                                    'changecmd', 'setarg', 'addarg', 'addchar']:
            button.clicked.connect(eval('lambda: console.Console._instance.tidcmds.'+func))
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

        actdata = bs.net.get_nodedata()

        if self.ac_selected != acid and acid != '' and actdata.atcmode != 'ACC':
            index = actdata.acdata.id.index(acid)
            rwy = actdata.acdata.rwy[index]
            self.change_tid('appmain', rwy=rwy)

        self.ac_selected = acid

    def actdata_changed(self, nodeid, nodedata, changed_elems):
        """
        Function: Update buffers when a different node is selected, or when the data of the current node is updated.
        Args:
            nodeid:         ID of the Node [bytes]
            nodedata:       The Node data [class]
            changed_elems:  The changed elements [list]
        Returns: -

        Created by: Bob van Dillen
        Date: 22-11-2022
        """

        if 'ATCMODE' in changed_elems:
            if nodedata.atcmode in ['APP', 'ACC']:
                if self.name == 'Function-TID':
                    print(nodedata.atcmode.lower()+'main')
                    self.change_tid(nodedata.atcmode.lower()+'main')
                elif self.name == 'Display-TID':
                    self.change_tid(nodedata.atcmode.lower()+'disp')

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


"""
TID Commands
"""


class TIDCmds:
    """
    Class definition: Process inputs coming from the TID
    Methods:
        clear():            Clear variables
        update_cmdline():   Update the command line

        Usable in TID:
        exq():              Execute commandline
        exqaccmd():         Execute an aircraft command
        exqcmd():           Execute a command
        clr():              Clear command
        cor():              Correct command
        setcmd():           Set a command
        changecmd():        Change the current command
        setarg():           Set an argument
        addarg():           Add an argument
        addchar():          Add a character

    Created by: Bob van Dillen
    Date: 28-1-2022
    """

    def __init__(self):
        self.cmdslst = []
        self.argslst = []

        self.iact = 0

    def clear(self):
        """
        Function: Clear variables
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        self.cmdslst = []
        self.argslst = []

        self.iact = 0

    def update_cmdline(self):
        """
        Function: Update the command line
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        id_select = console.Console._instance.id_select

        cmdline = id_select.strip() + ' ; '

        # Loop over commands
        for cmd, args in zip(self.cmdslst, self.argslst):
            cmdline += cmd
            # Loop over arguments for this command
            for arg in args:
                cmdline += ' ' + arg

            cmdline += ' ; '

        cmdline = cmdline[:-3]  # Remove last ' ; '

        # Set the command line
        console.Console._instance.set_cmdline(cmdline, 1)

    def exq(self):
        """
        Function: Execute commandline
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        actdata = bs.net.get_nodedata()
        id_select = console.Console._instance.id_select

        # Check if an aircraft is selected
        if id_select:
            idx = misc.get_indices(actdata.acdata.id, id_select)[0]
            IPaddr = socket.gethostbyname(socket.gethostname())[-11:]

            # Check if selected aircraft is UCO
            if actdata.acdata.uco[idx] == IPaddr or 'UCO' in self.cmdslst:

                cmdline = ''

                # Loop over commands
                for cmd, args in zip(self.cmdslst, self.argslst):

                    # Handle UCO command
                    if cmd == 'UCO':
                        cmdline += 'UCO ' + id_select + ' ' + IPaddr + ' ; '
                        continue

                    # Handle altitude command
                    if cmd == 'EFL':
                        cmd = 'ALT'
                        addfl = True
                    else:
                        addfl = False

                    cmdline += id_select + ' ' + cmd

                    # Loop over arguments for this command
                    for arg in args:
                        if addfl:
                            cmdline += ' FL' + arg
                        else:
                            cmdline += ' ' + arg

                    cmdline += ' ; '

                cmdline = cmdline[:-3]  # Remove last ' ; '

                # Stack the command line
                console.Console._instance.stack(cmdline)
            else:
                bs.scr.echo(id_select+' not UCO')
        else:
            bs.scr.echo('No aircraft selected')

        # Clear
        self.clear()

        # Empty command line
        console.Console._instance.set_cmdline('')

    @staticmethod
    def exqaccmd(cmd, arg=''):
        """
        Function: Execute an aircraft command
        Args:
            cmd:    command [str]
            arg:    argument [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        cmd = cmd.strip().upper()
        arg = arg.strip()

        # Selected aircraft
        id_select = console.Console._instance.id_select

        # Check if an aircraft is selected
        if id_select:
            # Check for UCO
            if cmd.upper() == 'UCO':
                IPaddr = socket.gethostbyname(socket.gethostname())[-11:]
                cmdline = 'UCO ' + id_select + ' ' + IPaddr
            else:
                cmdline = id_select + ' ' + cmd + ' ' + arg
                cmdline = cmdline.strip()

            # Stack the command
            console.Console._instance.stack(cmdline)
        else:
            bs.scr.echo('No aircraft selected')

    @staticmethod
    def exqcmd(cmd, arg=''):
        """
        Function: Execute a command
        Args:
            cmd:    command [str]
            arg:    argument [str]
            acid:   Add the selected aircraft [bool]
        Returns: -

        Created by: Bob van Dillen
        Date: 18-11-2022
        """

        # Command line
        cmdline = cmd + ' ' + arg
        cmdline = cmdline.strip()

        # Stack the command
        console.Console._instance.stack(cmdline)

    def clr(self):
        """
        Function: Clear command
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        self.argslst[self.iact] = ['']

        # Set the command line
        self.update_cmdline()

    def cor(self):
        """
        Function: Correct command
        Args: -
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        # Clear
        self.clear()

        # Update the command line
        console.Console._instance.set_cmdline('')

    def setcmd(self, cmd):
        """
        Function: Set a command
        Args:
            cmd:    command [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        cmd = cmd.strip().upper()

        if cmd in self.cmdslst:
            # Get index
            self.iact = self.cmdslst.index(cmd)
        else:
            # Unfinished previous command
            if len(self.cmdslst) != 0 and self.cmdslst[self.iact] not in ['UCO', 'REL'] and self.argslst[self.iact] == ['']:
                self.cmdslst[self.iact] = cmd
                self.argslst[self.iact] = ['']
            # Finished previous command
            else:
                # Append new command
                self.cmdslst.append(cmd)
                self.argslst.append([''])

                # Index
                self.iact = len(self.cmdslst) - 1

        # Update command line
        self.update_cmdline()

    def changecmd(self, cmd):
        """
        Function: Change the current command
        Args:
            cmd:    command [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        cmd = cmd.strip().upper()

        # Change command
        self.cmdslst[self.iact] = cmd
        # Clear arguments
        self.argslst[self.iact] = ['']

        # Update command line
        self.update_cmdline()

    def setarg(self, arg, argn):
        """
        Function: Set an argument
        Args:
            arg:    argument [str]
            argn:   argument number (1, 2, ..., n) [int]
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        # Set the argument
        self.argslst[self.iact][argn-1] = arg.strip()

        # Update command line
        self.update_cmdline()

    def addarg(self, arg):
        """
        Function: Add an argument
        Args:
            arg:    argument [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        # Append argument
        self.argslst[self.iact].append(arg.strip())

        # Update command line
        self.update_cmdline()

    def addchar(self, char):
        """
        Function: Add a character
        Args:
            char:   character [str]
        Returns: -

        Created by: Bob van Dillen
        Date: 28-1-2022
        """

        # Append character
        self.argslst[self.iact][-1] += char.strip()

        # Update command line
        self.update_cmdline()