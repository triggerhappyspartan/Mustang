import sys
import os
import os.path
import numpy as np
import random
import time
import math
import reproduction
import metrics
import casmo_functions
import fuel_assembly
import subprocess
####################################################
#             Define Parameters
####################################################
input_file = 'input_data.txt'
upper_file = 'upper_guide_assembly.inp'
lower_file = 'lower_guide_assembly.inp'
lower_skip = 47
upper_skip = 56
initial_mutation_rate = 0.25
target_mutation_rate = 0.70
#batch_size = 18
#random.seed(12)
###############################################
#        Class Definitions
###############################################
class inputs:
# A class to organize all input information
      def __init__(self, name):
      #Initialize all information recorded by teh input class
          self.name = name
          self.number_allowable_rod_types = 8
          self.number_of_regions = 0
          self.region_map = []
          self.rod_list = []
      def read_input_data(self, filename):
      #Reads the input file and stores the information in the applicable location.
          input_file = open(filename,'r')
          info = input_file.readlines()
          input_file.close()
          for line in info:
            elems = line.strip().split()
            if(len(elems) > 0):
              if(elems[0] == 'number_of_regions'):
                self.number_of_regions = int(elems[2])
                for i in xrange(int(elems[2])+1):
                  self.rod_list.append([])
                self.rod_list[0] = [['0','0']]
              #  print self.region_list
              elif(elems[0] == 'rod'):
                place = int(elems[1])
                temp_stuff = [elems[2],elems[3]]
                self.rod_list[place].append(temp_stuff)
              #  print self.region_list
              elif(elems[0] == 'pin_map'):
                for i in range(1,len(elems)):
                  self.region_map.append(int(elems[i]))
      def make_input_lattices(self):
      #Makes rod lattices for the initial rod bundles.
          lattice = []
          temp_rod_list = []
          for i in xrange(self.number_allowable_rod_types):
            x = random.randint(0,len(self.rod_list[1])-1)
            temp_rod_list.append(x)
          for i in self.region_map:
            if(i == 1):
              x = random.choice(temp_rod_list)
              lattice.append(x)
            else:
              x = 0
              lattice.append(x)
          return (lattice,temp_rod_list)
input_data = inputs('Optimization Parameters')
input_data.read_input_data(input_file)
number_changes = 0
for i in input_data.region_map:
  number_changes = number_changes + len(input_data.rod_list[i])

temp = number_changes**0.333333333333333333333333333333
population = 40*temp
temp = population % batch_size
temp = batch_size - temp
population = population + temp
population = int(population)

number_of_generations = population*population/1500
number_of_generations = int(number_of_generations) + 2

casmo = open(upper_file,'r')
upper_casmo_lines = casmo.readlines()
casmo.close()

casmo = open(lower_file,'r')
lower_casmo_lines = casmo.readlines()
casmo.close()

number_batches = population/batch_size

new_lattice_list = reproduction.extract_lattices('parent_list.txt')
lattice_count = 0
batch_number = 0
for lattice in new_lattice_list:
  (lower_lattice,upper_lattice) = reproduction.decode_rod_lattice(lattice, input_data.region_map, input_data.rod_list)
  casmo = open('batch_'+str(batch_number)+'.lower_assembly.'+str(lattice_count+1)+'.inp','w')
  pin_map = metrics.return_pin_map(lower_lattice)
  line_number = 1
  for line in lower_casmo_lines:
    if(line_number == lower_skip):
      casmo.write(pin_map)
    elif(line_number > lower_skip and line_number <= upper_skip):
      pass
    else: casmo.write(line)
    line_number+=1
  casmo.close()
  lattice_count+=1
  if(lattice_count == batch_size):
    lattice_count = 0
    batch_number+=1

script_name = 'final_submission'
script = open(script_name,'w')
script.write('#! /bin/sh\n')
script.write('#\n')
script.write('#PBS -N Mustang_final\n')
script.write('#PBS -e error.dat\n')
script.write('#PBS -o info.dat\n')
script.write('#PBS -q default\n')
script.write('#PBS -l nodes=1:ppn=1\n')
script.write('#PBS -t 1-'+str(batch_size)+'\n')
script.write('\n')
script.write('#\n')
script.write('cd $PBS_O_WORKDIR\n')
script.write('date\n')
script.write('echo "starting job..."\n\nls\n\n')
for i in xrange(number_batches):
  script.write('casmo4e -v u1.00.02 batch_'+str(i)+'.lower_assembly.$PBS_ARRAYID.inp\n\n')
script.close()
pwd = os.getcwd()
os.system("ssh rdfmg 'cd "+pwd+"; qsub final_submission'")



search_string = 'Average number of pins per assembly:'
metric_file = open('metrics_file.txt','r')
metric_lines = metric_file.readlines()
metric_file.close()
search_elems = search_string.strip().split()
line_count = 100
lattice_list = []
lattice_count = 0
batch_count = 0
for line in metric_lines:
  print line
  elems = line.strip().split()
  if(len(elems) > len(search_elems)):
    print 'Fuck YOu'
    nmatch = 0
    elemcount = 0
    for el in search_elems: 
      if(el == elems[elemcount]):
        nmatch+=1
      elemcount+=1
    if(nmatch == len(search_elems)):
      line_count = 0
      print 'It Matched'
      temp_lattice = []
  if(line_count > 0 and line_count < 11):
    for el in elems:
      werd = list(el)
      true_werd = ''
      for x in werd:
        if(x == '['):
          pass
        elif(x == ','):
          pass
        elif(x == ']'):
          pass
        else:
          true_werd = true_werd + x

