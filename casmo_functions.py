#casmo_functions.py
#A method for organizing all the functions related to the operation of Casmo.
import sys
import os
import os.path
import numpy as np
import random
import time
import math
import reproduction
import metrics
import fuel_assembly
from subprocess import call

def pin_reader(lines, lower_skip, upper_skip):
#A function for reading the pin lattices from the casmo input file. 
    line_count = 1
    pin_list = []
    for line in lines:
      if(line_count > lower_skip and line_count <= upper_skip):
        elems = line.strip().split()
        for elem in elems:
          if(elem == 'LFU'):
            pass
          else:
            pin_list.append(elem)
      line_count+=1
    return pin_list

def check_job_status(job_name):
#Checks to see if the current generation of jobs has completed or not. i
#Returns false if job has not completed. Returns true if job has completed.
    os.system('qstat &> job_list.txt')
    job_file = open('job_list.txt','r')
#    os.system('qstat -u bdander3')
    job_lines = job_file.readlines()
    job_file.close()
    job_status = False
    for line in job_lines:
      elem = line.strip().split()
#      print elem[1]
      if(elem[1] == job_name):
        if(elem[4] == 'R' or elem[4] == 'Q'):
          job_status = True
#        print 'pancakes'
#    print job_status
    if(job_status == True):
#      print 'Job is still running'
      return False
    else:
#      print 'Job is Finished'
      return True

def evaluate_job_files(generation,population,batch_size):
#Evaluates casmo input files in batches of twenty in order to avoid issues with the job scheduler.
#After the first batch of input files, the previous batch of input files are evaluated while
#waiting for the current generation of input files to finish.
    cost_list = []
    job_name = 'gen_'+str(generation)
    number_batch_submits = population/batch_size
    last_submit = population % batch_size
    file_exists = os.path.isfile('cost_list.txt')
    if(file_exists == True):
      os.remove('cost_list.txt')
    cost_list = open('cost_list.txt','w')
    for i in xrange(number_full_submits):
      #Begin making submission script to evaluate Casmo input files.
      first_file = batch_size*i + 1
      last_file = batch_size*i + batch_size
      if(i==0): evaluate_batch = False
      else: evaluate_batch = True
      submit_job_file(generation,first_file,last_file)
      #Casmo files have now been submitted to job scheduler         
      if(evaluate_batch == True):
        begin_file = batch_size*(i-1) + 1
        end_file = batch_size*(i-1) + batch_size+1
        for j in range(begin_file,end_file):
          file_exists = os.path.isfile('upper_assembly.'+str(j)+'.out')
          if(file_exists == True): 
            casmo = open('upper_assembly.'+str(j)+'.out','r')
            output_lines = casmo.readlines()
            casmo.close()
            k_inf = fuel_assembly.search_for_k_inf(output_lines)
            FdH = fuel_assembly.search_for_peak_power(output_lines)
#            average_burnup = [0.0,0.1,0.5]
#            max_burnup = fuel_assembly.search_maximum_burnup(output_lines)
            temp_cost = fuel_assembly.calculate_cost(k_inf,FdH)
            cost_list.write(str(temp_cost)+'\n')
          else:
            start = time.clock()
            finish = time.clock()
            while(finish - start < 10):
              finish = time.clock()
            file_exists = os.path.isfile('upper_assembly.'+str(j)+'.out')
            if(file_exists == True):
              casmo = open('assembly.'+str(j)+'.out','r')
              output_lines = casmo.readlines()
              casmo.close()
              k_inf = fuel_assembly.search_for_k_inf(output_lines)
              FdH = fuel_assembly.search_for_peak_power(output_lines)
              average_burnup = [0.0,0.1,0.5]
              max_burnup = fuel_assembly.search_maximum_burnup(output_lines)
              temp_cost = fuel_assembly.calculate_cost(k_inf, FdH)
              cost_list.write(str(temp_cost)+'\n')
            else: cost_list.write('0\n')  
      else: pass         
      #Begin wait for the current batch of files to finish
      job_finished = False
      start = time.clock()
      while(job_finished == False):
        finish = time.clock()
        if(finish-start>30):  #Checks every three seconds to see if the current batch
          job_finished = check_job_status(job_name) #of input files has finished.
          start = time.clock()
      #End of wait. Job has finished. Back to top of loop to start new batch.
      start = time.clock()
      finish = time.clock()
      while(finish-start<10):
        finish = time.clock()
    if(last_submit == 0): 
      begin_file = (number_full_submits-1)*batch_size + 1
      end_file = number_full_submits*batch_size + 1
      for j in range(begin_file,end_file):
        casmo = open('upper_assembly.'+str(j)+'.out','r')
        output_lines = casmo.readlines()
        casmo.close()
        k_inf = fuel_assembly.search_for_k_inf(output_lines)
        FdH = fuel_assembly.search_for_peak_power(output_lines)
