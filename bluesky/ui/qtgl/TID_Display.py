from bluesky.ui.qtgl.TIDS import *

start2 = [['a1',    '',        None],
         ['a2',    '',        None],
         ['a3',    '',        None],
         ['a4',    '',        None],

         ['b1',    '',        None],
         ['b2',    '',        None],
         ['b3',    '',        None],
         ['b4',    '',        None],

         ['c1',    '',        None],
         ['c2',    'BASE',    ['lambda: start2.close()',
                               'lambda: show_basetid2("base", "base")']],
         ['c3',    'APP',     ['lambda: console.Console._instance.stack("MAPTOGGLE MAP 252")',
                               'lambda: start2.close()',
                               'lambda: show_basetid2("appdisp","appdisp")']],
         ['c4',    '',        None],

         ['d1',    '',        None],
         ['d2',    '',        None],
         ['d3',    'ACC',     ['lambda: console.Console._instance.stack("ATCMODE ACC")',
                               'lambda: console.Console._instance.stack("MAPTOGGLE MAP 751; MAPTOGGLE MAP 752")',
                               'lambda: start2.close()',
                               'lambda: show_basetid("accmain", "accmain")']],
         ['d4',    '',        None],

         ['e1',    '',        None],
         ['e2',    '',        None],
         ['e3',    '',        None],
         ['e4',    '',        None],

         ['f1',    '',        None],
         ['f2',    '',        None],
         ['f3',    '',        None],
         ['f4',    '',        None]]