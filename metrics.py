#metrics.py
import sys 
import os

def calculate_average_cost(cost_matrix):
#A function for calculating the average cost of each generation. 
   number_of_assemblies = 0
   total_cost = 0
   for assembly in cost_matrix:
      total_cost+=assembly
      number_of_assemblies+=1
   average_cost = total_cost/number_of_assemblies
   return average_cost
   
def calculate_cost_variance(cost_matrix, average_cost):
#A function for calculating the cost variance in the current generation.
    number_of_assemblies = 0
    variance_sum = 0
    for assembly in cost_matrix:
	temp = assembly - average_cost
	temp = temp**2
	variance_sum+=temp
	number_of_assemblies+=1
    stuff = variance_sum/number_of_assemblies
    variance = stuff**0.5
    return variance
	
def return_max_and_min(cost_matrix, lattice_matrix,what_happened):
#A function for returning the maximum and minimum scores in the current generation
    max_cost = 0
    min_cost = 1000000
    assembly_count = 0
    for assembly in cost_matrix:
	  if(assembly > max_cost):
            max_cost = assembly
            best_lattice = return_pin_map(lattice_matrix[assembly_count])
            best_what_happened = what_happened[assembly_count]
#            print 'new_max_cost'
#            print max_cost
	  if(assembly < min_cost):
            min_cost = assembly
            worst_lattice = return_pin_map(lattice_matrix[assembly_count])
            worst_what_happened = what_happened[assembly_count]
#            print 'new worst cost'
#            print min_cost
          assembly_count+=1
    return (min_cost, max_cost, best_lattice, worst_lattice,best_what_happened,worst_what_happened)
	  
def return_average_pins_used(lattice_matrix):	  
    list_of_pin_amounts = []
    for lattice in lattice_matrix:
      list_of_pins_used = [0]
      for pin in lattice:
	pin_not_used = True
	for elem in list_of_pins_used:
	  if(elem == pin): pin_not_used = False
	if(pin_not_used == True): list_of_pins_used.append(pin)
      list_of_pin_amounts.append(len(list_of_pins_used))
    pin_sum = 0
    number_of_assemblies = 0
    for number in list_of_pin_amounts:	  
		pin_sum+=number
		number_of_assemblies+=1
    pin_average = pin_sum/number_of_assemblies
    return pin_average
	
def return_pin_map(lattice):	
    row_number = 1
    pin_number = 0
    pin_map = ''
    for pin in lattice:
      pin_map = pin_map+ pin.ljust(3)
      pin_number+=1
      if(pin_number == row_number):
        pin_map = pin_map + '\n'
        pin_number = 0
        row_number+=1
    return pin_map

def are_there_multiple_bests(max_cost,cost_list, lattice_list):
    other_good_solutions = [] 
    assembly_count = 0
    for lattice in lattice_list:
      if(max_cost == cost_list[assembly_count]):
        row_number = 1
        pin_number = 0
        pin_map = ''
        for pin in lattice:
          pin_map = pin_map + pin.ljust(3)
          pin_number+=1
          if(pin_number == row_number):
            pin_map = pin_map + '\n'
            pin_number = 0
            row_number+=1
        pin_map = pin_map + '\n\n'
        other_good_solutions.append(pin_map)
      assembly_count+=1
    return other_good_solutions               
               
def btf_and_kinf_values(cost):
    total_file = open('total_track_file.txt','r')
    file_lines = total_file.readlines()
    total_file.close()
    for line in file_lines:    
      elems = line.strip.split()
      if(elems[0] == cost):
        btf = elems[2]
        kinf = elems[1]  
    return (btf,kinf)    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
