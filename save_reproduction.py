#reproduction.py
import random
import sys
import os
import numpy
import math
import metrics

#A module for handling all operations related to the reproduction of the current generation of assemblies.
def decode_rod_lattice(lattice,region_map,rod_list):
    lower_lattice = []
    upper_lattice = []
    pin_number = 0
    for i in lattice:
      x = region_map[pin_number]
      temp_one = rod_list[x][i][0]
      temp_two = rod_list[x][i][1]
      lower_lattice.append(temp_one)
      upper_lattice.append(temp_two)
      pin_number+=1
    return(lower_lattice,upper_lattice)

def calculate_lambda(initial_mutation_rate, target_mutation_rate,number_generations):
# A function for calculating the rate at which the mutation rate changes at each generation.
    temp =  (1-target_mutation_rate)/(1-initial_mutation_rate)
    temp = math.log(temp)
    temp = temp/number_generations
    lambda_s = math.exp(temp)
    return lambda_s

def update_mutation_rate(lambda_s,current_mutation_rate):
#A function for calculating the mutation rate for the current generation.
    new_rate =  1 - lambda_s*(1 - current_mutation_rate)
    return new_rate

def method_of_reproduction(parent_list, mutation_rate):
#A function for designating the method of reproduction for the current generation of parents.
   crossover_list = []
   crossover_rod_list = []
   single_mutation_list = []
   single_mutation_rod_list = []
   double_mutation_list = []
   double_mutation_rod_list = []
   what_happened_list = []
   for parent in xrange(len(parent_list)):
     x = random.random()
     if(x <= mutation_rate):
       y = random.random()
       if(y < 0.5):
         single_mutation_list.append(parent_list[parent])
       else:
         double_mutation_list.append(parent_list[parent])
     else:
       crossover_list.append(parent_list[parent])
   remainder = len(crossover_list) % 2
   if(remainder == 1):
     remove_this_assembly = random.randint(0,len(crossover_list)-1)
     single_mutation_list.append(crossover_list[remove_this_assembly])
     crossover_list.remove(crossover_list[remove_this_assembly])
   return (single_mutation_list,double_mutation_list,crossover_list)

def crossover(full_lattice_list, region_map, pin_list):
    remaining_assemblies = full_lattice_list[:]
    number_of_pairs = len(remaining_assemblies)/2
    for foo in xrange(number_of_pairs):
      current_assembly = remaining_assemblies[0][:]
      current_rod_list = return_active_rod_list(current_assembly,region_map)
      mate_lattice_number = 0
      mate_score = 0
      for assembly in range(1,len(remaining_assemblies)):
        matching_rod_count = 0
        current_examine_list = return_active_rod_list(remaining_assemblies[assembly],region_map)
        if(len(current_examine_list) > len(current_rod_list)):
            shorter_list = len(current_rod_list)
        else: shorter_list = len(current_examine_list)
        for rod in xrange(shorter_list):
          if(current_rod_list[rod] == current_examine_list[rod]):
            matching_rod_count+=1
        if(matching_rod_count > mate_score):
          mate_score = matching_rod_count
          mate_lattice_number = assembly
          mate_rod_list =  current_examine_list[:]
      mate_lattice = remaining_assemblies[mate_lattice_number]
      suitable_swap_locations = []
      rod_number = 0
      for rod in xrange(len(current_assembly)):
        if(mate_lattice[rod] == current_assembly[rod]):
          pass
        else:
          suitable_swap_locations.append(rod)
      if(len(suitable_swap_locations) < 4):
        double_mutation(current_assembly,current_rod_list,region_map,pin_list)
        double_mutation(mate_lattice,mate_rod_list,region_map,pin_list)
      else:
        number_swaps = len(suitable_swap_locations)/2
        actual_swap_spots = []
        for i in xrange(number_swaps):
          x = random.choice(suitable_swap_locations)
          actual_swap_spots.append(x)
        new_assembly_one = range(len(current_assembly))
        new_assembly_two = range(len(mate_lattice))
        for i in xrange(len(current_assembly)):
          not_swap_location = True
          for foo in actual_swap_spots:
            if(foo == i):
              not_swap_location = False
          if(not_swap_location == True):
            new_assembly_one[i] = current_assembly[i]
            new_assembly_two[i] = mate_lattice[i]
          else:
            new_assembly_one[i] = mate_lattice[i]
            new_assembly_two[i] = current_assembly[i]
        string_new_assembly_one = convert_to_string(new_assembly_one)
        string_new_assembly_two = convert_to_string(new_assembly_two)
        lattice_one_pin_map = metrics.return_pin_map(string_new_assembly_one)
        lattice_two_pin_map = metrics.return_pin_map(string_new_assembly_two)
        stowage = open('child_list.txt','a')
        stowage.write('Assembly\n')
        stowage.write(lattice_one_pin_map)
        stowage.write('What_Happened:  Pin_Swap_Crossover\n\n')
        stowage.write('Assembly\n')
        stowage.write(lattice_two_pin_map)
        stowage.write('What_Happened:  Pin_Swap_Crossover\n\n')
        stowage.close()
      if(current_assembly in remaining_assemblies):
        remaining_assemblies.remove(current_assembly)
      if(mate_lattice in remaining_assemblies):
        remaining_assemblies.remove(mate_lattice)


