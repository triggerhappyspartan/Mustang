import os
import sys

document = open('metrics_file.txt','r')
document_lines = document.readlines()
document.close()

average_list = []
minimum_list = []
maximum_list = []

for line in document_lines:
  elems = line.strip().split()
  if(len(elems) > 0):
    if(elems[0] == 'Average' and elems[1] == 'Lattice'):
      average_list.append(elems[3])
    elif(elems[0] == 'Minimum'):
      minimum_list.append(elems[3])
      maximum_list.append(elems[7])

document = open('for_plotting.txt','w')
document.write('average\n')
for item in average_list:
  document.write(item + '\n')
document.write('minimum\n')
for item in minimum_list:
  document.write(item + '\n')
document.write('maximum\n')
for item in maximum_list:
  document.write(item + '\n')

document.close() 
