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
lower_skip = 52
upper_skip = 61
initial_mutation_rate = 0.25
target_mutation_rate = 0.700
batch_size = 16
#random.seed(12)
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
          number_axial_zones = 1
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
#          for i in xrange(self.number_allowable_rod_types):
#            x = random.randint(0,len(self.rod_list[1])-1)
#            temp_rod_list.append(x)
          for i in self.region_map:
            if(len(self.rod_list[i]) > 1):
              x = random.randint(0,len(self.rod_list[i])-1)
              lattice.append(x)
            else:
              x = 0
              lattice.append(x)
          return (lattice,temp_rod_list)


#########################################################################################################
#             Main Program
##########################################################################################################
###########################################################
#This block of code reads the input file.
os.system('rm total_track_file.txt')
os.system('rm upper_assembly.* lower_assembly.* info.dat-* error.dat-* batch_*')
input_data = inputs('Optimization Parameters')
input_data.read_input_data(input_file)
os.system('rm metrics_file.txt')
os.system('rm parent_list.txt child_list.txt cost_list.txt')
number_changes = 0
for i in input_data.region_map:
  number_changes = number_changes + len(input_data.rod_list[i])
#############################################################
#This block of code calculates population size and the number of generations for which the optimization will run.

#temp = number_changes**0.333333333333333333333333333333
#population = 25*temp
#temp = population % batch_size
#temp = batch_size - temp
#population = population + temp
#population = int(population)
population = number_changes**0.33333333
population = number_changes**0.5
temp = population % batch_size
temp = batch_size - temp
population = population + temp
population = int(population)
number_of_generations = population*3
number_of_generations = int(number_of_generations) + 2
population = number_changes**0.5
population = int(population)
population = population*10

metrics_file = open('metrics_file.txt','a')
metrics_file.write('Number of Changes   '+str(number_changes)+'\n')
metrics_file.write('Population    '+str(population)+'\n')
metrics_file.write('Number of Generations      '+str(number_of_generations)+'\n')
metrics_file.close()

################################################################
#This block of code reads the casmo files that act as guides for the dominant and power shaping zones.
casmo = open(upper_file,'r')
upper_casmo_lines = casmo.readlines()
casmo.close()

casmo = open(lower_file,'r')
lower_casmo_lines = casmo.readlines()
casmo.close()

number_batches = population/batch_size
#number_batches = 5
#population = number_batches*batch_size
final_generation = number_of_generations - 1 #not sure this line of code does anything
########################################################################
#This batch of code writes the initial Casmo input files for the population. 
parent = open('parent_list.txt','w+')
for batch in xrange(number_batches):
  for people in xrange(batch_size):
    lattice_list = []
    (temp_lattice,temp_rod_list) = input_data.make_input_lattices()
    temp_str_map = []
    for t in temp_lattice:
      temp_str_map.append(str(t))
    lattice_list.append(temp_str_map)
    temp_rod_map = metrics.return_pin_map(temp_str_map)
    parent.write('Assembly\n')
    parent.write(temp_rod_map)
    parent.write('What Happened: Original_file\n\n')

#    print temp_lattice
    (lower_lattice,upper_lattice) = reproduction.decode_rod_lattice(temp_lattice,input_data.region_map, input_data.rod_list)
    casmo = open('batch_'+str(batch)+'.lower_assembly.'+str(people+1)+'.inp','w')
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
    casmo = open('batch_'+str(batch)+'.upper_assembly.'+str(people+1)+'.inp','w')
    pin_map = metrics.return_pin_map(upper_lattice)
    line_number = 1
    for line in upper_casmo_lines:
      if(line_number == lower_skip):
        casmo.write(pin_map)
      elif(line_number > lower_skip and line_number <= upper_skip):
        pass
      else: casmo.write(line)
      line_number+=1
    casmo.close()

parent.close()

#####################################################################
#This block calculates the rate at which the mutation rate will increase.
lambda_s = reproduction.calculate_lambda(initial_mutation_rate, target_mutation_rate,number_of_generations)
mutation_rate = initial_mutation_rate

