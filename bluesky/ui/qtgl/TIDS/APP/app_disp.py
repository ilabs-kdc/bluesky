"""
This python file contains the button definitions for the Approach display tid

Created by: Bob van Dillen
Date: 9-12-2021
Edited by: Mitchell de Keijzer
Changed: changed all commands for client position
"""

appdisp = [['a1',    'RANGE\nRADAR',    ['lambda: change_tid("TID_Display", "apprange")']],
           ['a2',    '36',              ['lambda: console.Console._instance.stack("SCREENRANGE 36")']],
           ['a3',    '48',              ['lambda: console.Console._instance.stack("SCREENRANGE 48")']],
           ['a4',    'CRO',             ['lambda: None']],

           ['b1',    'MOV',             ['lambda: None']],
           ['b2',    'WXS',             ['lambda: None']],
           ['b3',    'D/F',             ['lambda: None']],
           ['b4',    'CRB',             ['lambda: None']],

           ['c1',    'OCK',             ['lambda: None']],
           ['c2',    'SIZE\nLISTS',     ['lambda: None']],
           ['c3',    'LABEL',           ['lambda: change_tid("TID_Display", "applabel")']],
           ['c4',    'CBM',             ['lambda: None']],

           ['d1',    'OCO',             ['lambda: None']],
           ['d2',    'RAP\nOCO',        ['lambda: None']],
           ['d3',    'ANKB',            ['lambda: None']],
           ['d4',    'CXY',             ['lambda: None']],

           ['e1',    'MAPS\nAPP',       ['lambda: change_tid("TID_Display", "appmaps")']],
           ['e2',    'TBS',             ['lambda: None']],
           ['e3',    'BRIGHT\nNESS',    ['lambda: None']],
           ['e4',    'CRM',             ['lambda: None']],

           ['f1',    'COR',             ['lambda: console.Console._instance.stack("EXQ COR")',
                                         'lambda: change_tid("TID_Display", "appmain")']],
           ['f2',    '',                None],
           ['f3',    'TID\nCTRL',       ['lambda: None']],
           ['f4',    'EXQ',             ['lambda: change_tid("TID_Display", "appmain")']]
           ]


apprange = [['a1',    '16',                 ['lambda: console.Console._instance.stack("SCREENRANGE 16")']],
            ['a2',    '36',                 ['lambda: console.Console._instance.stack("SCREENRANGE 36")']],
            ['a3',    '48',                 ['lambda: console.Console._instance.stack("SCREENRANGE 48")']],
            ['a4',    'PLN\nVIEW',          ['lambda: console.Console._instance.stack("SCREENRANGE 120")']],

            ['b1',    '24',                 ['lambda: console.Console._instance.stack("SCREENRANGE 24")']],
            ['b2',    '42',                 ['lambda: console.Console._instance.stack("SCREENRANGE 42")']],
            ['b3',    '60',                 ['lambda: console.Console._instance.stack("SCREENRANGE 60")']],
            ['b4',    '160',                ['lambda: console.Console._instance.stack("SCREENRANGE 160")']],

            ['c1',    'RNG',                ['lambda: None']],
            ['c2',    'TAR W',              ['lambda: None']],
            ['c3',    'TAR 1',              ['lambda: None']],
            ['c4',    'ARTAS1\nAPP',        ['lambda: None']],

            ['d1',    'DCT\nTAR1',          ['lambda: None']],
            ['d2',    'DCT\nTAR W',         ['lambda: None']],
            ['d3',    '',                   None],
            ['d4',    'ARTAS2\nAPP',        ['lambda: None']],

            ['e1',    'DCT\nARTAS2\nAPP',   ['lambda: None']],
            ['e2',    '',                   None],
            ['e3',    'MADAP',              ['lambda: None']],
            ['e4',    'ARTAS1\nACC',        ['lambda: None']],

            ['f1',    '',                   None],
            ['f2',    'MAIN',               ['lambda: change_tid("TID_Display", "appdisp")']],
            ['f3',    '',                   None],
            ['f4',    '',                   None]
            ]


applabel = [['a1',    'SLA\nLARGE',         ['lambda: None']],
            ['a2',    'SLA\nMED',           ['lambda: None']],
            ['a3',    'SLA\nSMALL',         ['lambda: None']],
            ['a4',    'SLA\nX-SML',         ['lambda: None']],

            ['b1',    'LLL\nMED',           ['lambda: None']],
            ['b2',    'LLL\nSHORT',         ['lambda: None']],
            ['b3',    'SSR\nSMALL',         ['lambda: None']],
            ['b4',    'SSR\nX-SML',         ['lambda: None']],

            ['c1',    'SSR\nMOD-A',         ['lambda: tidcmds.exqcmd("SSRLABEL", "A")']],
            ['c2',    'SSR\nMOD-C',         ['lambda: tidcmds.exqcmd("SSRLABEL", "C")']],
            ['c3',    'SSR\nACID',          ['lambda: tidcmds.exqcmd("SSRLABEL", "ACID")']],
            ['c4',    'TRAIL\nONOFF',       ['lambda: console.Console._instance.stack("SWRAD HISTORY")']],

            ['d1',    'LINE0',              ['lambda: None']],
            ['d2',    'MOD-C',              ['lambda: None']],
            ['d3',    'TYPE',               ['lambda: None']],
            ['d4',    'MGSP\nWTC',          ['lambda: None']],

            ['e1',    '',                   None],
            ['e2',    'EFL\nNFL',           ['lambda: None']],
            ['e3',    'HDG\nSID',           ['lambda: None']],
            ['e4',    'SPEED',              ['lambda: None']],

            ['f1',    '',                   None],
            ['f2',    'MAIN',               ['lambda: change_tid("TID_Display", "appdisp")']],
            ['f3',    '',                   None],
            ['f4',    'FULL\nLABEL',        ['lambda: tidcmds.exqcmd("TRACKLABEL")']]
            ]