#        average_burnup = [0.0,0.1,0.5]
#        max_burnup = fuel_assembly.search_maximum_burnup(output_lines)
        temp_cost = fuel_assembly.calculate_cost(k_inf, FdH)
        cost_list.write(str(temp_cost)+'\n')
    else:
      first_file = number_full_submits*batch_size+1
      submit_job_file(generation,first_file,population)
      #final batch of input files submitted.
      #Begin evaulating N-1 batch of input files.
      begin_file = (number_full_submits-1)*batch_size + 1
      end_file = number_full_submits*batch_size + 1
      for j in range(begin_file,end_file):
        casmo = open('upper_assembly.'+str(j)+'.out','r')
        output_lines = casmo.readlines()
        casmo.close()
        k_inf = fuel_assembly.search_for_k_inf(output_lines)
        FdH = fuel_assembly.search_for_peak_power(output_lines)
#        average_burnup = [0.0,0.1,0.5]
#        max_burnup = fuel_assembly.search_maximum_burnup(output_lines)
        temp_cost = fuel_assembly.calculate_cost(k_inf, FdH)
        cost_list.write(str(temp_cost)+'\n')
      job_finished = False
      start = time.clock()
      while(job_finished == False):
        finish = time.clock()
        if(finish-start>3):  #Checks every three seconds to see if the current batch
          job_finished = check_job_status(job_name) #of input files has finished.
          start = time.clock()
      begin_file = number_full_submits*batch_size+1
      for j in range(begin_file,population):
        casmo = open('upper_assembly.'+str(j)+'.out','r')
        output_lines = casmo.readlines()
        casmo.close()
        k_inf = fuel_assembly.search_for_k_inf(output_lines)
        FdH = fuel_assembly.search_for_peak_power(output_lines)
#        average_burnup = [0.0,0.1,0.5]
#        max_burnup = fuel_assembly.search_maximum_burnup(output_lines)
        temp_cost = fuel_assembly.calculate_cost(k_inf, FdH)
        cost_list.write(str(temp_cost)+'\n')
      cost_list.close()   
            
def submit_job_file(generation,first_batch,batch_size,final_batch):
#A function to write and submit jobs to the cluster. 
    script_name = 'sub_file'
    file_exists = os.path.isfile(script_name)
    if(file_exists == True):
      os.remove(script_name)
    pwd = os.getcwd()
    script = open(script_name,'w')
    script.write('#! /bin/sh\n')
    script.write('#\n')
    script.write('#PBS -N Mustang_'+str(generation)+'\n')
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
    script.write('casmo4e -r batch_'+str(first_batch)+'.lower_assembly.$PBS_ARRAYID.inp\n\n')
    script.write('casmo4e -r batch_'+str(first_batch)+'.lower_top.$PBS_ARRAYID.inp\n\n')
    script.write('casmo4e -r batch_'+str(first_batch)+'.upper_assembly.$PBS_ARRAYID.inp\n\n')
    script.write('casmo4e -r batch_'+str(first_batch)+'.upper_top.$PBS_ARRAYID.inp\n\n')