def organized_crossover(full_lattice_list, region_map, pin_list):
#Function for organizeing the crossover functions.
    mute_rate = 0.25
    remaining_assemblies = full_lattice_list[:]
    number_of_pairs = len(remaining_assemblies) / 2
#    ideal_crossovers = int(len(full_lattice_list[0])*mutation_rate)
    for foo in xrange(number_of_pairs):
      x = random.random()
      if(x <  0.80):                                        #if x is less than 25% the assembly will be designated for switching over rod types. Otherwise it will trade rod positions.
        current_assembly = remaining_assemblies[0][:]
        current_rod_list = return_active_rod_list(current_assembly,region_map)
        mate_lattice_number = 0
        mate_score = 0
        for assembly in range(1,len(remaining_assemblies)):
          matching_rod_count = 0
          current_examine_list = return_active_rod_list(remaining_assemblies[assembly],region_map)
          if(len(current_examine_list) > len(current_rod_list)):
            shorter_list = len(current_rod_list)
          else: shorter_list = len(current_examine_list)
          for rod in xrange(shorter_list):
            if(current_rod_list[rod] == current_examine_list[rod]):
              matching_rod_count+=1
          if(matching_rod_count > mate_score):
            mate_score = matching_rod_count
            mate_lattice_number = assembly
            mate_rod_list =  current_examine_list[:]
        mate_lattice = remaining_assemblies[mate_lattice_number]
        rod_swap_crossover(current_assembly, mate_lattice, mate_rod_list, current_rod_list, region_map)
        if(current_assembly in remaining_assemblies):
          remaining_assemblies.remove(current_assembly)
        if(mate_lattice in remaining_assemblies):
          remaining_assemblies.remove(mate_lattice)
      else:
        current_assembly = remaining_assemblies[0][:]
	current_rod_list = return_active_rod_list(current_assembly,region_map)
	mate_lattice_number = 0
	mate_score = 0
	for assembly in range(1,len(remaining_assemblies)): 
	  matching_rod_count = 0
	  current_rod = 0
	  current_examine_list = return_active_rod_list(remaining_assemblies[assembly],region_map)
          if(len(current_examine_list) > len(current_rod_list)):
            shorter_list = len(current_rod_list)
          else: shorter_list = len(current_examine_list)
          for rod in xrange(shorter_list):
            if(current_rod_list[rod] == current_examine_list[rod]):
	      matching_rod_count+=1
	      current_rod+=1
	  if(matching_rod_count > mate_score):
            mate_score = matching_rod_count
            mate_lattice_number = assembly
            mate_rod_list = current_examine_list
	mate_lattice = remaining_assemblies[mate_lattice_number]
        if(mate_score < 6):
	  rod_swap_crossover(current_assembly, mate_lattice,mate_rod_list, current_rod_list,region_map)
	else: 
	  pin_swap_crossover(current_assembly, mate_lattice, current_rod_list, mate_rod_list)
	if(current_assembly in remaining_assemblies):
          remaining_assemblies.remove(current_assembly)
        if(mate_lattice in remaining_assemblies):
          remaining_assemblies.remove(mate_lattice)
	  
		  