for generation in xrange(number_of_generations):
  if(generation == 0):
  ############################################################################
  #This block of code evaluates the initial population and creates and evaluates the first generation of children.
    casmo_functions.evaluate_bundles(batch_size,generation,population)
    cost_file = open('cost_list.txt','r')
    cost_lines = cost_file.readlines()
    cost_file.close()
    cost_matrix = []
    for line in cost_lines:
      elems = line.strip().split()
      cost_matrix.append(float(elems[0]))
    reproduction.merge_files('cost_list.txt','parent_list.txt')
    lattice_list = reproduction.extract_lattices('parent_list.txt')
    max_cost = -20000            #Determines original best file. Necessary for the tournament function to work correctly.
    count_list = 0
    for cost in cost_matrix:
      if(cost > max_cost):
        max_cost = cost
        current_count = count_list
      count_list+=1
    print 'Max Cost'
    print max_cost
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
    os.system('rm batch_* info.dat* error.dat*')
    lattice_count = 0
    for batch in xrange(number_batches):
      for people in xrange(batch_size):
        (lower_lattice,upper_lattice) = reproduction.decode_rod_lattice(new_lattice_list[lattice_count], input_data.region_map, input_data.rod_list)
        casmo = open('batch_'+str(batch)+'.lower_assembly.'+str(people+1)+'.inp','w')
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
        casmo = open('batch_'+str(batch)+'.upper_assembly.'+str(people+1)+'.inp','w')
        pin_map = metrics.return_pin_map(upper_lattice)
        line_number = 1
        for line in upper_casmo_lines:
          if(line_number == lower_skip):
            casmo.write(pin_map)
          elif(line_number > lower_skip and line_number <= upper_skip):
            pass
          else: casmo.write(line)
          line_number+=1
        casmo.close()
        lattice_count+=1
    mutation_rate = reproduction.update_mutation_rate(lambda_s,mutation_rate) 
    casmo_functions.evaluate_bundles(batch_size,generation,population)
    reproduction.merge_files('cost_list.txt','child_list.txt')
    Number_of_times = 0
  else:
    ###################################################################
    #Second Generation and Later Files
    old_max_cost = max_cost
    max_cost = reproduction.tournament('parent_list.txt','child_list.txt')
    if(max_cost == old_max_cost):
      Number_of_times+=1
    else:
      old_max_cost = max_cost
      Number_of_times = 0
    print 'Number of Times' 
    print Number_of_times 
    if(Number_of_times == 3):
      #########################################################################################
      #SPECIAL PROTOCAL IF MAX FITNESS is not being advanced sufficiently. Replaces child population with
      #only single mutation of the highest fitness solution.       
      metrics_file = open('metrics_file.txt','a')
      metrics_file.write('special_protocal happened\n')     
      metrics_file.close()
      best_lattice = reproduction.special_read_metric_file('metrics_file.txt') 
      for i in xrange(number_batches):
        active_rods = reproduction.return_active_rod_list(best_lattice,input_data.region_map)
        file_exists = os.path.isfile('child_list.txt')
        if(file_exists == True):
          os.remove('child_list.txt')
        for j in xrange(batch_size):
          reproduction.single_mutation(best_lattice, active_rods, input_data.region_map, input_data.rod_list)
        lattice_list = reproduction.extract_lattices('child_list.txt')
        os.system('rm batch_* info-dat* error-dat*')
        for j in xrange(batch_size):
          (lower_lattice,upper_lattice) = reproduction.decode_rod_lattice(lattice_list[j],input_data.region_map, input_data.rod_list)
          casmo = open('batch_0.lower_assembly.'+str(j+1)+'.inp','w')
          pin_map = metrics.return_pin_map(lower_lattice)
#          total_list.write(pin_map+'\n\n')
          line_number = 1
          for line in lower_casmo_lines:
            if(line_number == lower_skip):
              casmo.write(pin_map)
            elif(line_number > lower_skip and line_number <= upper_skip):
              pass
            else: casmo.write(line)
            line_number+=1
          casmo.close()
          casmo = open('batch_0.upper_assembly.'+str(j+1)+'.inp','w')
          pin_map = metrics.return_pin_map(upper_lattice)
          line_number = 1
          for line in upper_casmo_lines:
            if(line_number == lower_skip):
              casmo.write(pin_map)
            elif(line_number > lower_skip and line_number <= upper_skip):
              pass
            else: casmo.write(line)
            line_number+=1
          casmo.close() 
        casmo_functions.special_evaluate_files(batch_size,generation)
        reproduction.merge_files('cost_list.txt','child_list.txt')
        (max_cost, best_lattice) = reproduction.special_tournament(max_cost, best_lattice,'child_list.txt')
        os.system('mv child_list.txt child_list_number_'+str(i)+'.txt')
      child_file = open('child_list.txt','w')
      for i in xrange(number_batches):
        current_file = open('child_list_number_'+str(i)+'.txt','r')
        current_file_lines = current_file.readlines()
        current_file.close()
        
        for line in current_file_lines:
          child_file.write(line)
      child_file.close()

    else:
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
          casmo = open('batch_'+str(batch)+'.lower_assembly.'+str(people+1)+'.inp','w')
          pin_map = metrics.return_pin_map(lower_lattice)
#          total_list.write(pin_map+'\n\n')
          line_number = 1
          for line in lower_casmo_lines:
            if(line_number == lower_skip):
              casmo.write(pin_map)
            elif(line_number > lower_skip and line_number <= upper_skip):
              pass
            else: casmo.write(line)
            line_number+=1
          casmo.close()
          casmo = open('batch_'+str(batch)+'.upper_assembly.'+str(people+1)+'.inp','w')
          pin_map = metrics.return_pin_map(upper_lattice)
#          total_list.write(pin_map+'\n\n')
          line_number = 1
          for line in upper_casmo_lines:
            if(line_number == lower_skip):
              casmo.write(pin_map)
            elif(line_number > lower_skip and line_number <= upper_skip):
              pass
            else: casmo.write(line)
            line_number+=1
          casmo.close()
          lattice_count+=1
      casmo_functions.evaluate_bundles(batch_size,generation,population)
      reproduction.merge_files('cost_list.txt','child_list.txt')
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
    
            
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
       
           