#    if(generation == final_generation-1):
#      script.write('python next_generation.py\n\n')
#      script.write("ssh rdfmg 'cd "+pwd+"; qsub final_submission\n\n'")
#    else:
#      script.write('python next_generation.py\n\n')
#      script.write("ssh rdfmg 'cd "+pwd+"; qsub sub_file'")
#    script.close()
    

         
def evaluate_bundles(batch_size, generation, population):
#Function to submit 2D lattice designs and evaluate the lattices as a 3 Dimensional fuel bundle
#Cost is based on K_inf and BTF calculation
    number_of_generations = 30	
    number_batches = population/batch_size
    number_jobs = 2
    jobs_first_submit = int(number_batches*0.75)
    for i in xrange(number_batches):
      if(i > 0):
        submit_job_file(generation,i,batch_size,number_batches)
        pwd = os.getcwd()
        os.system("ssh rdfmg 'cd "+pwd+"; qsub sub_file'")
        job_name = 'Mustang_'+str(generation)
        start = time.clock()
        finish = time.clock()
        while(finish-start < 3):
          finish = time.clock()

        for k in xrange(batch_size):
          lower_lattice_file = open('batch_'+str(i-1)+'.lower_assembly.'+str(k+1)+'.out','r')
          lower_lattice_lines = lower_lattice_file.readlines()
          lower_lattice_file.close()

          lower_top_file = open('batch_'+str(i-1)+'.lower_top.'+str(k+1)+'.out','r')
          lower_top_lines = lower_top_file.readlines()
          lower_top_file.close()

          upper_lattice_file = open('batch_'+str(i-1)+'.upper_assembly.'+str(k+1)+'.out','r')
          upper_lattice_lines = upper_lattice_file.readlines()
          upper_lattice_file.close()  	
  	  
          upper_top_file = open('batch_'+str(i-1)+'.upper_top.'+str(k+1)+'.out','r')
          upper_top_lines = upper_top_file.readlines()
          upper_top_file.close()

    	  kinf_two = fuel_assembly.search_for_k_inf(lower_lattice_lines)
  	  kinf_three = fuel_assembly.search_for_k_inf(lower_top_lines)
          kinf_four = fuel_assembly.search_for_k_inf(upper_lattice_lines)
          kinf_five = fuel_assembly.search_for_k_inf(upper_top_lines)

          power_two = fuel_assembly.search_power_distributions(lower_lattice_lines)
          power_three = fuel_assembly.search_power_distributions(lower_top_lines)
          power_four = fuel_assembly.search_power_distributions(upper_lattice_lines)
          power_five = fuel_assembly.search_power_distributions(upper_top_lines)

          average_kinf_list = fuel_assembly.average_kinf_values_over_burnup(kinf_one, kinf_two, kinf_three, kinf_four, kinf_five, kinf_six)
          average_kinf = fuel_assembly.average_kinf_value(average_kinf_list)
          btf_list = fuel_assembly.calculate_btf(average_kinf_list, power_one, power_two, power_three, power_four, power_five, power_six)
          score = fuel_assembly.calculate_bundle_cost(average_kinf,btf_list)
          temp_string_one = str(score)
          #average_btf = fuel_assembly.average_btf_value(btf_list)
          temp_string_two = str(btf_list)
          temp_string_three = str(average_kinf)
  	  cost_file.write(temp_string_one+'\n')