def rod_swap_crossover(assembly_one_lattice, assembly_two_lattice, assembly_two_rod_list, assembly_one_rod_list,region_map):
#Swaps a rod between the two assemblies. It doesn't account to make sure that the rod is not in common with the current assembly.
    chromosome_one = random.choice(assembly_one_rod_list)
    chromosome_two = chromosome_one
    while(chromosome_one == chromosome_two):
      chromosome_two = random.choice(assembly_two_rod_list)
    rod_count = 0
    for rod in region_map:
      if(rod == 1):
        if(assembly_one_lattice[rod_count] == chromosome_one):
          assembly_one_lattice[rod_count] = chromosome_two
        if(assembly_two_lattice[rod_count] == chromosome_two):
          assembly_two_lattice[rod_count] = chromosome_one
      rod_count+=1
    assembly_one_rod_list.remove(chromosome_one)
    assembly_one_rod_list.append(chromosome_two)
    assembly_two_rod_list.remove(chromosome_two)
    assembly_two_rod_list.append(chromosome_one)
    string_assembly_one_lattice = convert_to_string(assembly_one_lattice)
    string_assembly_two_lattice = convert_to_string(assembly_two_lattice)
    lattice_one_pin_map = metrics.return_pin_map(string_assembly_one_lattice)
    lattice_two_pin_map = metrics.return_pin_map(string_assembly_two_lattice) 
    stowage = open('child_list.txt','a')
    stowage.write('Assembly\n')
    stowage.write(lattice_one_pin_map)
    stowage.write('What_Happened:  Rod_Swap_Crossover\n\n')
    stowage.write('Assembly\n')
    stowage.write(lattice_two_pin_map)
    stowage.write('What_Happened:  Rod_Swap_Crossover\n\n')
    stowage.close()


