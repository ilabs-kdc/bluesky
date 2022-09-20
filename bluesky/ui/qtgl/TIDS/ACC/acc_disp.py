"""
This python file contains the button definitions for the ACC display tid

Created by: Bob van Dillen
Date: 26-1-2022
"""

accdisp = [['a1',    'VIEW',            ['lambda: change_tid("TID_Display", "accview")']],
           ['a2',    'LABEL',           ['lambda: change_tid("TID_Display", "acclabel")']],
           ['a3',    'CRO',             ['lambda: None']],
           ['a4',    'CRB',             ['lambda: None']],

           ['b1',    'MAPS',            ['lambda: change_tid("TID_Display", "accmaps")']],
           ['b2',    'LISTS',           ['lambda: None']],
           ['b3',    'CBM',             ['lambda: None']],
           ['b4',    'CXY',             ['lambda: None']],

           ['c1',    'RTS',             ['lambda: None']],
           ['c2',    'HBS',             ['lambda: None']],
           ['c3',    'CRM',             ['lambda: None']],
           ['c4',    'D/F',             ['lambda: None']],

           ['d1',    'SVI\nCBL',        ['lambda: None']],
           ['d2',    'WXS',             ['lambda: None']],
           ['d3',    'VRV',             ['lambda: None']],
           ['d4',    'AUTO\nPOS',       ['lambda: None']],

           ['e1',    'SLB',             ['lambda: None']],
           ['e2',    'SEL',             ['lambda: None']],
           ['e3',    'SEQ',             ['lambda: None']],
           ['e4',    'BACK\nUP',        ['lambda: None']],

           ['f1',    'COR',             ['lambda: console.Console._instance.stack("EXQ COR")',
                                         'lambda: change_tid("TID_Display", "accmain")']],
           ['f2',    'ACM',             None],
           ['f3',    'INFO',            ['lambda: None']],
           ['f4',    'EXQ',             ['lambda: change_tid("TID_Display", "accmain")']]
           ]


accview = [['a1',    'SE5',             ['lambda: console.Console._instance.stack("PAN 52.843333333333334,3.9274999999999998 ; SCREENRANGE 80")']],
           ['a2',    'SUGOL',           ['lambda: console.Console._instance.stack("PAN SUGOL ; SCREENRANGE 80")']],
           ['a3',    'SE4',             ['lambda: console.Console._instance.stack("PAN 52.3925,3.7552777777777777 ; SCREENRANGE 80")']],
           ['a4',    '',                None],

           ['b1',    'FIC',             ['lambda: console.Console._instance.stack("PAN 52.79694444444444,4.014166666666667 ; SCREENRANGE 80")']],
           ['b2',    'ACO',             ['lambda: console.Console._instance.stack("PAN 52.538888888888884,4.849722222222222 ; SCREENRANGE 80")']],
           ['b3',    'RIVER',           ['lambda: console.Console._instance.stack("PAN RIVER ; SCREENRANGE 80")']],
           ['b4',    'SE3',             ['lambda: console.Console._instance.stack("PAN 51.68,4.148611111111111 ; SCREENRANGE 80")']],

           ['c1',    'SE1',             ['lambda: console.Console._instance.stack("PAN 52.70805555555556,6.049722222222222 ; SCREENRANGE 80")']],
           ['c2',    'ARTIP',           ['lambda: console.Console._instance.stack("PAN ARTIP ; SCREENRANGE 80")']],
           ['c3',    'SE2',             ['lambda: console.Console._instance.stack("PAN 52.49805555555556,6.036388888888888 ; SCREENRANGE 80")']],
           ['c4',    'RNG\n140',        ['lambda: console.Console._instance.stack("SCREENRANGE 140")']],

           ['d1',    'RNG\n80',         ['lambda: console.Console._instance.stack("SCREENRANGE 80")']],
           ['d2',    'RNG\n90',         ['lambda: console.Console._instance.stack("SCREENRANGE 90")']],
           ['d3',    'RNG\n100',        ['lambda: console.Console._instance.stack("SCREENRANGE 100")']],
           ['d4',    'RNG\n120',        ['lambda: console.Console._instance.stack("SCREENRANGE 120")']],

           ['e1',    'OCK',             ['lambda: None']],
           ['e2',    '',                None],
           ['e3',    'COBRI',           ['lambda: None']],
           ['e4',    'PDS',             ['lambda: None']],

           ['f1',    '',                None],
           ['f2',    'MAIN',            ['lambda: change_tid("TID_Display", "accdisp")']],
           ['f3',    '',                None],
           ['f4',    '',                None]
           ]


acclabel = [['a1',    'SLA\nLARGE',         ['lambda: None']],
            ['a2',    'SLA\nMED',           ['lambda: None']],
            ['a3',    'SLA\nSMALL',         ['lambda: None']],
            ['a4',    'SLA\nX-SML',         ['lambda: None']],

            ['b1',    'LLL\nLONG',          ['lambda: None']],
            ['b2',    'LLL\nMED',           ['lambda: None']],
            ['b3',    'LLL\nSHORT',         ['lambda: None']],
            ['b4',    '',                   None],

            ['c1',    'CALLSIGN',           ['lambda: None']],
            ['c2',    'MOD-C',              ['lambda: None']],
            ['c3',    'XFL\nIFL',           ['lambda: None']],
            ['c4',    '.SL\nSPD',           ['lambda: None']],

            ['d1',    '',                   None],
            ['d2',    'NFL\nEFL',           ['lambda: None']],
            ['d3',    'GRND\nSPEED',        ['lambda: None']],
            ['d4',    'TYP\nHDG',           ['lambda: None']],

            ['e1',    'MODE-S\nACID',       ['lambda: tidcmds.exqcmd("SSRLABEL", "ACID")']],
            ['e2',    'LKP',                ['lambda: None']],
            ['e3',    '15 MIN\nHIST',       ['lambda: None']],
            ['e4',    'FULL\nLABEL',        ['lambda: tidcmds.exqcmd("TRACKLABEL")']],

            ['f1',    '',                   None],
            ['f2',    'MAIN',               ['lambda: change_tid("TID_Display", "accdisp")']],
            ['f3',    'SSR\nSMALL',         ['lambda: None']],
            ['f4',    'SSR\nX-SML',         ['lambda: None']]
            ]