#          print 'here'
#          print temp_string_two
#          print temp_string_one
          total_track_file.write(temp_string_one.ljust(20) + temp_string_two.ljust(20) + temp_string_three.ljust(20)+'\n')
      else:
        job_name = 'Mustang_'+str(generation)
        submit_job_file(generation,0,batch_size,jobs_first_submit)
        pwd = os.getcwd()
        os.system("ssh rdfmg 'cd "+pwd+"; qsub sub_file'")
        bottom_file = open('bottom_lattice.out','r')
        bottom_lines = bottom_file.readlines()
        bottom_file.close()
    
        top_file = open('top_lattice.out','r')
        top_lines = top_file.readlines()
        top_file.close()
    
        cost_file = open('cost_list.txt','w')
        kinf_one = fuel_assembly.search_for_k_inf(bottom_lines)
        kinf_six = fuel_assembly.search_for_k_inf(top_lines)
        power_one = fuel_assembly.search_power_distributions(bottom_lines)
        power_six = fuel_assembly.search_power_distributions(top_lines)

        for j in xrange(number_batches):
          for k in xrange(batch_size):
            write_restart_file(j,k+1)
        
        total_track_file = open('total_track_file.txt','a')
        start = time.clock()
        finish = time.clock()
        while(finish - start < 5):
          finish = time.clock()

      job_finished = check_job_status(job_name)
      start = time.clock()
      while(job_finished == False):
        finish = time.clock()
        if(finish-start>5):  #Checks every three seconds to see if the current batch
          job_finished = check_job_status(job_name) #of input files has finished.
          start = time.clock()   
    start = time.clock()
    finish = time.clock()
    while(finish-start < 10):
      finish = time.clock()
    for j in xrange(batch_size):
      
        lower_lattice_file = open('batch_'+str(number_batches-1)+'.lower_assembly.'+str(j+1)+'.out','r')
        lower_lattice_lines = lower_lattice_file.readlines()
        lower_lattice_file.close()

        lower_top_file = open('batch_'+str(number_batches-1)+'.lower_top.'+str(j+1)+'.out','r')
        lower_top_lines = lower_top_file.readlines()
        lower_top_file.close()

        upper_lattice_file = open('batch_'+str(number_batches-1)+'.upper_assembly.'+str(j+1)+'.out','r')
        upper_lattice_lines = upper_lattice_file.readlines()
        upper_lattice_file.close()

        upper_top_file = open('batch_'+str(number_batches-1)+'.upper_top.'+str(j+1)+'.out','r')
        upper_top_lines = upper_top_file.readlines()
        upper_top_file.close()

        kinf_two = fuel_assembly.search_for_k_inf(lower_lattice_lines)
        kinf_three = fuel_assembly.search_for_k_inf(lower_top_lines)
        kinf_four = fuel_assembly.search_for_k_inf(upper_lattice_lines)
        kinf_five = fuel_assembly.search_for_k_inf(upper_top_lines)

        power_two = fuel_assembly.search_power_distributions(lower_lattice_lines)
        power_three = fuel_assembly.search_power_distributions(lower_top_lines)
        power_four = fuel_assembly.search_power_distributions(upper_lattice_lines)
        power_five = fuel_assembly.search_power_distributions(upper_top_lines)

        average_kinf_list = fuel_assembly.average_kinf_values_over_burnup(kinf_one, kinf_two, kinf_three, kinf_four, kinf_five, kinf_six)
        average_kinf = fuel_assembly.average_kinf_value(average_kinf_list)
        btf_list = fuel_assembly.calculate_btf(average_kinf_list, power_one, power_two, power_three, power_four, power_five, power_six)
                                                                                       
        score = fuel_assembly.calculate_bundle_cost(average_kinf,btf_list)
        temp_string_one = str(score)
        temp_string_two = str(btf_list)
        temp_string_three = str(average_kinf)
        cost_file.write(str(score)+'\n')
        total_track_file.write(temp_string_one.ljust(20) + temp_string_two.ljust(20) + temp_string_three.ljust(20)+'\n')


    cost_file.close()
    total_track_file.close()
		
