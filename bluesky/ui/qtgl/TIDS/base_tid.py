import bluesky as bs
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from bluesky.ui.qtgl import console, gui
from bluesky.ui.qtgl.TIDS import *
from bluesky.tools import misc
import platform
import os


def show_basetid(name, layout):
    globals()[str(name)] = QDialog()
    uic.loadUi(os.path.join(bs.settings.gfx_path, 'TID_Base.ui'), globals()[str(name)])
#    uic.loadUi('C:/Users/LVNL_ILAB3/Desktop/bluesky-lvnl_2/bluesky-master2/data/graphics/TID_Base.ui', globals()[str(name)])

    tid_load = 'bs.ui.qtgl.TID_Function.' + layout
    dlgbuttons = eval(tid_load)

    for i in range(len(dlgbuttons)):
        loop_button = 'pushButton_'+str(dlgbuttons[i][0])
        exec(name+'.'+loop_button+'.setText(dlgbuttons[i][1])')
        if dlgbuttons[i][2] != None:
            # Check for multiple functions
            if isinstance(dlgbuttons[i][2], list):
                for func in dlgbuttons[i][2]:
                    exec(name + '.' + loop_button + '.clicked.connect(' + func + ')')
            else:
                exec(name + '.' + loop_button + '.clicked.connect(' + dlgbuttons[i][2] + ')')
        else:
            exec(name+'.' + loop_button + '.setStyleSheet("border: 0px solid red;")')

    globals()[str(name)].setWindowTitle("Function TID")
    globals()[str(name)].setWindowModality(Qt.WindowModal)
    # gui.win.windowHandle().setScreen(app.screens()[1])
    # globals()[str(name)].move(globals()[str(name)].left(), globals()[str(name)].top())
    globals()[str(name)].showMaximized()
    globals()[str(name)].setWindowFlag(Qt.WindowMinMaxButtonsHint)
    globals()[str(name)].exec()

def show_basetid2(name, layout):
    globals()[str(name)] = QDialog()
    uic.loadUi(os.path.join(bs.settings.gfx_path, 'TID_Base.ui'), globals()[str(name)])
#    uic.loadUi('C:/Users/LVNL_ILAB3/Desktop/bluesky-lvnl_2/bluesky-master2/data/graphics/TID_Base.ui', globals()[str(name)])

    tid_load = 'bs.ui.qtgl.TID_Display.' + layout
    dlgbuttons = eval(tid_load)

    for i in range(len(dlgbuttons)):
        loop_button = 'pushButton_'+str(dlgbuttons[i][0])
        exec(name+'.'+loop_button+'.setText(dlgbuttons[i][1])')
        if dlgbuttons[i][2] != None:
            # Check for multiple functions
            if isinstance(dlgbuttons[i][2], list):
                for func in dlgbuttons[i][2]:
                    exec(name + '.' + loop_button + '.clicked.connect(' + func + ')')
            else:
                exec(name + '.' + loop_button + '.clicked.connect(' + dlgbuttons[i][2] + ')')
        else:
            exec(name+'.' + loop_button + '.setStyleSheet("border: 0px solid red;")')

    globals()[str(name)].setWindowTitle("Display TID")
    globals()[str(name)].setWindowModality(Qt.WindowModal)
    globals()[str(name)].showMaximized()
    globals()[str(name)].setWindowFlag(Qt.WindowMinMaxButtonsHint)
    globals()[str(name)].exec()


# def tidclose(command, dialogname):
def tidclose(command, dialogname):
    lambda: command
    globals()[str(dialogname)].close()
    bs.ui.qtgl.console.Console._instance.stack(bs.ui.qtgl.console.Console._instance.command_line)


class TIDCmds:
    """
    Class definition: Process inputs coming from the TID
    Methods:
        clear():            Clear variables
        update_cmdline():   Update the command line
        exq():              Execute commandline
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

        actdata = bs.net.get_nodedata()
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

            # Check if selected aircraft is UCO
            if actdata.acdata.uco[idx] or 'UCO' in self.cmdslst:

                cmdline = ''

                # Loop over commands
                for cmd, args in zip(self.cmdslst, self.argslst):
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
    def exqcmd(cmd, arg=''):
        """
        Function: Execute a command
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
        actdata = bs.net.get_nodedata()
        id_select = console.Console._instance.id_select

        # Check if an aircraft is selected
        if id_select:
            # Command line
            cmdline = id_select + ' ' + cmd + ' ' + arg
            cmdline = cmdline.strip()

            # Stack the command
            console.Console._instance.stack(cmdline)
        else:
            bs.scr.echo('No aircraft selected')

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


tidcmds = TIDCmds()
