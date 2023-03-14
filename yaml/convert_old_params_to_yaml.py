from EVONode import EVONode
from EVOThreads import SaveToFileThread
from work_with_file import fill_sheet_dict

nodes_list = fill_sheet_dict('../python_for_help/TheBestNode.xlsx')
best_node = EVONode(group_par_dict=nodes_list['Sheet1'])
tr = SaveToFileThread()
tr.node_to_save = best_node
tr.save_file()
print()
