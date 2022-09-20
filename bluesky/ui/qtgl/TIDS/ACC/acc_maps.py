"""
This python file contains the button definitions for the ACC maps

Created by: Bob van Dillen
Date: 26-1-2022
"""

accmaps = [['a1',    'NEW\nPNTS',       ['lambda: None']],
           ['a2',    'CTR/\nTMA',       ['lambda: change_tid("TID", "accctrtma")']],
           ['a3',    '',                 None],
           ['a4',    'AAA\nAREAS',      ['lambda: change_tid("TID", "accaaa")']],

           ['b1',    'FIC\nITEMS',      ['lambda: change_tid("TID", "accficitms")']],
           ['b2',    'APPR\nEHAM',      ['lambda: change_tid("TID", "accappeham")']],
           ['b3',    'APPR\nOTHER',     ['lambda: change_tid("TID", "accappother")']],
           ['b4',    'MISC',            ['lambda: change_tid("TID", "accmisc")']],

           ['c1',    'FIC\nMAPS',       ['lambda: change_tid("TID", "accfic")']],
           ['c2',    'APPR\nEHEH',      ['lambda: change_tid("TID", "accappeheh")']],
           ['c3',    'APPR\nEHLE',      ['lambda: change_tid("TID", "accappehle")']],
           ['c4',    'MIL\nMISC',       ['lambda: change_tid("TID", "accmilmisc")']],

           ['d1',    'APPR\nMIL N',     ['lambda: change_tid("TID", "accappmiln")']],
           ['d2',    'APPR\nMIL S',     ['lambda: change_tid("TID", "accappmils")']],
           ['d3',    'APPR\nEHKD',      ['lambda: change_tid("TID", "accappehkd")']],
           ['d4',    'MIL\nEHR8',       ['lambda: change_tid("TID", "accmilehr8")']],

           ['e1',    'OCA',             ['lambda: None']],
           ['e2',    'OCN',             ['lambda: None']],
           ['e3',    '',                None],
           ['e4',    '',                None],

           ['f1',    '',                None],
           ['f2',    'MAIN',            ['lambda: change_tid("TID", "accdisp")']],
           ['f3',    '',                None],
           ['f4',    '',                None]
           ]