#def two_d_btf(kinf_list, power_list):
#
#
##Calculates boiling transition factor for a single region.
#    additive_constants = np.matrix([[ 0.20,-0.10,-0.10,-0.10,-0.10, -0.10,-0.10,-0.10,-0.10, 0.20],
#                                    [ 0.20,-0.10,-0.10,-0.10,-0.10, -0.10,-0.10,-0.10,-0.10, 0.20],
#                                    [-0.10,-0.09,-0.09,-0.09,-0.09, -0.09,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09, 0.20,  0.20,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09,-0.09, -0.09,-0.09,-0.09,-0.09,-0.10],
#                                    [-0.10,-0.09,-0.09,-0.09,-0.09, -0.09,-0.09,-0.09,-0.09,-0.10],
#                                    [ 0.20,-0.10,-0.10,-0.10,-0.10, -0.10,-0.10,-0.10,-0.10, 0.20]])
#
#    weight_side = 0.2
#    weight_corner = 0.05
#
#    number_depletion_steps = len(kinf_list)
#    print number_depletion_steps
#    btf_matrix     = np.zeros((10,10, number_depletion_steps))
#    power_matrix   = np.zeros((10,10, number_depletion_steps))
#    number_corners = np.zeros((10,10, number_depletion_steps))
#    number_sides   = np.zeros((10,10, number_depletion_steps))
#    square_corner  = np.zeros((10,10, number_depletion_steps))
#    square_sides   = np.zeros((10,10, number_depletion_steps))
#    power_zones    = np.zeros((10,10, number_depletion_steps))
#
#    for w in xrange(number_depletion_steps):
#      power_matrix[:,:,w] = power_list[w][:,:]
#
#
#    for w in xrange(number_depletion_steps):
#      for x in xrange(10):
#        for y in xrange(10):
#          if(power_matrix[x,y,w] > 0):
#            power_zones[x,y,w] = 1
#
#
#    for w in xrange(number_depletion_steps):
#      for x in xrange(10):
#        for y in xrange(10):
#          if(x == 0):
#            pass
#          elif(x == 9):
#            pass
#          elif(y == 0):
#            pass
#          elif(y == 9):
#            pass
#          else:
#            number_corners[x,y,w] = power_zones[x-1,y-1,w] +  power_zones[x-1,y+1,w] + power_zones[x+1,y-1,w] + power_zones[x+1,y+1,w]
#            number_sides[x,y,w] = power_zones[x-1,y-1,w] +  power_zones[x-1,y+1,w] + power_zones[x+1,y-1,w] + power_zones[x+1,y+1,w]
#    
#    for w in xrange(number_depletion_steps):
#      for x in xrange(10):
#        for y in xrange(10):
#          if(x == 0):
#            pass
#          elif(x == 9):
#            pass
#          elif(y == 0):
#            pass
#          elif(y == 9):
#            pass
#          else:
#            square_corner[x,y,w] = power_matrix[x-1,y-1,w]**0.5 + power_matrix[x-1,y+1,w]**0.5 + power_matrix[x+1,y-1,w]**0.5 + power_matrix[x+1,y+1,w]**0.5
#            square_sides[x,y,w] = power_matrix[x-1,y-1,w]**0.5 +  power_matrix[x-1,y+1,w]**0.5 + power_matrix[x+1,y-1,w]**0.5 + power_matrix[x+1,y+1,w]**0.5
#
#
#    for w in xrange(number_depletion_steps):
#      for x in xrange(10):
#        for y in xrange(10):
#          if(power_matrix[x,y,w] > 0):
#            numerator = power_matrix[x,y,w]**0.5 + square_corner[x,y,w]*weight_corner + square_sides[x,y,w]*weight_side
#            print 'Numerator'
#            print numerator
#            denominator = 1 + number_sides[x,y,w]*weight_side + number_corners[x,y,w]*weight_corner
#            print 'Denominator'
#            denominator
#            btf_matrix[x,y,w] = (numerator/denominator) + additive_constants[x,y]
#    print 'BTF MATRIX'
#    print btf_matrix
##    print number_axial_positions
##    print number_depletion_steps
#    kinf_matrix = np.zeros((number_depletion_steps))
#    kinf_sum = 0
#    kinf_count = 0
#    for w in xrange(number_depletion_steps):
#        kinf_sum+=kinf_list[w]
#        kinf_count+=1
#    for w in xrange(number_depletion_steps):
#      for x in xrange(10):
#        for y in xrange(10):
#          if(power_matrix[x,y,w] > 0):
#            btf_matrix[x,y,w] = kinf_list[w]*kinf_count*btf_matrix[x,y,w]/kinf_sum
#    max_btf_value = np.zeros(number_depletion_steps)
#    for w in xrange(number_depletion_steps):
#      for x in xrange(10):
#        for y in xrange(10):
#          if(btf_matrix[x,y,w] > max_btf_value[w]):
#            max_btf_value[w] = btf_matrix[x,y,w]
#    print max_btf_value
#    return max_btf_value
#
#def two_d_score(kinf_list, btf_values):
#    number_depletion_steps = len(btf_values)
#    score = 0
#    kinf_weight = 100
#    for w in xrange(number_depletion_steps):
#      temp_one =  kinf_list[w] - 1.04
#
#      score+= (20/btf_values[w]) - kinf_weight*abs(temp_one)
#    return score	

