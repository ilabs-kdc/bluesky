import numpy as np
import pandas as pd
import fortranformat as ff

climb = 'I6, 1X, I3, 1X, I6, 1X, F7.3, 1X, I7, 2(1X, F8.2), 1X, F7.2, 1X, I6, 2(1X, I9), 1X, F7.1, 1X, F7.2, 1X, I7, 1X, I8, 1X, F7.2'
descent = 'I6, 1X, I3, 1X, I6, 1X, F7.3, 1X, I7, 2(1X, F8.2), 1X, F7.2, 1X, I6, 2(1X, I9), 1X, F7.1, 1X, F7.2, 1X, I7, 1X, I8, 1X, F8.2'

FL_index = 0
ESF_index = 12



class ESFinterpolate():

    def __init__(self):
        self.FL =           np.array([])
        self.ESF_climb =    np.array([])
        self.ESF_descent =  np.array([])

    def read_data(self, bada_path):

        data_file = bada_path + '/' + type + '__.PTD'
        data = pd.read_csv(data_file)['BADA PERFORMANCE FILE RESULTS']

        climb_reader = ff.FortranRecordReader(climb)
        descent_reader = ff.FortranRecordReader(descent)

        table_count = 0
        correct_set = False

        for i, line in data:
            if correct_set:
                if line.isspace():
                    correct_set = False
                    continue

                if climb:
                    data_points = climb_reader.read(line)
                if descent:
                    data_points = descent_reader.read(line)

                # if data_points[0] < alt:
                #     FL_1, ESF_1 = climb_reader.read(data[i - 1])[FL_index], climb_reader.read(data[i - 1])[ESF_index]
                #     FL_2, ESF_2 = climb_reader.read(data[i])[FL_index], climb_reader.read(data[i])[ESF_index]
                #
                #     ESF_c = (ESF_2 - ESF_1) / (FL_2 - FL_1) * (FL - FL_1) + ESF_1
                #
                #     return ESF_c

            if 'FL[-]' in i:
                table_count += 1
                if table_count == 2:
                    climb = True







#
# def esf_test(bada_path, alt=0, type='B744', climb=True):
#     # if descent climb=False
#
#     data_file = bada_path + '/' +type + '__.PTD'
#     # print('filepath', data_file)
#
#     climb = 'I6, 1X, I3, 1X, I6, 1X, F7.3, 1X, I7, 2(1X, F8.2), 1X, F7.2, 1X, I6, 2(1X, I9), 1X, F7.1, 1X, F7.2, 1X, I7, 1X, I8, 1X, F7.2'
#     descent = 'I6, 1X, I3, 1X, I6, 1X, F7.3, 1X, I7, 2(1X, F8.2), 1X, F7.2, 1X, I6, 2(1X, I9), 1X, F7.1, 1X, F7.2, 1X, I7, 1X, I8, 1X, F8.2'
#
#     FL_index = 0
#     ESF_index = 12
#
#     FL = alt/0.3048/100 # to FL
#
#
#     climb_reader = ff.FortranRecordReader(climb)
#     descent_reader = ff.FortranRecordReader(descent)
#
#     data = pd.read_csv(data_file)['BADA PERFORMANCE FILE RESULTS']  # , delimiter=r"\s+")
#
#     new_set = False
#     count = 0
#     table_count = 0
#
#     x_fl = []
#     y_esf = []
#
#     correct_set = False
#
#     for i,line in data:
#         if correct_set:
#             if climb:
#                 data_points = climb_reader.read(line)
#             else:
#                 data_points = descent_reader.read(line)
#
#             if data_points[0] < alt:
#                 FL_1, ESF_1 = climb_reader.read(data[i - 1])[FL_index], climb_reader.read(data[i - 1])[ESF_index]
#                 FL_2, ESF_2 = climb_reader.read(data[i ])[FL_index], climb_reader.read(data[i])[ESF_index]
#
#                 ESF_c = (ESF_2-ESF_1)/(FL_2-FL_1) * (FL-FL_1) + ESF_1
#
#                 return ESF_c
#
#         if 'FL[-]' in i:
#             table_count += 1
#             if table_count == 2:
#                 correct_set = True
#
#     #
#     #
#     #
#     # for i in data:
#     #     if new_set:
#     #         if table_count < 3:
#     #             data_points = climb_reader.read(i)
#     #         else:
#     #             data_points = descent_reader.read(i)
#     #         x_fl.append(data_points[0])
#     #         y_esf.append(data_points[12])
#     #         count += 1
#     #     if count >= 10:
#     #         new_set = False
#     #         count = 0
#     #         if table_count == 4: table_count = 'descent'
#     #         plt.plot(x_fl, y_esf, label=str(table_count))
#     #         print(x_fl, y_esf)
#     #         x_fl, y_esf = [], []
#     #     if 'FL[-]' in i:
#     #         new_set = True
#     #         table_count += 1
#     #
#     # plt.legend()
#     # plt.show()
#
#     esf = 0
#
#     return esf