accaaa = [['a1',    '',                 None],
          ['a2',    '',                 None],
          ['a3',    '',                 None],
          ['a4',    '',                 None],

          ['b1',    'ACOD\nAREAS',      ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 401")']],
          ['b2',    'PACOD\nAREAS',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 402")']],
          ['b3',    'STCA\nAREAS',      ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 403")']],
          ['b4',    'AIRSP\nCROSS',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 404")']],

          ['c1',    '',                 None],
          ['c2',    '',                 None],
          ['c3',    '',                 None],
          ['c4',    '',                 None],

          ['d1',    '',                 None],
          ['d2',    '',                 None],
          ['d3',    '',                 None],
          ['d4',    '',                 None],

          ['e1',    '',                 None],
          ['e2',    '',                 None],
          ['e3',    '',                 None],
          ['e4',    '',                 None],

          ['f1',    '',                 None],
          ['f2',    'MAIN',             ['lambda: change_tid("TID", "accdisp")']],
          ['f3',    'MAPS',             ['lambda: change_tid("TID", "accmaps")']],
          ['f4',    '',                 None]
          ]


accappeham = [['a1',    'AM\n36C',      ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 21")']],
              ['a2',    '',             None],
              ['a3',    'AM\n18R',      ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 18")']],
              ['a4',    'AM\n22',       ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 38")']],

              ['b1',    'AM\n36R',      ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 23")']],
              ['b2',    'AM\n06',       ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 28")']],
              ['b3',    'AM\n18C',      ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 35")']],
              ['b4',    'AM\n27',       ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 42")']],

              ['c1',    '',                 None],
              ['c2',    '',                 None],
              ['c3',    '',                 None],
              ['c4',    '',                 None],

              ['d1',    'VNR\n36R',         ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 121")']],
              ['d2',    'TRANS\n06',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 92")']],
              ['d3',    'TRANS\n18R/C',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 94")']],
              ['d4',    'RNP\n22',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 169")']],

              ['e1',    '',                 None],
              ['e2',    '',                 None],
              ['e3',    '',                 None],
              ['e4',    '',                 None],

              ['f1',    '',                 None],
              ['f2',    'MAIN',             ['lambda: change_tid("TID", "accdisp")']],
              ['f3',    'MAPS',             ['lambda: change_tid("TID", "accmaps")']],
              ['f4',    '',                 None]
              ]


accappehle = [['a1',    'LE\n05',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 73")']],
              ['a2',    'CDO\n05',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 827")']],
              ['a3',    'INBOUND',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 825")']],
              ['a4',    'NAMES',            ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 823")']],

              ['b1',    'LE\n23',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 74")']],
              ['b2',    'CDO\n23',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 830")']],
              ['b3',    'SIDS',             ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 824")']],
              ['b4',    'TMA',              ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 820")']],

              ['c1',    '',                 None],
              ['c2',    'CDO\nRPN\n05',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 828")']],
              ['c3',    '',                 None],
              ['c4',    'CTR-1',            ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 832")']],

              ['d1',    '',                 None],
              ['d2',    'CDO\nRPN\n23',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 831")']],
              ['d3',    '',                 None],
              ['d4',    '',                 None],

              ['e1',    '',                 None],
              ['e2',    '',                 None],
              ['e3',    '',                 None],
              ['e4',    '',                 None],

              ['f1',    '',                 None],
              ['f2',    'MAIN',             ['lambda: change_tid("TID", "accdisp")']],
              ['f3',    'MAPS',             ['lambda: change_tid("TID", "accmaps")']],
              ['f4',    '',                 None]
              ]


accappother = [['a1',    'RD\n06',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 75")']],
               ['a2',    'LE\n05',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 73")']],
               ['a3',    'GG\n05',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 53")']],
               ['a4',    '',                None],

               ['b1',    'RD\n24',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 76")']],
               ['b2',    'LE\n23',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 74")']],
               ['b3',    'GG\n23',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 54")']],
               ['b4',    '',                None],

               ['c1',    '',                None],
               ['c2',    '',                None],
               ['c3',    '',                None],
               ['c4',    '',                None],

               ['d1',    '',                None],
               ['d2',    '',                None],
               ['d3',    '',                None],
               ['d4',    '',                None],

               ['e1',    '',                None],
               ['e2',    '',                None],
               ['e3',    '',                None],
               ['e4',    '',                None],

               ['f1',    '',                None],
               ['f2',    'MAIN',            ['lambda: change_tid("TID", "accdisp")']],
               ['f3',    'MAPS',            ['lambda: change_tid("TID", "accmaps")']],
               ['f4',    '',                None]
               ]


accctrtma = [['a1',    'CTR\nEHAM',         ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 202")']],
             ['a2',    'CTR\nEHKD',         ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 205")']],
             ['a3',    '',                  None],
             ['a4',    'TMA\nSPL',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 252")']],

             ['b1',    'CTR\nEHRD',         ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 206")']],
             ['b2',    '',                  None],
             ['b3',    '',                  None],
             ['b4',    'TMA\nLE',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 820")']],

             ['c1',    '',                  None],
             ['c2',    '',                  None],
             ['c3',    '',                  None],
             ['c4',    'MIL\nTMA A',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 254")']],

             ['d1',    '',                  None],
             ['d2',    '',                  None],
             ['d3',    '',                  None],
             ['d4',    '',                  None],

             ['e1',    '',                  None],
             ['e2',    '',                  None],
             ['e3',    '',                  None],
             ['e4',    '',                  None],

             ['f1',    '',                  None],
             ['f2',    'MAIN',              ['lambda: change_tid("TID", "accdisp")']],
             ['f3',    'MAPS',              ['lambda: change_tid("TID", "accmaps")']],
             ['f4',    '',                  None]
             ]


accficitms = [['a1',    'HPZ',              ['lambda: change_tid("TID", "acchpz")']],
              ['a2',    'MCB',              ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 372")']],
              ['a3',    'ATZ',              ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 353")']],
              ['a4',    'ATZ\nEHVB',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 354")']],

              ['b1',    'HMR',              ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 351")']],
              ['b2',    'GLV\nXII',         ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 373")']],
              ['b3',    'GLIDE\nSITES',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 482")']],
              ['b4',    'RP\nNAMES',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 477")']],

              ['c1',    'ASR',              ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 374")']],
              ['c2',    '',                 None],
              ['c3',    'FIC\nOBST',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 456")']],
              ['c4',    'POLL\nPTS',        ['lambda: change_tid("TID", "accpoll")']],

              ['d1',    'CODE\n150X',       ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 850")']],
              ['d2',    'CODE\n242X',       ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 851")']],
              ['d3',    '',                 None],
              ['d4',    'VIC\nARR',         ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 111")']],

              ['e1',    '',                 None],
              ['e2',    '',                 None],
              ['e3',    '',                 None],
              ['e4',    '',                 None],

              ['f1',    '',                 None],
              ['f2',    'MAIN',             ['lambda: change_tid("TID", "accdisp")']],
              ['f3',    'MAPS',             ['lambda: change_tid("TID", "accmaps")']],
              ['f4',    '',                 None]
              ]


acchpz = [['a1',    'HANZE',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 360")']],
          ['a2',    'GORO\nMAND',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 362")']],
          ['a3',    'MEBOT',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 367")']],
          ['a4',    'MARK\nHAM',            ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 363")']],

          ['b1',    'DER\nMAR',             ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 361")']],
          ['b2',    'PENTA\nCON',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 365")']],
          ['b3',    'RYN\nVELD',            ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 369")']],
          ['b4',    'BOGTI',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 375")']],

          ['c1',    'UNI\nCORN',            ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 368")']],
          ['c2',    '',                     None],
          ['c3',    '',                     None],
          ['c4',    '',                     None],

          ['d1',    '',                     None],
          ['d2',    '',                     None],
          ['d3',    '',                     None],
          ['d4',    '',                     None],

          ['e1',    '',                     None],
          ['e2',    '',                     None],
          ['e3',    '',                     None],
          ['e4',    '',                     None],

          ['f1',    '',                     None],
          ['f2',    'MAIN',                 ['lambda: change_tid("TID", "accdisp")']],
          ['f3',    'MAPS',                 ['lambda: change_tid("TID", "accmaps")']],
          ['f4',    '',                     None]
          ]


accpoll = [['a1',    'NL\nPTS',             ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 473")']],
           ['a2',    'KM\nPTS',             ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 462")']],
           ['a3',    'KA+KD\nPTS',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 463")']],
           ['a4',    'GTB-N',               ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 380")']],

           ['b1',    'G\nPTS',              ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 472")']],
           ['b2',    'KW\nPTS',             ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 465")']],
           ['b3',    'ZS+SB\nPTS',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 466")']],
           ['b4',    'GTB-W',               ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 381")']],

           ['c1',    'B\nPTS',              ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 461")']],
           ['c2',    'KV\nPTS',             ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 467")']],
           ['c3',    'KB\nPTS',             ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 470")']],
           ['c4',    'GTB-Z',               ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 382")']],

           ['d1',    'WZ+VB\nPTS',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 468")']],
           ['d2',    'KX\nPTS',             ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 469")']],
           ['d3',    'WS+VZ\nPTS',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 464")']],
           ['d4',    '',                    None],

           ['e1',    'N\nPTS',              ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 473")']],
           ['e2',    'V\nPTS',              ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 471")']],
           ['e3',    'S\nPTS',              ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 474")']],
           ['e4',    '',                     None],

           ['f1',    '',                     None],
           ['f2',    'MAIN',                 ['lambda: change_tid("TID", "accdisp")']],
           ['f3',    'MAPS',                 ['lambda: change_tid("TID", "accmaps")']],
           ['f4',    '',                     None]
           ]


accfic = [['a1',    'FM 1',                 ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 700")']],
          ['a2',    'FM 6',                 ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 705")']],
          ['a3',    'FM 11',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 710")']],
          ['a4',    'FM 16',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 715")']],

          ['b1',    'FM 2',                 ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 701")']],
          ['b2',    'FM 7',                 ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 706")']],
          ['b3',    'FM 12',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 711")']],
          ['b4',    'FM 17',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 716")']],

          ['c1',    'FM 3',                 ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 702")']],
          ['c2',    'FM 8',                 ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 707")']],
          ['c3',    'FM 13',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 712")']],
          ['c4',    'FM 18',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 717")']],

          ['d1',    'FM 4',                 ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 703")']],
          ['d2',    'FM 9',                 ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 708")']],
          ['d3',    'FM 14',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 713")']],
          ['d4',    'FM 19',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 718")']],

          ['e1',    'FM 5',                 ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 704")']],
          ['e2',    'FM 10',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 709")']],
          ['e3',    'FM 15',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 714")']],
          ['e4',    'FM 20',                ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 719")']],

          ['f1',    '',                     None],
          ['f2',    'MAIN',                 ['lambda: change_tid("TID", "accdisp")']],
          ['f3',    'MAPS',                 ['lambda: change_tid("TID", "accmaps")']],
          ['f4',    '',                     None]
          ]


accappeheh = [['a1',    'EH\n03',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 785")']],
              ['a2',    'CDO\n03',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 807")']],
              ['a3',    'CDO\nSYM\n03',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 809")']],
              ['a4',    '',                 None],

              ['b1',    'EH\n21',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 786")']],
              ['b2',    'CDO\n21',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 808")']],
              ['b3',    'CDO\nSYM\n21',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 810")']],
              ['b4',    '',                 None],

              ['c1',    '',                 None],
              ['c2',    '',                 None],
              ['c3',    '',                 None],
              ['c4',    '',                 None],

              ['d1',    '',                 None],
              ['d2',    '',                 None],
              ['d3',    '',                 None],
              ['d4',    '',                 None],

              ['e1',    '',                 None],
              ['e2',    '',                 None],
              ['e3',    '',                 None],
              ['e4',    '',                 None],

              ['f1',    '',                 None],
              ['f2',    'MAIN',             ['lambda: change_tid("TID", "accdisp")']],
              ['f3',    'MAPS',             ['lambda: change_tid("TID", "accmaps")']],
              ['f4',    '',                 None]
              ]


accappehkd = [['a1',    '',                 None],
              ['a2',    'RNP\nY 03',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 833")']],
              ['a3',    'RNP\nY 21',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 837")']],
              ['a4',    '',                 None],

              ['b1',    'KD\n21',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 792")']],
              ['b2',    'RNP Y\nNAMES\n03', ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 834")']],
              ['b3',    'RNP Y\nNAMES\n21', ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 838")']],
              ['b4',    '',                 None],

              ['c1',    '',                 None],
              ['c2',    'RNP\nZ 03',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 835")']],
              ['c3',    'RNP\nZ 21',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 839")']],
              ['c4',    '',                 None],

              ['d1',    '',                 None],
              ['d2',    'RNP Z\nNAMES\n03', ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 836")']],
              ['d3',    'RNP Z\nNAMES\n21', ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 840")']],
              ['d4',    '',                 None],

              ['e1',    '',                 None],
              ['e2',    '',                 None],
              ['e3',    '',                 None],
              ['e4',    '',                 None],

              ['f1',    '',                 None],
              ['f2',    'MAIN',             ['lambda: change_tid("TID", "accdisp")']],
              ['f3',    'MAPS',             ['lambda: change_tid("TID", "accmaps")']],
              ['f4',    '',                 None]
              ]


accappmiln = [['a1',    '',                 None],
              ['a2',    'LW\n05',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 795")']],
              ['a3',    'LE\n05',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 826")']],
              ['a4',    'DL\n02',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 783")']],

              ['b1',    'KD\n21',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 792")']],
              ['b2',    'LW\n09',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 796")']],
              ['b3',    'LE\n23',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 829")']],
              ['b4',    'DL\n20',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 784")']],

              ['c1',    '',                 None],
              ['c2',    'LW\n23',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 797")']],
              ['c3',    '',                 None],
              ['c4',    'TW',               ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 800")']],

              ['d1',    '',                 None],
              ['d2',    'LW\n27',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 798")']],
              ['d3',    '',                 None],
              ['d4',    'TE\n26',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 799")']],

              ['e1',    '',                 None],
              ['e2',    '',                 None],
              ['e3',    '',                 None],
              ['e4',    '',                 None],

              ['f1',    '',                 None],
              ['f2',    'MAIN',             ['lambda: change_tid("TID", "accdisp")']],
              ['f3',    'MAPS',             ['lambda: change_tid("TID", "accmaps")']],
              ['f4',    '',                 None]
              ]


accappmils = [['a1',    'WO\n07',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 805")']],
              ['a2',    'GR\n02',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 787")']],
              ['a3',    'EH\n03',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 785")']],
              ['a4',    'VK\n06L',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 801")']],

              ['b1',    'WO\n25',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 806")']],
              ['b2',    'GR\n10',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 788")']],
              ['b3',    'EH\n21',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 786")']],
              ['b4',    'VK\n06R',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 802")']],

              ['c1',    '',                 None],
              ['c2',    'GR\n20',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 789")']],
              ['c3',    'BD\n21',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 780")']],
              ['c4',    'VK\n24L',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 803")']],

              ['d1',    'LV\n09',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 793")']],
              ['d2',    'GR\n28',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 790")']],
              ['d3',    'BL\n05R',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 781")']],
              ['d4',    'VK\n24R',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 804")']],

              ['e1',    'LV\n27',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 794")']],
              ['e2',    '',                 None],
              ['e3',    'BL\n23L',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 782")']],
              ['e4',    '',                 None],

              ['f1',    '',                 None],
              ['f2',    'MAIN',             ['lambda: change_tid("TID", "accdisp")']],
              ['f3',    'MAPS',             ['lambda: change_tid("TID", "accmaps")']],
              ['f4',    '',                 None]
              ]


accmilehr8 = [['a1',    'EHR8\nNORTH',      ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 815")']],
              ['a2',    'EHR8\nMID',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 816")']],
              ['a3',    'EHR8\nSOUTH',      ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 817")']],
              ['a4',    '',                 None],

              ['b1',    '',                 None],
              ['b2',    '',                 None],
              ['b3',    '',                 None],
              ['b4',    '',                 None],

              ['c1',    '',                 None],
              ['c2',    '',                 None],
              ['c3',    '',                 None],
              ['c4',    '',                 None],

              ['d1',    '',                 None],
              ['d2',    '',                 None],
              ['d3',    '',                 None],
              ['d4',    '',                 None],

              ['e1',    '',                 None],
              ['e2',    '',                 None],
              ['e3',    '',                 None],
              ['e4',    '',                 None],

              ['f1',    '',                 None],
              ['f2',    'MAIN',             ['lambda: change_tid("TID", "accdisp")']],
              ['f3',    'MAPS',             ['lambda: change_tid("TID", "accmaps")']],
              ['f4',    '',                 None]
              ]


accmilmisc = [['a1',    'RP\nNAMES',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 772")']],
              ['a2',    'RP\nSYMB',         ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 771")']],
              ['a3',    'CTRS',             ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 762")']],
              ['a4',    'MC\nPNTS',         ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 358")']],

              ['b1',    'EHEH03\nNAMES',    ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 768")']],
              ['b2',    'EHEH03\nSYMB',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 767")']],
              ['b3',    'NR\nVA',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 811")']],
              ['b4',    'NEW\nPNTS',        ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 779")']],

              ['c1',    'EHEH21\nNAMES',    ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 770")']],
              ['c2',    'EHEH21\nSYMB',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 769")']],
              ['c3',    'EHLE\nNAMES',      ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 823")']],
              ['c4',    'EHLE\nSYMB',       ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 828; MAPTOGGLE MAP 831")']],

              ['d1',    'EHKD\nNAMES',      ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 776")']],
              ['d2',    'EHKD\nSYMB',       ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 775")']],
              ['d3',    '',                 None],
              ['d4',    '',                 None],

              ['e1',    'NAVAID\nNAMES',    ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 774")']],
              ['e2',    'NAVAID\nSYMB',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 773")']],
              ['e3',    '',                 None],
              ['e4',    '',                 None],

              ['f1',    '',                 None],
              ['f2',    'MAIN',             ['lambda: change_tid("TID", "accdisp")']],
              ['f3',    'MAPS',             ['lambda: change_tid("TID", "accmaps")']],
              ['f4',    '',                 None]
              ]


accmisc = [['a1',    'NL\nGEO',             ['lambda: console.Console._instance.stack("SWRAD GEO")']],
           ['a2',    'AMST\nCITY',          ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 452")']],
           ['a3',    'D/F\nSTAT',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 478")']],
           ['a4',    '',                    None],

           ['b1',    'NL\nFIC',             ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 441; MAPTOGGLE MAP 442; MAPTOGGLE MAP 443; MAPTOGGLE MAP 444; MAPTOGGLE MAP 445; MAPTOGGLE MAP 446")']],
           ['b2',    'NL\nBASIC',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 758")']],
           ['b3',    '',                    None],
           ['b4',    '',                    None],

           ['c1',    'AIRFNAMES',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 481")']],
           ['c2',    '',                    None],
           ['c3',    'RP\nNAMES',           ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 476")']],
           ['c4',    '',                    None],

           ['d1',    '',                    None],
           ['d2',    '',                    None],
           ['d3',    '',                    None],
           ['d4',    '',                    None],

           ['e1',    '',                    None],
           ['e2',    '',                    None],
           ['e3',    '',                    None],
           ['e4',    '',                    None],

           ['f1',    '',                    None],
           ['f2',    'MAIN',                ['lambda: change_tid("TID", "accdisp")']],
           ['f3',    'MAPS',                ['lambda: change_tid("TID", "accmaps")']],
           ['f4',    '',                    None]
           ]