def pin_swap_crossover(current_assembly, mate_lattice, current_rod_list, mate_rod_list):
#Swaps Rod Locations between two assemblies. Only rods that already exist within the bundle may be switched. 
    initial_lattice_rods = [0]
    for rod in current_assembly:
      doesnt_exist = True
      for foo in initial_lattice_rods:
        if(rod == foo):
          doesnt_exist = False
      if(doesnt_exist == True):
        initial_lattice_rods.append(rod)
    in_common_rod_list = [0]
    for rod in mate_lattice:
      for foo in initial_lattice_rods:
        if(rod == foo):
          doesnt_exist = True
          for thing in in_common_rod_list:
            if(thing == rod):
              doesnt_exist = False
          if(doesnt_exist == True):
            in_common_rod_list.append(rod)
         
    rod_number = 0
    suitable_swap_locations = []
    for rod in current_assembly:
      for foo in in_common_rod_list:
        if(rod == foo):
          for footoo in in_common_rod_list:
            if(mate_lattice[rod_number] == footoo):
              if(mate_lattice[rod_number] == rod):
                pass
              else: suitable_swap_locations.append(rod_number)
      rod_number+=1          
    number_swaps = len(suitable_swap_locations)/2
    actual_swap_spots = []
    for i in xrange(number_swaps):
      x = random.choice(suitable_swap_locations)
      actual_swap_spots.append(x)
    new_assembly_one = range(len(current_assembly))
    new_assembly_two = range(len(mate_lattice))
    for i in xrange(len(current_assembly)):
      not_swap_location = True
      for foo in actual_swap_spots:
        if(foo == i):
          not_swap_location = False
      if(not_swap_location == True):
        new_assembly_one[i] = current_assembly[i]
        new_assembly_two[i] = mate_lattice[i]
      else:
        new_assembly_one[i] = mate_lattice[i]
        new_assembly_two[i] = current_assembly[i]            
    lattice_one_pin_map = metrics.return_pin_map(new_assembly_one)
    lattice_two_pin_map = metrics.return_pin_map(new_assembly_two)
    assembly_one_rod_list = []
    assembly_two_rod_list = []
    for rod in new_assembly_one:
      if(rod == '0'):
        pass
      else:
        rod_not_used = True
        for foo in assembly_one_rod_list:
          if(foo == rod):
            rod_not_used = False
        if(rod_not_used == True):
          assembly_one_rod_list.append(rod)
    for rod in new_assembly_two:
      if(rod == '0'):
        pass
      else:
        rod_not_used = True
        for foo in assembly_two_rod_list:
          if(foo == rod):
            rod_not_used = False
        if(rod_not_used == True):
          assembly_two_rod_list.append(rod)
    stowage = open('child_list.txt','a')
    stowage.write('Assembly\n')
    stowage.write(lattice_one_pin_map)
    stowage.write('What_Happened:  Pin_Swap_Crossover\n\n')
    stowage.write('Assembly\n')
    stowage.write(lattice_two_pin_map)
    stowage.write('What_Happened:  Pin_Swap_Crossover\n\n')
    stowage.close()
       
def single_mutation(lattice, rod_list, region_map, pin_list):
#A function to alter a single rod location within the lattice. Does not introduce new rod types to the lattice.
#I don't know why I didn't make this one so that it accepts the lattice. list. I think it would be
#best to make an organized mutation function similar to what I did for crossover.
    suitable_swap_locations = []
    for rod in xrange(len(region_map)):
      if(region_map[rod] == 1): suitable_swap_locations.append(rod)    
    x = random.choice(suitable_swap_locations)
    original_pin = lattice[x]
    foo = original_pin
    while(foo == original_pin):  
      foo = random.randint(0,len(pin_list[1])-1)
    new_lattice = range(len(lattice))
    for i in xrange(len(lattice)):
      if(i == x): new_lattice[i] = str(foo)
      else: new_lattice[i] = lattice[i]
    string_new_lattice = convert_to_string(new_lattice)
    pin_map = metrics.return_pin_map(string_new_lattice)
    stowage = open('child_list.txt','a')
    stowage.write('Assembly\n')
    stowage.write(pin_map)
    stowage.write('What_Happened:  Single_Mutation\n\n')
    stowage.close()
	

def double_mutation(lattice, rod_list,region_map, pin_list):         
# A function to alter two rod locations within the lattice. Does not introduce any new rod types.
    suitable_swap_locations = []
    for rod in xrange(len(region_map)):
      if(region_map[rod] == 1): suitable_swap_locations.append(rod)
    x1 = random.choice(suitable_swap_locations)
    x2 = random.choice(suitable_swap_locations)
    original_pin_one = lattice[x1]
    original_pin_two = lattice[x2]
    foo_one = original_pin_one
    foo_two = original_pin_two
    while(foo_one == original_pin_one):
      foo_one = random.randint(0,len(pin_list[1])-1)
    while(foo_two == original_pin_two):
      foo_two = random.randint(0,len(pin_list[1])-1)
    new_lattice = range(len(lattice))
    for i in xrange(len(lattice)):
      if(i == x1): new_lattice[i] = str(foo_one)
      elif(i == x2): new_lattice[i] = str(foo_two)
      else: new_lattice[i] = lattice[i]
    string_new_lattice = convert_to_string(new_lattice)
    pin_map = metrics.return_pin_map(string_new_lattice)
    stowage = open('child_list.txt','a')
    stowage.write('Assembly\n')
    stowage.write(pin_map)
    stowage.write('What_Happened:  Double_Mutation\n\n')
    stowage.close()

