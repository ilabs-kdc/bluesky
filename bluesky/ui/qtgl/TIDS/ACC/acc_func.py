"""
This python file contains the button definitions for the ACC functional tid

Created by: Bob van Dillen
Date: 26-1-2022
"""


accmain = [['a1', 'DCT',            ['lambda: console.Console._instance.stack("EXQ CMD HDG")',
                                     'lambda: change_tid("TID_Function", "accdct")']],
           ['a2', 'HOLD/\nSWAP',    ['lambda: None']],
           ['a3', 'SSI',            ['lambda: None']],
           ['a4', '>>>>',           ['lambda: change_tid("TID_Function", "accdisp")']],

           ['b1', 'COORD',          ['lambda: None']],
           ['b2', 'AMA',            ['lambda: None']],
           ['b3', 'RTE\nEXQ',       ['lambda: None']],
           ['b4', 'ACOD\nMENU',     ['lambda: None']],

           ['c1', 'DPL',            ['lambda: None']],
           ['c2', 'LBL',            ['lambda: console.Console._instance.stack("EXQ CMD TRACKLABEL")']],
           ['c3', 'STR',            ['lambda: None']],
           ['c4', 'ERA',            ['lambda: None']],

           ['d1', 'TOC\nEXQ',       ['lambda: tidcmds.exqcmd("REL")']],
           ['d2', 'TOC',            ['lambda: console.Console._instance.stack("EXQ REL")']],
           ['d3', 'UCO\nEXQ',       ['lambda: tidcmds.exqcmd("UCO")']],
           ['d4', 'EC\nNKB',        ['lambda: None']],

           ['e1', 'EFL',            ['lambda: console.Console._instance.stack("EXQ CMD EFL")',
                                     'lambda: change_tid("TID_Function", "accefl")']],
           ['e2', 'HDG',            ['lambda: console.Console._instance.stack("EXQ CMD HDG")',
                                     'lambda: change_tid("TID_Function", "acchdg")']],
           ['e3', 'SPD',            ['lambda: console.Console._instance.stack("EXQ CMD SPD")',
                                     'lambda: change_tid("TID_Function", "accspd")']],
           ['e4', 'PLAY\nBACK',     ['lambda: change_tid("TID_Function", "accpbm")']],

           ['f1', 'COR',            ['lambda: None']],
           ['f2', 'REV\nEXQ',       ['lambda: None']],
           ['f3', 'ACK',            ['lambda: None']],
           ['f4', 'EXQ',            ['lambda: console.Console._instance.stack("EXQ EXQ")']]
           ]


accdct = [['a1', '',        None],
          ['a2', '',        None],
          ['a3', 'SUGOL',   ['lambda: console.Console._instance.stack("EXQ SETARG SUGOL")']],
          ['a4', 'NIRSI',   ['lambda: console.Console._instance.stack("EXQ SETARG NIRSI")']],

          ['b1', '',        None],
          ['b2', '',        None],
          ['b3', 'RIVER',   ['lambda: console.Console._instance.stack("EXQ SETARG RIVER")']],
          ['b4', 'SOKSI',   ['lambda: console.Console._instance.stack("EXQ SETARG SOKSI")']],

          ['c1', '',        None],
          ['c2', '',        None],
          ['c3', 'ARTIP',   ['lambda: console.Console._instance.stack("EXQ SETARG ARTIP")']],
          ['c4', 'PAM',     ['lambda: console.Console._instance.stack("EXQ SETARG PAM")']],

          ['d1', '',        None],
          ['d2', '',        None],
          ['d3', '',        None],
          ['d4', '',        None],

          ['e1', '',        None],
          ['e2', '',        None],
          ['e3', '',        None],
          ['e4', '',        None],

          ['f1', 'COR',     ['lambda: console.Console._instance.stack("EXQ COR")',
                             'lambda: change_tid("TID_Function", "accmain")']],
          ['f2', 'CLR',     ['lambda: console.Console._instance.stack("EXQ CLR")']],
          ['f3', 'ANKB',    ['lambda: None']],
          ['f4', 'EXQ',     ['lambda: console.Console._instance.stack("EXQ EXQ")',
                             'lambda: change_tid("TID_Function", "accmain")']]
          ]


accefl = [['a1', '',        None],
          ['a2', '',        None],
          ['a3', '',        None],
          ['a4', '',        None],

          ['b1', '',        None],
          ['b2', '',        None],
          ['b3', '',        None],
          ['b4', '',        None],

          ['c1', '7',       ['lambda: console.Console._instance.stack("EXQ CHAR 7")']],
          ['c2', '4',       ['lambda: console.Console._instance.stack("EXQ CHAR 4")']],
          ['c3', '1',       ['lambda: console.Console._instance.stack("EXQ CHAR 1")']],
          ['c4', '',        None],

          ['d1', '8',       ['lambda: console.Console._instance.stack("EXQ CHAR 8")']],
          ['d2', '5',       ['lambda: console.Console._instance.stack("EXQ CHAR 5")']],
          ['d3', '2',       ['lambda: console.Console._instance.stack("EXQ CHAR 2")']],
          ['d4', '0',       ['lambda: console.Console._instance.stack("EXQ CHAR 0")']],

          ['e1', '9',       ['lambda: console.Console._instance.stack("EXQ CHAR 9")']],
          ['e2', '6',       ['lambda: console.Console._instance.stack("EXQ CHAR 6")']],
          ['e3', '3',       ['lambda: console.Console._instance.stack("EXQ CHAR 3")']],
          ['e4', '',        None],

          ['f1', 'COR',     ['lambda: console.Console._instance.stack("EXQ COR")',
                             'lambda: change_tid("TID_Function", "accmain")']],
          ['f2', 'CLR',     ['lambda: console.Console._instance.stack("EXQ CLR")']],
          ['f3', '',        None],
          ['f4', 'EXQ',     ['lambda: console.Console._instance.stack("EXQ EXQ")',
                             'lambda: change_tid("TID_Function", "accmain")']]
          ]


