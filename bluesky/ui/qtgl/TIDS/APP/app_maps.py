"""
This python file contains the button definitions for the Approach maps

Created by: Bob van Dillen
Date: 9-12-2021
Edited by: Mitchell de Keijzer
Date: 09-04-2022
Changed: new maptoggle function from 'MAP #' to 'MAPTOGGLE MAP #'
"""

appmaps = [['a1',    'ALS\n10NM',     ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("als10nm","als10nm")']],
           ['a2',    'T-BAR',         ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("tbar","tbar")']],
           ['a3',    'VMT\nAREAS',    ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("vmt", "vmt")']],
           ['a4',    'NIGHT\nMAPS',   'lambda: None'],

           ['b1',    'ALS\n20NM',     ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("als20nm", "als20nm")']],
           ['b2',    'ALS\nTMA',      ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("alstma", "alstma")']],
           ['b3',    'FAV\nAREAS',    ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("favareas", "favareas")']],
           ['b4',    'RNP\nMAPS',     'lambda: None'],

           ['c1',    'PAR\nAPP',      ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("parapp", "parapp")']],
           ['c2',    'NL\nGEO',       'lambda: console.Console._instance.stack("SWRAD GEO")'],
           ['c3',    'AREAS\nRD',     ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("areasrd", "areasrd")']],
           ['c4',    'AREAS\nLE',     ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("areasle", "areasle")']],

           ['d1',    'REF\nPOINT',    'lambda: None'],
           ['d2',    'TWEC\nTOC',     ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("twectoc", "twectoc")']],
           ['d3',    'OCA',           'lambda: None'],
           ['d4',    'CTR\nKD',       'lambda: console.Console._instance.stack("MAPTOGGLE MAP 205")'],

           ['e1',    'VNR\nMAPS',     'lambda: None'],
           ['e2',    'POINTS\nFINAL', 'lambda: None'],
           ['e3',    'OCN',           'lambda: None'],
           ['e4',    'PARA\nTMA',     ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("paratma", "paratma")']],

           ['f1',    'COR',           'lambda: None'],
           ['f2',    'MAIN',          ['lambda: appmaps.close()',
                                       'lambda: show_basetid2("appdisp", "appdisp")']],
           ['f3', 'TOGGLE\nVNR MAP',         ['lambda: console.Console._instance.stack("MAPTOGGLE map GMP")']],
           ['f4',    'FIC\nMAPS',     'lambda: None']]


parapp = [['a1',    '10 NM\n36C',    'lambda: console.Console._instance.stack("MAPTOGGLE map 21; MAPTOGGLE map 213")'],
          ['a2',    '10 NM\n36R',    'lambda: console.Console._instance.stack("MAPTOGGLE map 23; MAPTOGGLE map 218")'],
          ['a3',    '16 NM\n36C',    'lambda: console.Console._instance.stack("MAPTOGGLE map 7; MAPTOGGLE map 246")'],
          ['a4',    '16 NM\n36R',    'lambda: console.Console._instance.stack("map 8; map 247")'],

          ['b1',    '10 NM\n18R',    'lambda: console.Console._instance.stack("MAPTOGGLE map 18; MAPTOGGLE map 220")'],
          ['b2',    '10 NM\n18C',    'lambda: console.Console._instance.stack("MAPTOGGLE map 35; MAPTOGGLE map 212")'],
          ['b3',    '14 NM\n18R',    'lambda: console.Console._instance.stack("MAPTOGGLE map 9; MAPTOGGLE map 248")'],
          ['b4',    '14 NM\n18C',    'lambda: console.Console._instance.stack("MAPTOGGLE map 10; MAPTOGGLE map 249")'],

          ['c1',    '',              None],
          ['c2',    '',              None],
          ['c3',    '',              None],
          ['c4',    '',              None],

          ['d1',    '',              None],
          ['d2',    '',              None],
          ['d3',    '',              None],
          ['d4',    '',              None],

          ['e1',    '',              None],
          ['e2',    '',              None],
          ['e3',    '',              None],
          ['e4',    '',              None],

          ['f1',    'COR',           'lambda: None'],
          ['f2',    'MAIN',          ['lambda: parapp.close()',
                                      'lambda: show_basetid2("appdisp", "appdisp")']],
          ['f3',    'MAPS\nAPP',     ['lambda: parapp.close()',
                                      'lambda: show_basetid2("appmaps", "appmaps")']],
          ['f4',    '',              None]]


als10nm = [['a1',    '10 NM\n06',     'lambda: console.Console._instance.stack("MAPTOGGLE map 28; MAPTOGGLE map 210")'],
           ['a2',    '10 NM\n18C',    'lambda: console.Console._instance.stack("MAPTOGGLE map 35; MAPTOGGLE map 212")'],
           ['a3',    '10 NM\n27',     'lambda: console.Console._instance.stack("MAPTOGGLE map 42; MAPTOGGLE map 216")'],
           ['a4',    '10 NM\n36R',    'lambda: console.Console._instance.stack("MAPTOGGLE map 23; MAPTOGGLE map 218")'],

           ['b1',    '10 NM\n24',     'lambda: console.Console._instance.stack("MAPTOGGLE map 40; MAPTOGGLE map 211")'],
           ['b2',    '10 NM\n36C',    'lambda: console.Console._instance.stack("MAPTOGGLE map 21; MAPTOGGLE map 213")'],
           ['b3',    '10 NM\n09',     'lambda: console.Console._instance.stack("MAPTOGGLE map 31; MAPTOGGLE map 217")'],
           ['b4',    '10 NM\n18L',    'lambda: console.Console._instance.stack("MAPTOGGLE map 33; MAPTOGGLE map 219")'],

           ['c1',    '10 NM\n18R',    'lambda: console.Console._instance.stack("MAPTOGGLE map 18; MAPTOGGLE map 220")'],
           ['c2',    '10 NM\n22',     'lambda: console.Console._instance.stack("MAPTOGGLE map 38; MAPTOGGLE map 214")'],
           ['c3',    '',              None],
           ['c4',    '',              None],

           ['d1',    '',              None],
           ['d2',    '10 NM\n04',     'lambda: console.Console._instance.stack("MAPTOGGLE map 26; MAPTOGGLE map 215")'],
           ['d3',    '',              None],
           ['d4',    '',              None],

           ['e1',    'ALS\n20NM',     ['lambda: als10nm.close()',
                                       'lambda: show_basetid2("als20nm", "als20nm")']],
           ['e2',    '',              None],
           ['e3',    '',              None],
           ['e4',    '',              None],

           ['f1',    '',              None],
           ['f2',    'MAIN',          ['lambda: als10nm.close()',
                                       'lambda: show_basetid2("appdisp", "appdisp")']],
           ['f3',    'MAPS\nAPP',     ['lambda: als10nm.close()',
                                       'lambda: show_basetid2("appmaps", "appmaps")']],
           ['f4',    '',              None]]


als20nm = [['a1',    '20 NM\n06',     'lambda: console.Console._instance.stack("MAPTOGGLE map 29; MAPTOGGLE map 221")'],
           ['a2',    '20 NM\n18C',    'lambda: console.Console._instance.stack("MAPTOGGLE map 36; MAPTOGGLE map 223")'],
           ['a3',    '20 NM\n27',     'lambda: console.Console._instance.stack("MAPTOGGLE map 43; MAPTOGGLE map 226")'],
           ['a4',    '20 NM\n36R',    'lambda: console.Console._instance.stack("MAPTOGGLE map 24; MAPTOGGLE map 227")'],

           ['b1',    '20 NM\n18R',    'lambda: console.Console._instance.stack("MAPTOGGLE map 19; MAPTOGGLE map 222")'],
           ['b2',    '20 NM\n36C',    'lambda: console.Console._instance.stack("MAPTOGGLE map 45; MAPTOGGLE map 224")'],
           ['b3',    '',              None],
           ['b4',    '',              None],

           ['c1',    '',              None],
           ['c2',    '20 NM\n22',     'lambda: console.Console._instance.stack("MAPTOGGLE map 46; MAPTOGGLE map 225")'],
           ['c3',    '',              None],
           ['c4',    '',              None],

           ['d1',    '',              None],
           ['d2',    '',              None],
           ['d3',    '',              None],
           ['d4',    '',              None],

           ['e1',    'ALS\n10NM',     ['lambda: als20nm.close()',
                                       'lambda: show_basetid2("als10nm", "als10nm")']],
           ['e2',    '',              None],
           ['e3',    '',              None],
           ['e4',    '',              None],

           ['f1',    '',              None],
           ['f2',    'MAIN',          ['lambda: als20nm.close()',
                                       'lambda: show_basetid2("appdisp", "appdisp")']],
           ['f3',    'MAPS\nAPP',     ['lambda: als20nm.close()',
                                       'lambda: show_basetid2("appmaps", "appmaps")']],
           ['f4',    '',              None]]


vmt = [['a1',    'VMT\n06',       'lambda: console.Console._instance.stack("MAPTOGGLE map 104")'],
       ['a2',    'VMT\n18C',      'lambda: console.Console._instance.stack("MAPTOGGLE map 107")'],
       ['a3',    'VMT\n27',       'lambda: console.Console._instance.stack("MAPTOGGLE map 110")'],
       ['a4',    'VMT\n36R',      'lambda: console.Console._instance.stack("MAPTOGGLE map 102")'],

       ['b1',    'VMT\n24',       'lambda: console.Console._instance.stack("MAPTOGGLE map 109")'],
       ['b2',    'VMT\n36C',      'lambda: console.Console._instance.stack("MAPTOGGLE map 101")'],
       ['b3',    'VMT\n09',       'lambda: console.Console._instance.stack("MAPTOGGLE map 105")'],
       ['b4',    'VMT\n18L',      'lambda: console.Console._instance.stack("MAPTOGGLE map 106")'],

       ['c1',    'VMT\n18R',      'lambda: console.Console._instance.stack("MAPTOGGLE map 116")'],
       ['c2',    'VMT\n06/36R',   'lambda: console.Console._instance.stack("MAPTOGGLE map 112")'],
       ['c3',    '',              None],
       ['c4',    'STARS\nFDR',    'lambda: console.Console._instance.stack("MAPTOGGLE map 151")'],

       ['d1',    'VMT\n18R/C',    'lambda: console.Console._instance.stack("MAPTOGGLE map 115")'],
       ['d2',    'VMT\n36R/27',   'lambda: console.Console._instance.stack("MAPTOGGLE map 113")'],
       ['d3',    '',              None],
       ['d4',    'VIC\nARR',      'lambda: console.Console._instance.stack("MAPTOGGLE map 111")'],

       ['e1',    '',              None],
       ['e2',    '',              None],
       ['e3',    '',              None],
       ['e4',    '',              None],

       ['f1',    'COR',           'lambda: None'],
       ['f2',    'MAIN',          ['lambda: vmt.close()',
                                   'lambda: show_basetid2("appdisp", "appdisp")']],
       ['f3',    'MAPS\nAPP',     ['lambda: vmt.close()',
                                   'lambda: show_basetid2("appmaps", "appmaps")']],
       ['f4',    '',              None]]


alstma = [['a1',    'KD\n03',        'lambda: console.Console._instance.stack("MAPTOGGLE map 71; MAPTOGGLE map 238")'],
          ['a2',    'LE\n05',        'lambda: console.Console._instance.stack("MAPTOGGLE map 73; MAPTOGGLE map 240")'],
          ['a3',    '',              None],
          ['a4',    '',              None],

          ['b1',    'KD\n21',        'lambda: console.Console._instance.stack("MAPTOGGLE map 72; MAPTOGGLE map 239")'],
          ['b2',    'LE\n23',        'lambda: console.Console._instance.stack("MAPTOGGLE map 74; MAPTOGGLE map 241")'],
          ['b3',    '',              None],
          ['b4',    '',              None],

          ['c1',    'RD\n06',        'lambda: console.Console._instance.stack("MAPTOGGLE map 75; MAPTOGGLE map 242")'],
          ['c2',    '',              None],
          ['c3',    '',              None],
          ['c4',    '',              None],

          ['d1',    'RD\n24',        'lambda: console.Console._instance.stack("MAPTOGGLE map 76; MAPTOGGLE map 243")'],
          ['d2',    '',              None],
          ['d3',    '',              None],
          ['d4',    '',              None],

          ['e1',    '',              None],
          ['e2',    '',              None],
          ['e3',    '',              None],
          ['e4',    '',              None],

          ['f1',    '',              None],
          ['f2',    'MAIN',          ['lambda: alstma.close()',
                                      'lambda: show_basetid2("appdisp", "appdisp")']],
          ['f3',    'MAPS\nAPP',     ['lambda: alstma.close()',
                                      'lambda: show_basetid2("appmaps", "appmaps")']],
          ['f4',    '',              None]]


areasle = [['a1',    'LE\n05',        'lambda: console.Console._instance.stack("MAPTOGGLE map 73; MAPTOGGLE map 240")'],
           ['a2',    '',              None],
           ['a3',    'INBOUND',       'lambda: console.Console._instance.stack("MAPTOGGLE map 825")'],
           ['a4',    'NAMES',         'lambda: console.Console._instance.stack("MAPTOGGLE map 823")'],

           ['b1',    'LE\n23',        'lambda: console.Console._instance.stack("MAPTOGGLE map 74; MAPTOGGLE map 241")'],
           ['b2',    '',              None],
           ['b3',    'SIDS',          'lambda: console.Console._instance.stack("MAPTOGGLE map 824")'],
           ['b4',    'TMA',           'lambda: console.Console._instance.stack("MAPTOGGLE map 820")'],

           ['c1',    '',              None],
           ['c2',    '',              None],
           ['c3',    '',              None],
           ['c4',    '',              None],

           ['d1',    '',              None],
           ['d2',    '',              None],
           ['d3',    '',              None],
           ['d4',    '',              None],

           ['e1',    '',              None],
           ['e2',    '',              None],
           ['e3',    '',              None],
           ['e4',    '',              None],

           ['f1',    '',              None],
           ['f2',    'MAIN',          ['lambda: areasle.close()',
                                       'lambda: show_basetid2("appdisp", "appdisp")']],
           ['f3',    'MAPS\nAPP',     ['lambda: areasle.close()',
                                       'lambda: show_basetid2("appmaps", "appmaps")']],
           ['f4',    '',              None]]


areasrd = [['a1',    'ATZ\nVB',       'lambda: console.Console._instance.stack("MAPTOGGLE MAP 354")'],
           ['a2',    '',              None],
           ['a3',    '',              None],
           ['a4',    'VFR\nEHRD',     'lambda: console.Console._instance.stack("MAPTOGGLE MAP 262")'],

           ['b1',    '',              None],
           ['b2',    'BOSKO',         'lambda: console.Console._instance.stack("MAPTOGGLE MAP 259")'],
           ['b3',    'NL\nGEO',       'lambda: console.Console._instance.stack("SWRAD GEO")'],
           ['b4',    'NL\nW-WAY',     'lambda: console.Console._instance.stack("MAPTOGGLE MAP 444; MAPTOGGLE MAP 445; MAPTOGGLE MAP 446")'],

           ['c1',    'RD\n06',        'lambda: console.Console._instance.stack("MAPTOGGLE MAP 75; MAPTOGGLE MAP 242")'],
           ['c2',    'FAVA\nRD 06',   'lambda: console.Console._instance.stack("MAPTOGGLE MAP 137")'],
           ['c3',    '',              None],
           ['c4',    '',              None],

           ['d1',    'RD\n24',        'lambda: console.Console._instance.stack("MAPTOGGLE MAP 76; MAPTOGGLE MAP 243")'],
           ['d2',    'FAVA\nRD 24',   'lambda: console.Console._instance.stack("MAPTOGGLE MAP 138")'],
           ['d3',    'MVA\nNE',       'lambda: console.Console._instance.stack("MAPTOGGLE MAP 139")'],
           ['d4',    '',              None],

           ['e1',    '',              None],
           ['e2',    'TMA\nRD',       'lambda: console.Console._instance.stack("MAPTOGGLE MAP 250")'],
           ['e3',    'RAP\nOCO',      'lambda: None'],
           ['e4',    '',              None],

           ['f1',    '',              None],
           ['f2',    'MAIN',          ['lambda: areasrd.close()',
                                       'lambda: show_basetid2("appdisp", "appdisp")']],
           ['f3',    'MAPS\nAPP',     ['lambda: areasrd.close()',
                                       'lambda: show_basetid2("appmaps", "appmaps")']],
           ['f4',    '',              None]]


twectoc = [['a1',    'RAD\n019',      'lambda: console.Console._instance.stack("MAPTOGGLE MAP 281")'],
           ['a2',    'RAD\n040',      'lambda: console.Console._instance.stack("MAPTOGGLE MAP 282")'],
           ['a3',    'RAD\n200',      'lambda: console.Console._instance.stack("MAPTOGGLE MAP 283")'],
           ['a4',    'RAD\n205',      'lambda: console.Console._instance.stack("MAPTOGGLE MAP 284")'],

           ['b1',    '',              None],
           ['b2',    '',              None],
           ['b3',    '',              None],
           ['b4',    '',              None],

           ['c1',    '',              None],
           ['c2',    '',              None],
           ['c3',    '',              None],
           ['c4',    '',              None],

           ['d1',    '',              None],
           ['d2',    '',              None],
           ['d3',    '',              None],
           ['d4',    '',              None],

           ['e1',    '',              None],
           ['e2',    '',              None],
           ['e3',    '',              None],
           ['e4',    '',              None],

           ['f1',    '',              None],
           ['f2',    'MAIN',          ['lambda: twectoc.close()',
                                       'lambda: show_basetid2("appdisp", "appdisp")']],
           ['f3',    'MAPS\nAPP',     ['lambda: twectoc.close()',
                                       'lambda: show_basetid2("appmaps", "appmaps")']],
           ['f4',    '',              None]]


paratma = [['a1',    '',              None],
           ['a2',    'CLIMB\nAREA',   'lambda: console.Console._instance.stack("MAPTOGGLE MAP 507")'],
           ['a3',    'LEUSD\nHEIDE',  'lambda: console.Console._instance.stack("MAPTOGGLE MAP 505")'],
           ['a4',    '',              None],

           ['b1',    '',              None],
           ['b2',    'HILVE-\nRSUM',  'lambda: console.Console._instance.stack("MAPTOGGLE MAP 503")'],
           ['b3',    'WIJK\nDUUR',    'lambda: console.Console._instance.stack("MAPTOGGLE MAP 506")'],
           ['b4',    '',              None],

           ['c1',    '',              None],
           ['c2',    'WEST\nBROEK',   'lambda: console.Console._instance.stack("MAPTOGGLE MAP 504")'],
           ['c3',    '',              None],
           ['c4',    '',              None],

           ['d1',    '',              None],
           ['d2',    'BAARN',         'lambda: console.Console._instance.stack("MAPTOGGLE MAP 502")'],
           ['d3',    '',              None],
           ['d4',    '',              None],

           ['e1',    '',              None],
           ['e2',    'RHOON\n2NM',    'lambda: console.Console._instance.stack("MAPTOGGLE MAP 509")'],
           ['e3',    'RHOON\n5NM',    'lambda: console.Console._instance.stack("MAPTOGGLE MAP 530")'],
           ['e4',    '',              None],

           ['f1',    '',              None],
           ['f2',    'MAIN',          ['lambda: paratma.close()',
                                       'lambda: show_basetid2("appdisp", "appdisp")']],
           ['f3',    'MAPS\nAPP',     ['lambda: paratma.close()',
                                       'lambda: show_basetid2("appmaps", "appmaps")']],
           ['f4',    '',              None]]


favareas = [['a1',    'FAVA\n18R',     'lambda: console.Console._instance.stack("MAPTOGGLE MAP 132")'],
            ['a2',    'FAVA\n18C',     'lambda: console.Console._instance.stack("MAPTOGGLE MAP 131")'],
            ['a3',    'FAVA\n06',      'lambda: console.Console._instance.stack("MAPTOGGLE MAP 130")'],
            ['a4',    'FAVA\n22',      'lambda: console.Console._instance.stack("MAPTOGGLE MAP 133")'],

            ['b1',    'FAVA\n36R',     'lambda: console.Console._instance.stack("MAPTOGGLE MAP 136")'],
            ['b2',    'FAVA\n36C',     'lambda: console.Console._instance.stack("MAPTOGGLE MAP 135")'],
            ['b3',    'FAVA\n27',      'lambda: console.Console._instance.stack("MAPTOGGLE MAP 134")'],
            ['b4',    '',              None],

            ['c1',    '',              None],
            ['c2',    '',              None],
            ['c3',    '',              None],
            ['c4',    '',              None],

            ['d1',    '',              None],
            ['d2',    '',              None],
            ['d3',    '',              None],
            ['d4',    '',              None],

            ['e1',    '',              None],
            ['e2',    '',              None],
            ['e3',    '',              None],
            ['e4',    '',              None],

            ['f1',    '',              None],
            ['f2',    'MAIN',          ['lambda: favareas.close()',
                                        'lambda: show_basetid2("appdisp", "appdisp")']],
            ['f3',    'MAPS\nAPP',     ['lambda: favareas.close()',
                                        'lambda: show_basetid2("appmaps", "appmaps")']],
            ['f4',    '',              None]]


tbar = [['a1',    'NIRSI',         'lambda: console.Console._instance.stack("MAPTOGGLE MAP NIRSI")'],
        ['a2',    'SOKS2',         'lambda: console.Console._instance.stack("MAPTOGGLE MAP SOKS2")'],
        ['a3',    'GALIS',         'lambda: console.Console._instance.stack("MAPTOGGLE MAP GALIS")'],
        ['a4',    'BAR',           'lambda: console.Console._instance.stack("MAPTOGGLE MAP RANGEBAR; RANGEBAR")'],

        ['b1',    '',              None],
        ['b2',    '',              None],
        ['b3',    '',              None],
        ['b4',    '',              None],

        ['c1',    '',              None],
        ['c2',    '',              None],
        ['c3',    '',              None],
        ['c4',    '',              None],

        ['d1',    '',              None],
        ['d2',    '',              None],
        ['d3',    '',              None],
        ['d4',    '',              None],

        ['e1',    '',              None],
        ['e2',    '',              None],
        ['e3',    '',              None],
        ['e4',    '',              None],

        ['f1',    '',              None],
        ['f2',    'MAIN',          ['lambda: tbar.close()',
                                    'lambda: show_basetid2("appdisp", "appdisp")']],
        ['f3',    'MAPS\nAPP',     ['lambda: tbar.close()',
                                    'lambda: show_basetid2("appmaps", "appmaps")']],
        ['f4',    '',              None]
        ]
