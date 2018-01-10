import sys
import os

data = open('total_track_file.txt','r')
data_lines = data.readlines()
data.close()

btf = open('full_btf_list.txt','w')
kinf = open('full_kinf_list.txt','w')
score = open('full_score_list.txt','w')
for line in data_lines:
  elems = line.strip().split()
  score.write(elems[0]+'\n')
  btf.write(elems[1]+'\n')
  kinf.write(elems[2]+'\n')

btf.close()
kinf.close()
score.close()

metrics = open('metrics_file.txt','r')
metric_lines = metrics.readlines()
metrics.close()
max_score_list = []
for line in metric_lines:
  elems = line.strip().split()
  if(len(elems) > 0):
    if(elems[0] == 'Minimum'):
      max_score_list.append(elems[7])

metric_results = open('metric_results.txt','w')
print max_score_list
for line in data_lines:
  elems = line.strip().split()
  for score in max_score_list:
    if(elems[0] == score):
      string_one = str(elems[0])
      string_two = str(elems[1])
      print string_two
      string_three = str(elems[2])
      metric_results.write(string_one.ljust(20) + string_two.ljust(20) + string_three.ljust(20) + '\n')

metric_results.close()

parent_metrics = open('parent_metric_results.txt','w')
parent_file = open('parent_list.txt','r')
parent_lines = parent_file.readlines()
parent_file.close()

parent_score_list = []
for line in parent_lines:
  elems = line.strip().split()
  if(len(elems) > 0):
    if(elems[0] == 'Lattice_Cost:'):
      parent_score_list.append(elems[1])

for parent in parent_score_list:
  for line in data_lines:
    elems = line.strip().split()
    if(elems[0] == parent):
      string_one = str(elems[0])
      string_two = str(elems[1])
      string_three = str(elems[2])
      parent_metrics.write(string_one.ljust(20) + string_two.ljust(20) + string_three.ljust(20) + '\n')
parent_metrics.close()
