#restart.py
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

###############################################
#        Class Definitions
###############################################
class inputs:
# A class to organize all input information
      def __init__(self, name):
      #Initialize all information recorded by teh input class
          self.name = name
          self.number_allowable_rod_types = 15
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


############################################
#             Main Program
############################################
next_gen_file = open('next_generation_information.txt')
next_gen_lines = next_gen_file.readlines()
next_gen_file.close()

for line in next_gen_lines:
  elems = line.strip().split()
  if(elems[0] == 'generation'):
    generation = int(elems[1])
  elif(elems[0] == 'lambda'):
    lambda_s = float(elems[1])
  elif(elems[0] == 'mutation_rate'):
    mutation_rate = float(elems[1])
  elif(elems[0] == 'population'):
    population = int(elems[1])
  elif(elems[0] == 'batch_size'):
    batch_size = int(elems[1])
  elif(elems[0] == 'input_file'):
    input_file = elems[1]
  elif(elems[0] == 'lower_file'):
    lower_file = elems[1]
  elif(elems[0] == 'upper_file'):
    upper_file = elems[1]
  elif(elems[0] == 'final_generation'):
    final_generation = int(elems[1])
  elif(elems[0] == 'lower_skip'):
    lower_skip = int(elems[1])
  elif(elems[0] == 'upper_skip'):
    upper_skip = int(elems[1])

number_batches = population/batch_size

casmo = open(upper_file,'r')
upper_casmo_lines = casmo.readlines()
casmo.close()

casmo = open(lower_file,'r')
lower_casmo_lines = casmo.readlines()
casmo.close()


#os.remove('next_generation_information.txt')
input_data = inputs('Optimization Parameters')
input_data.read_input_data(input_file)


for i in range(generation, final_generation):
  casmo_functions.evaluate_bundles(batch_size,generation,population)
  reproduction.merge_files('cost_list.txt','child_list.txt')
  reproduction.tournament('parent_list.txt','child_list.txt')
  lattice_list = reproduction.extract_lattices('parent_list.txt')
  (single_mutation_list,double_mutation_list,crossover_list) = reproduction.method_of_reproduction(lattice_list,mutation_rate)
  file_exists = os.path.isfile('child_list.txt')
  if(file_exists == True):
    os.remove('child_list.txt')
  reproduction.crossover(crossover_list,input_data.region_map, input_data.rod_list)
  for i in xrange(len(single_mutation_list)):
    active_rods = reproduction.return_active_rod_list(single_mutation_list[i],input_data.region_map)
    reproduction.single_mutation(single_mutation_list[i], active_rods, input_data.region_map, input_data.rod_list)
  for i in xrange(len(double_mutation_list)):
    active_rods = reproduction.return_active_rod_list(double_mutation_list[i],input_data.region_map)
    reproduction.double_mutation(double_mutation_list[i], active_rods, input_data.region_map, input_data.rod_list)
  new_lattice_list = reproduction.extract_lattices('child_list.txt')
  os.system('rm batch_* info-dat* error-dat*')
  lattice_count = 0
  for batch in xrange(number_batches):
    for people in xrange(batch_size):
      (lower_lattice,upper_lattice) = reproduction.decode_rod_lattice(new_lattice_list[lattice_count], input_data.region_map, input_data.rod_list)
      print new_lattice_list[lattice_count]
      print lower_lattice
      print upper_lattice
      pin_map = metrics.return_pin_map(lattice_count+=1)
      casmo = open('batch_'+str(batch)+'.lower_assembly.'+str(people+1)+'.inp','w')
      for line in lower_casmo_lines:
        if(line_number == lower_skip):
          casmo.write(pin_map)
        elif(line_number > lower_skip and line_number <= upper_skip):
          pass
        else: casmo.write(line)
        line_number+=1
      casmo.close()
      lattice_count+=1
  mutation_rate = reproduction.update_mutation_rate(lambda_s,mutation_rate)

  next_gen_file = open('next_generation_information.txt','w')
  next_gen_file.write('generation             '+str(generation)+'\n')
  next_gen_file.write('lambda                 '+str(lambda_s)+'\n')
  next_gen_file.write('mutation_rate          '+str(mutation_rate)+'\n')
  next_gen_file.write('population             '+str(population)+'\n')
  next_gen_file.write('batch_size             '+str(batch_size)+'\n')
  next_gen_file.write('input_file             '+input_file+'\n')
  next_gen_file.write('lower_file             '+lower_file+'\n')
  next_gen_file.write('upper_file             '+upper_file+'\n')
  next_gen_file.write('final_generation       '+str(final_generation)+'\n')
  next_gen_file.write('lower_skip             '+str(lower_skip)+'\n')
  next_gen_file.write('upper_skip             '+str(upper_skip)+'\n')
  next_gen_file.close()