def write_restart_file(i,j):
    restart_file_name = "'batch_"+str(i)+".lower_assembly."+str(j)+".res'"
    new_file_name =  'batch_'+str(i)+'.lower_top.'+str(j)+'.inp'

    new_file = open(new_file_name,'w')
    new_file.write('TTL * batch_'+str(i)+'.lower_top.'+str(j)+'\n')
    new_file.write('FIL '+restart_file_name+'\n')
    new_file.write("RES,'EX21', 0.0, 0.1 0.5\n")
#    new_file.write("RES,'EX21', 0.0, 0.1 0.5 1 1.5 2 2.5 3 3.5 4. 4.5 5. 5.5 6. 6.5 7. 7.5 8. 8.5 9. 9.5 10. 10.5 11. 11.5 12. 12.5 13.\n")
#    new_file.write('            13.5 14. 14.5 15. 15.5 16. 16.5 17. 17.5 18. 18.5 19. 19.5 20. 20.5 21. 21.5 22. 22.5 23. 23.5 24. 24.5\n')
#    new_file.write('            25. 25.5 26. 26.5 27. 27.5 28. 28.5 29. 29.5 30.\n')
    new_file.write('VOI=40\n')
    new_file.write('TFU=980.0\n')
    new_file.write('TMO=583.3\n')
    new_file.write('NLI, STA\n')
    new_file.write('END')
    new_file.close()

    restart_file_name = "'batch_"+str(i)+".upper_assembly."+str(j)+".res'"
    new_file_name =  'batch_'+str(i)+'.upper_top.'+str(j)+'.inp'

    new_file = open(new_file_name,'w')
    new_file.write('TTL * batch_'+str(i)+'.upper_top.'+str(j)+'\n')
    new_file.write('FIL '+restart_file_name+'\n')
    new_file.write("RES,'EX21', 0.0, 0.1 0.5\n")
#    new_file.write("RES,'EX21', 0.0, 0.1 0.5 1 1.5 2 2.5 3 3.5 4. 4.5 5. 5.5 6. 6.5 7. 7.5 8. 8.5 9. 9.5 10. 10.5 11. 11.5 12. 12.5 13.\n")
#    new_file.write('            13.5 14. 14.5 15. 15.5 16. 16.5 17. 17.5 18. 18.5 19. 19.5 20. 20.5 21. 21.5 22. 22.5 23. 23.5 24. 24.5\n')
#    new_file.write('            25. 25.5 26. 26.5 27. 27.5 28. 28.5 29. 29.5 30.\n')
    new_file.write('VOI=70\n')
    new_file.write('TFU=980.0\n')
    new_file.write('TMO=583.3\n')
    new_file.write('NLI, STA\n')
    new_file.write('END')
    new_file.close()