def tournament(previous_generation, current_generation):
#A function for determining which assemblies survive to breed in the next generation. 
#Two assemblies are randomly drawn from the total list of assemblies. 
#The assembly with the highest cost survives to the next generation while the lower 
#cost assembly is killed.
#previous_generation is the name of the previous generation survivor list.
    parent_file = open(previous_generation, 'r')
    parent_lines = parent_file.readlines()
    parent_file.close()
    child_file = open(current_generation, 'r')
    child_lines = child_file.readlines()
    child_file.close()
    lattice_list = []
    lattice_count = 0
    cost_list = [] 
    rod_list = []
    what_happened_list = []
    line_count = 1000
    for line in parent_lines:  
      elems = line.strip().split()
      if(len(elems) > 0):
        if(elems[0] == 'Assembly'):
          line_count = 0
          lattice_count+=1
          temp_lattice = []
        if(line_count > 0 and line_count < 11):
          for el in elems:
            temp_lattice.append(el)
        elif(line_count == 11):
          lattice_list.append(temp_lattice)
          what_happened_list.append(elems[1])
        elif(line_count == 12):
          cost_list.append(float(elems[1]))
      line_count+=1   
       
    line_count = 1000
    for line in child_lines:
      elems = line.strip().split()
      if(len(elems) > 0):
        if(elems[0] == 'Assembly'):
          line_count = 0
          lattice_count+=1
          temp_lattice = []
        if(line_count > 0 and line_count < 11):
          for el in elems:
            temp_lattice.append(el)
        elif(line_count == 11):
          lattice_list.append(temp_lattice)
          what_happened_list.append(elems[1])
        elif(line_count == 12):
          cost_list.append(float(elems[1]))
      line_count+=1   

    average_cost = metrics.calculate_average_cost(cost_list)
    variance = metrics.calculate_cost_variance(cost_list,average_cost)
    (min_cost, max_cost,best_lattice,worst_lattice,best_what_happened,worst_what_happened) = metrics.return_max_and_min(cost_list,lattice_list,what_happened_list)
    pin_average = metrics.return_average_pins_used(lattice_list)
    metric_file = open('metrics_file.txt','a')


    metric_file.write('Average Lattice Cost:   '+str(average_cost)+'\n')
    metric_file.write('Variance in lattice score:    '+str(variance)+'\n')
    metric_file.write('Minimum lattice score: '+str(min_cost))
    metric_file.write('  Maximum lattice score:  '+str(max_cost)+'\n')
    metric_file.write('Average number of pins per assembly:  '+str(pin_average))
    metric_file.write('Highest scoring Pin Lattice \n'+best_lattice)
    metric_file.write('Worst Scoring Pin Lattice \n'+worst_lattice+'\n\n\n')

    print('Average Lattice Cost:   '+str(average_cost)+'\n')
    print('Variance in lattice score:    '+str(variance)+'\n')
    print('Minimum lattice score: '+str(min_cost))
    print('  Maximum lattice score:  '+str(max_cost)+'\n')
    print('Average number of pins per assembly:  '+str(pin_average))
    print('Highest scoring Pin Lattice \n'+best_lattice)
    print('Worst Scoring Pin Lattice \n'+worst_lattice+'\n\n\n')

    metric_file.close()
    
    new_parent = open('parent_list.txt','w')
    number_of_rounds = lattice_count / 2
    for i in xrange(number_of_rounds):
      foo_one = random.randint(0,len(lattice_list)-1)
      foo_two = foo_one
      while(foo_one == foo_two):
        foo_two = random.randint(0,len(lattice_list)-1)
      contestant_one_lattice = lattice_list[foo_one]
      contestant_two_lattice = lattice_list[foo_two]
      contestant_one_cost = cost_list[foo_one]
      contestant_two_cost = cost_list[foo_two]
      contestant_one_what_happened = what_happened_list[foo_one]
      contestant_two_what_happened = what_happened_list[foo_two]

      if(contestant_one_cost > contestant_two_cost):
        new_parent.write('Assembly\n')
        pin_map = metrics.return_pin_map(contestant_one_lattice)
        new_parent.write(pin_map)
        new_parent.write('What_Happened: '+contestant_one_what_happened+'\n')
        new_parent.write('Lattice_Cost:  '+str(contestant_one_cost)+'\n\n')
      else:  
        new_parent.write('Assembly\n')
        pin_map = metrics.return_pin_map(contestant_two_lattice)
        new_parent.write(pin_map)
        new_parent.write('What_Happened: '+contestant_two_what_happened+'\n')
        new_parent.write('Lattice_Cost:  '+str(contestant_two_cost)+'\n\n')
      lattice_list.remove(contestant_one_lattice)
      lattice_list.remove(contestant_two_lattice)
      cost_list.remove(contestant_one_cost)
      cost_list.remove(contestant_two_cost)
      what_happened_list.remove(contestant_one_what_happened)
      what_happened_list.remove(contestant_two_what_happened)