#      print true_werd
      elemcount+=1
#      print 'Elemcount is '+str(elemcount)
      temp_lattice.append(int(true_werd))
  if(line_count == 12):
    (lower_lattice,upper_lattice) = reproduction.decode_rod_lattice(temp_lattice,input_data.region_map,input_data.rod_list)
    casmo = open('batch_'+str(batch_count)+'.assembly.'+str(lattice_count+1)+'.inp','w')
    pin_map = metrics.return_pin_map(lower_lattice)
    line_number = 1
    for line in lower_casmo_lines:
      if(line_number == lower_skip):
        casmo.write(pin_map)
      elif(line_number > lower_skip and line_number <= upper_skip):
        pass
      else: casmo.write(line)
      line_number+=1
    casmo.close()
    lattice_count+=1
    if(lattice_count == batch_size):
      batch_count+=1
      lattice_count = 0
  line_count+=1


job_name = 'Mustang_final'
job_finished = False
start = time.clock()
while(job_finished == False):
  finish = time.clock()
  if(finish-start>30):  #Checks every three seconds to see if the current batch
    job_finished = casmo_functions.check_job_status(job_name) #of input files has finished.
    start = time.clock()


script_name = 'final_submission'
script = open(script_name,'w')
script.write('#! /bin/sh\n')
script.write('#\n')
script.write('#PBS -N Mustang_final\n')
script.write('#PBS -e error.dat\n')
script.write('#PBS -o info.dat\n')
script.write('#PBS -q default\n')
script.write('#PBS -l nodes=1:ppn=1\n')
script.write('#PBS -t 1-'+str(batch_size)+'\n')
script.write('\n')
script.write('#\n')
script.write('cd $PBS_O_WORKDIR\n')
script.write('date\n')
script.write('echo "starting job..."\n\nls\n\n')
for i in xrange(number_batches):
  script.write('casmo4e -v u1.00.02 batch_'+str(i)+'.assembly.$PBS_ARRAYID.inp\n\n')
script.close()
pwd = os.getcwd()
os.system("ssh rdfmg 'cd "+pwd+"; qsub final_submission'")

finish = time.clock()
start = time.clock()
while(finish - start < 60):
  finish = time.clock()

cost_file = open('final_cost_list.txt','w')
btf_file = open('final_btf_list.txt','w')
kinf_list = open('final_kinf_list.txt','w')
for j in xrange(number_batches):
  for k in xrange(batch_size):
    lower_lattice_file = open('batch_'+str(j)+'.lower_assembly.'+str(k+1)+'.out','r')
    lower_lattice_lines = lower_lattice_file.readlines()
    lower_lattice_file.close()


    kinf_two = fuel_assembly.search_for_k_inf(lower_lattice_lines)
    average_kinf = 0
    for elem in kinf_two:
      average_kinf+=elem
    average_kinf = average_kinf/3
    power_two = fuel_assembly.search_power_distributions(lower_lattice_lines)

    btf_list = casmo_functions.two_d_btf(kinf_two,power_two)
    average_btf = 0
    for elem in btf_list:
      average_btf+=elem
    average_btf = average_btf/3

    score = casmo_functions.two_d_score(kinf_two,btf_list)
    cost_file.write(str(score)+'\n')
    btf_file.write(str(average_btf)+'\n')
    kinf_list.write(str(average_kinf)+'\n')

cost_file.close()
btf_file.close()
kinf_list.close()

job_name = 'Mustang_final'
job_finished = False
start = time.clock()
while(job_finished == False):
  finish = time.clock()
  if(finish-start>30):  #Checks every three seconds to see if the current batch
    job_finished = casmo_functions.check_job_status(job_name) #of input files has finished.
    start = time.clock()


finish = time.clock()
start = time.clock()
while(finish - start < 60):
  finish = time.clock()


cost_file = open('generation_cost_list.txt','w')
btf_file = open('generation_btf_list.txt','w')
kinf_list = open('generation_kinf_list.txt','w')
for j in xrange(number_batches):
  for k in xrange(batch_size):
    lattice_file = open('batch_'+str(j)+'.assembly.'+str(k+1)+'.out','r')
    lattice_lines = lattice_file.readlines()
    lattice_file.close()


  kinf_two = fuel_assembly.search_for_k_inf(lattice_lines)
  average_kinf = 0
  for elem in kinf_two:
    average_kinf+=elem
  average_kinf = average_kinf/3
  power_two = fuel_assembly.search_power_distributions(lattice_lines)

  btf_list = two_d_btf(kinf_two,power_two)
  average_btf = 0
  for elem in btf_list:
    average_btf+=elem
  average_btf = average_btf/3

  score = two_d_score(kinf_two,btf_list)
  cost_file.write(str(score)+'\n')
  btf_file.write(str(average_btf)+'\n')
  kinf_list.write(str(average_kinf)+'\n')

cost_file.close()
btf_file.close()
kinf_list.close()