def special_evaluate_files(batch_size, generation):
#Function evaluates one batch at a time for special protocol instances. 

    submit_job_file(generation,0,batch_size,4)
    pwd = os.getcwd()
    os.system("ssh rdfmg 'cd "+pwd+"; qsub sub_file'")
    for j in xrange(batch_size):
      write_restart_file(0,j+1)

    total_track_file = open('total_track_file.txt','a')
    job_name = 'Mustang_'+str(generation)
    start = time.clock()
    finish = time.clock()
    while(finish - start < 10):
      finish = time.clock()
    job_finished = check_job_status(job_name)
    start = time.clock()
    while(job_finished == False):
      finish = time.clock()
      if(finish - start > 5):
        job_finished = check_job_status(job_name)
        start = time.clock()         
    
    bottom_file = open('bottom_lattice.out','r')
    bottom_lines = bottom_file.readlines()
    bottom_file.close()

    top_file = open('top_lattice.out','r')
    top_lines = top_file.readlines()
    top_file.close()

    cost_file = open('cost_list.txt','w')
    kinf_one = fuel_assembly.search_for_k_inf(bottom_lines)
    kinf_six = fuel_assembly.search_for_k_inf(top_lines)
    power_one = fuel_assembly.search_power_distributions(bottom_lines)
    power_six = fuel_assembly.search_power_distributions(top_lines)
                       
    for j in xrange(batch_size):
      lower_lattice_file = open('batch_0.lower_assembly.'+str(j+1)+'.out','r')
      lower_lattice_lines = lower_lattice_file.readlines()
      lower_lattice_file.close()
                           
      lower_top_file = open('batch_0.lower_top.'+str(j+1)+'.out','r')
      lower_top_lines = lower_top_file.readlines()
      lower_top_file.close()
                    
      upper_lattice_file = open('batch_0.upper_assembly.'+str(j+1)+'.out','r')
      upper_lattice_lines = upper_lattice_file.readlines()
      upper_lattice_file.close()
                    
      upper_top_file = open('batch_0.upper_top.'+str(j+1)+'.out','r')
      upper_top_lines = upper_top_file.readlines()
      upper_top_file.close()
                          
      kinf_two = fuel_assembly.search_for_k_inf(lower_lattice_lines)
      kinf_three = fuel_assembly.search_for_k_inf(lower_top_lines)
      kinf_four = fuel_assembly.search_for_k_inf(upper_lattice_lines)
      kinf_five = fuel_assembly.search_for_k_inf(upper_top_lines)
                       
      power_two = fuel_assembly.search_power_distributions(lower_lattice_lines)
      power_three = fuel_assembly.search_power_distributions(lower_top_lines)
      power_four = fuel_assembly.search_power_distributions(upper_lattice_lines)
      power_five = fuel_assembly.search_power_distributions(upper_top_lines)

      average_kinf_list = fuel_assembly.average_kinf_values_over_burnup(kinf_one, kinf_two, kinf_three, kinf_four, kinf_five, kinf_six)
      average_kinf = fuel_assembly.average_kinf_value(average_kinf_list)
      btf_list = fuel_assembly.calculate_btf(average_kinf_list, power_one, power_two, power_three, power_four, power_five, power_six)
      score = fuel_assembly.calculate_bundle_cost(average_kinf,btf_list)
      temp_string_one = str(score)
      #average_btf = fuel_assembly.average_btf_value(btf_list)
      temp_string_two = str(btf_list)
      temp_string_three = str(average_kinf)
      cost_file.write(temp_string_one+'\n')
      total_track_file.write(temp_string_one.ljust(20) + temp_string_two.ljust(20) + temp_string_three.ljust(20)+'\n')
    cost_file.close()
    total_track_file.close()        