def merge_files(cost_file, assembly_file):
#A function to add the cost list to the assembly file  
    assembly = open(assembly_file,'r')
    assembly_lines = assembly.readlines()
    assembly.close()
    cost = open(cost_file,'r')
    cost_lines = cost.readlines()
    cost.close()
    line_count = 1000
    os.remove(assembly_file)
    assembly = open(assembly_file,'w')
    cost_list = []
    for line in cost_lines:
      cost_list.append(line)
    assembly_count = 0
    for line in assembly_lines:
      elems = line.strip().split()
      if(len(elems) > 0):
        if(elems[0] == 'Assembly'):
          line_count = 0
      if(line_count == 12):
        assembly.write('Assembly_Cost:  '+cost_list[assembly_count])
        assembly_count+=1
      assembly.write(line)
      line_count+=1
    assembly.close()   
       
def extract_lattices(Rod_File):
    document = open(Rod_File,'r')
    document_lines = document.readlines()       
    document.close()   
    line_count = 1000
    lattice_list = []
    lattice_count = 0
    for line in document_lines:   
      elems = line.strip().split()
      if(len(elems) > 0):
        if(elems[0] == 'Assembly'):
          line_count = 0
          lattice_count+=1
          temp_lattice = []
          elemcount = 0
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
              
#            print true_werd
            elemcount+=1
#            print 'Elemcount is '+str(elemcount)
            temp_lattice.append(int(true_werd))
      if(line_count == 12):
        lattice_list.append(temp_lattice)
      line_count+=1
    return lattice_list   
       
       
       
def return_active_rod_list(lattice,region_map):
    active_rod_list = []
    rod_count = 0
    for rod in region_map:
      if(rod == '0'):
        pass
      else:
        not_used = True
	check_rod = lattice[rod_count]
        for foo in active_rod_list:
          if(foo == check_rod):
            not_used = False
        if(not_used == True):
          active_rod_list.append(check_rod)		
      rod_count+=1
    return active_rod_list

def convert_to_string(lattice):
    string_lattice = []
    for elem in lattice:
      rod = str(elem)
      string_lattice.append(rod)
    return string_lattice	
       
def roulette(previous_generation, current_generation):

#A function for determining which assemblies survive to breed in the next generation.
#Uses a roulette method to select the survivors. All assemblies are drawn into single rank list. Then
#ranks are randomly picked until the population list is full.
#previous_generation is the name of the previous generation survivor list.
       