acchdg = [['a1', '',        None],
          ['a2', '',        None],
          ['a3', '',        None],
          ['a4', 'PAM',     ['lambda: console.Console._instance.stack("EXQ SETARG PAM")']],

          ['b1', '',        None],
          ['b2', '',        None],
          ['b3', 'SPY',     ['lambda: console.Console._instance.stack("EXQ SETARG SPY")']],
          ['b4', '>>>>',    ['lambda: None']],

          ['c1', '7',       ['lambda: console.Console._instance.stack("EXQ CHAR 7")']],
          ['c2', '4',       ['lambda: console.Console._instance.stack("EXQ CHAR 4")']],
          ['c3', '1',       ['lambda: console.Console._instance.stack("EXQ CHAR 1")']],
          ['c4', '',        None],

          ['d1', '8',       ['lambda: console.Console._instance.stack("EXQ CHAR 8")']],
          ['d2', '5',       ['lambda: console.Console._instance.stack("EXQ CHAR 5")']],
          ['d3', '2',       ['lambda: console.Console._instance.stack("EXQ CHAR 2")']],
          ['d4', '0',       ['lambda: console.Console._instance.stack("EXQ CHAR 0")']],

          ['e1', '9',       ['lambda: console.Console._instance.stack("EXQ CHAR 9")']],
          ['e2', '6',       ['lambda: console.Console._instance.stack("EXQ CHAR 6")']],
          ['e3', '3',       ['lambda: console.Console._instance.stack("EXQ CHAR 3")']],
          ['e4', '',        None],

          ['f1', 'COR',     ['lambda: console.Console._instance.stack("EXQ COR")',
                             'lambda: change_tid("TID_Function", "accmain")']],
          ['f2', 'CLR',     ['lambda: console.Console._instance.stack("EXQ CLR")']],
          ['f3', 'ANKB',    ['lambda: None']],
          ['f4', 'EXQ',     ['lambda: console.Console._instance.stack("EXQ EXQ")',
                             'lambda: change_tid("TID_Function", "accmain")']]
          ]


accspd = [['a1', '220',     ['lambda: console.Console._instance.stack("EXQ SETARG 220")']],
          ['a2', '250',     ['lambda: console.Console._instance.stack("EXQ SETARG 250")']],
          ['a3', '280',     ['lambda: console.Console._instance.stack("EXQ SETARG 280")']],
          ['a4', '300',     ['lambda: console.Console._instance.stack("EXQ SETARG 300")']],

          ['b1', 'SPD',     ['lambda: None']],
          ['b2', '',        None],
          ['b3', '',        None],
          ['b4', '',        None],

          ['c1', '7',       ['lambda: console.Console._instance.stack("EXQ CHAR 7")']],
          ['c2', '4',       ['lambda: console.Console._instance.stack("EXQ CHAR 4")']],
          ['c3', '1',       ['lambda: console.Console._instance.stack("EXQ CHAR 1")']],
          ['c4', '',        None],

          ['d1', '8',       ['lambda: console.Console._instance.stack("EXQ CHAR 8")']],
          ['d2', '5',       ['lambda: console.Console._instance.stack("EXQ CHAR 5")']],
          ['d3', '2',       ['lambda: console.Console._instance.stack("EXQ CHAR 2")']],
          ['d4', '0',       ['lambda: console.Console._instance.stack("EXQ CHAR 0")']],

          ['e1', '9',       ['lambda: console.Console._instance.stack("EXQ CHAR 9")']],
          ['e2', '6',       ['lambda: console.Console._instance.stack("EXQ CHAR 6")']],
          ['e3', '3',       ['lambda: console.Console._instance.stack("EXQ CHAR 3")']],
          ['e4', '',        None],

          ['f1', 'COR',     ['lambda: console.Console._instance.stack("EXQ COR")',
                             'lambda: change_tid("TID_Function", "accmain")']],
          ['f2', 'CLR',     ['lambda: console.Console._instance.stack("EXQ CLR")']],
          ['f3', '',        None],
          ['f4', 'EXQ',     ['lambda: console.Console._instance.stack("EXQ EXQ")',
                             'lambda: change_tid("TID_Function", "accmain")']]
          ]

accpbm = [['a1', '',        None],
          ['a2', '',        None],
          ['a3', '',        None],
          ['a4', '',        None],

          ['b1', '',        None],
          ['b2', '',        None],
          ['b3', '',        None],
          ['b4', '',        None],

          ['c1', '',        None],
          ['c2', '',        None],
          ['c3', '',        None],
          ['c4', '',        None],

          ['d1', '',        None],
          ['d2', '',        None],
          ['d3', 'PBP',     ['lambda: console.Console._instance.stack("HOLD")']],
          ['d4', 'PBR',     ['lambda: console.Console._instance.stack("OP")']],

          ['e1', '',        None],
          ['e2', '',        None],
          ['e3', '',        None],
          ['e4', '',        None],

          ['f1', '',        None],
          ['f2', 'MAIN',    ['lambda: change_tid("TID_Function", "accmain")']],
          ['f3', '',        None],
          ['f4', '',        None]
          ]