casmo_functions.evaluate_bundles(batch_size,generation,population)
reproduction.merge_files('cost_list.txt','child_list.txt')
reproduction.tournament('parent_list.txt','child_list.txt')
lattice_list = reproduction.extract_lattices('parent_list.txt')
lattice_count = 0
for batch in xrange(number_batches):
  for people in xrange(batch_size):
    (lower_lattice,upper_lattice) = reproduction.decode_rod_lattice(new_lattice_list[lattice_count], input_data.region_map, input_data.rod_list)
    casmo = open('final_batch_'+str(batch)+'.upper_assembly.'+str(people+1)+'.inp','w')
    pin_map = metrics.return_pin_map(upper_lattice)
    line_number = 1
    for line in upper_casmo_lines:
      if(line_number == lower_skip):
        casmo.write(pin_map)
      elif(line_number > lower_skip and line_number < upper_skip):
        pass
      else: casmo.write(line)
      line_number+=1
    casmo.close()
    casmo = open('final_batch_'+str(batch)+'.lower_assembly.'+str(people+1)+'.inp','w')
    for line in lower_casmo_lines:
      if(line_number == lower_skip):
        casmo.write(pin_map)
      elif(line_number > lower_skip and line_number < upper_skip):
        pass
      else: casmo.write(line)
      line_number+=1
    casmo.close()
    lattice_count+=1
script_name = 'final_submission'
script = open(script_name,'w')
script.write('#! /bin/sh\n')
script.write('#\n')
script.write('#PBS -N Mustang_final\n')
script.write('#PBS -e error.dat\n')
script.write('#PBS -o info.dat\n')
script.write('#PBS -q default\n')
script.write('#PBS -l nodes=1:ppn=20\n')
script.write('#PBS -t 1-'+str(batch_size)+'\n')
script.write('\n')
script.write('#\n')
script.write('cd $PBS_O_WORKDIR\n')
script.write('date\n')
script.write('echo "starting job..."\n\nls\n\n')
for i in xrange(number_batches):
  script.write('casmo4e -v u1.00.02 final_batch_'+str(i)+'.upper_assembly.$PBS_ARRAYID.inp\n\n')
  script.write('casmo4e -v u1.00.02 final_batch_'+str(i)+'.lower_assembly.$PBS_ARRAYID.inp\n\n')
script.close()
os.system("ssh rdfmg 'cd "+pwd+"; qsub final_submission'")
job_name = 'Mustang_final'
job_finished = False
start = time.clock()
while(job_finished == False):
  finish = time.clock()
  if(finish-start>30):  #Checks every three seconds to see if the current batch
    job_finished = casmo_functions.check_job_status(job_name) #of input files has finished.
    start = time.clock()
bottom_file = open('bottom_lattice.out','r')
bottom_lines = bottom_file.readlines()
bottom_file.close()

top_file = open('top_lattice.out','r')
top_lines = top_file.readlines()
top_file.close()

kinf_one = fuel_assembly.search_for_k_inf(bottom_lines)
kinf_four = fuel_assembly.search_for_k_inf(top_lines)
power_one = fuel_assembly.search_power_distributions(bottom_lines)
power_four = fuel_assembly.search_power_distributions(top_lines)

number_batches = population/batch_size

plot_curve = open('surface_values.txt','w')
for i in xrange(number_batches):
  for j in xrange(batch_size):
    lower_lattice_file = open('final_batch_'+str(i)+'.lower_assembly.'+str(j+1)+'.out','r')
    lower_lattice_lines = lower_lattice_file.readlines()
    lower_lattice_file.close()

    upper_lattice_file = open('final_batch_'+str(i)+'.upper_assembly.'+str(j+1)+'.out','r')
    upper_lattice_lines = upper_lattice_file.readlines()
    upper_lattice_file.close()

    kinf_two = fuel_assembly.search_for_k_inf(lower_lattice_lines)
    kinf_three = fuel_assembly.search_for_k_inf(upper_lattice_lines)

    power_two = fuel_assembly.search_power_distributions(lower_lattice_lines)
    power_three = fuel_assembly.search_power_distributions(upper_lattice_lines)

    btf_list = fuel_assembly.calculate_btf(kinf_one,kinf_two,kinf_three,kinf_four,power_one,power_two,power_three,power_four)

    btf_sum = 0
    for foo in btf_list:
      btf_sum+=foo

    average_kinf_list = fuel_assembly.average_kinf_values_over_burnup(kinf_one,kinf_two,kinf_three,kinf_four)
    kinf_sum = 0
    for foo in average_kinf_list:
      kinf_sum+=foo
    temp_one = str(btf_sum)
    plot_curve.write(temp_one.ljust(20) + str(kinf_sum)+'\n')

plot_curve.close()