#rent_file = open(previous_generation, 'r')
    parent_lines = parent_file.readlines()
    parent_file.close()
    child_file = open(current_generation, 'r')
    child_lines = child_file.readlines()
    child_file.close()
    lattice_list = []
    lattice_count = 0
    cost_list = []
    rod_list = []
    what_happened_list = []
    line_count = 1000
    for line in parent_lines:
      elems = line.strip().split()
      if(len(elems) > 0):
        if(elems[0] == 'Assembly'):
          line_count = 0
          lattice_count+=1
          temp_lattice = []
        if(line_count > 0 and line_count < 11):
          for el in elems:
            temp_lattice.append(el)
        elif(line_count == 11):
          lattice_list.append(temp_lattice)
          what_happened_list.append(elems[1])
        elif(line_count == 12):
          cost_list.append(float(elems[1]))
      line_count+=1

    line_count = 1000
    for line in child_lines:
      elems = line.strip().split()
      if(len(elems) > 0):
        if(elems[0] == 'Assembly'):
          line_count = 0
          lattice_count+=1
          temp_lattice = []
        if(line_count > 0 and line_count < 11):
          for el in elems:
            temp_lattice.append(el)
        elif(line_count == 11):
          lattice_list.append(temp_lattice)
          what_happened_list.append(elems[1])
        elif(line_count == 12):
          cost_list.append(float(elems[1]))
      line_count+=1

       
       
    average_cost = metrics.calculate_average_cost(cost_list)
    variance = metrics.calculate_cost_variance(cost_list,average_cost)
    (min_cost, max_cost,best_lattice,worst_lattice,best_what_happened,worst_what_happened) = metrics.return_max_and_min(cost_list,lattice_list,what_happened_list)
    pin_average = metrics.return_average_pins_used(lattice_list)
    metric_file = open('metrics_file.txt','a')


    metric_file.write('Average Lattice Cost:   '+str(average_cost)+'\n')
    metric_file.write('Variance in lattice score:    '+str(variance)+'\n')
    metric_file.write('Minimum lattice score: '+str(min_cost))
    metric_file.write('  Maximum lattice score:  '+str(max_cost)+'\n')
    metric_file.write('Average number of pins per assembly:  '+str(pin_average))
    metric_file.write('Highest scoring Pin Lattice \n'+best_lattice)
    metric_file.write('Worst Scoring Pin Lattice \n'+worst_lattice+'\n\n\n')

    print('Average Lattice Cost:   '+str(average_cost)+'\n')
    print('Variance in lattice score:    '+str(variance)+'\n')
    print('Minimum lattice score: '+str(min_cost))
    print('  Maximum lattice score:  '+str(max_cost)+'\n')
    print('Average number of pins per assembly:  '+str(pin_average))
    print('Highest scoring Pin Lattice \n'+best_lattice)
    print('Worst Scoring Pin Lattice \n'+worst_lattice+'\n\n\n')

    metric_file.close()

    new_parent = open('parent_list.txt','w')
    number_of_rounds = lattice_count / 2
    rank_list = 0
    cost_sum = 0 
    for cost in cost_list:
      cost_sum+= cost
    
    rank_sum = 0
    for cost in cost_list:
      temp_rank = (cost/cost_sum) + rank_sum
      rank_list.append(temp_rank)
      rank_sum = temp_rank
       
    for i in xrange(number_of_rounds):
      temp = random.random()
      match_cost_not_found = True
      assembly_count = 0
      for rank in rank_list:
        if(match_cost_not_found == True):
          if(rank > temp):
            assembly_number = assembly_count
            match_cost_not_found = False   
        assembly_count+=1
       
      new_parent.write('Assembly\n')
      pin_map = metrics.return_pin_map(lattice_list[assembly_number])
      new_parent.write(pin_map)
      new_parent.write('What_Happened: '+what_happened_list[assembly_number]+'\n')
      new_parent.write('Lattice_Cost:  '+str(cost_list[assembly_number])+'\n\n')
      new_parent.close() 
       
       
       
       
       
       
       
       
       
       
       
       
              
       
       
       
       
       
       
         
