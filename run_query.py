#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 06:33:53 2019

@author: Mirkazemi

This script is provided to get the number density of stars at diffrenet
point of sky within DES footprints. The right ascensions and declinations
of the point are given in a CSV (',' separated) file with columsn name
of 'ra' and 'dec'.  

You need to have an account on: https://model.obs-besancon.fr/ws/

To run the scrip in the terminal run run_query.py by following arguments:

run_query.py 
   -c Chrome Driver address
   -r a fiolder address or saving the results
   -p a CSV file address including 'ra' and 'dec' columns for locations
      in the sky.
   -a area in degree^2, It should be between 0 and 42000

"""

import argparse
import getpass
import os 
import BesanconWorker
import pandas as pd
import sys
import time


if __name__ == '__main__':
    t0 = time.time()
    parser = argparse.ArgumentParser(description='Query for Besancon Model')
    parser.add_argument('-u', '--username', type=str, help='Username to login in "https://model.obs-besancon.fr/ws".')
    parser.add_argument('-c', '--chromedriver_address', type=str, help='Address of chrome driver.')
    parser.add_argument('-r', '--result_folder', type=str, help='Address of a folder for saving results.')
    parser.add_argument('-p', '--positions', type=str, help='Address of a CSV file inclduing "ra" and "dec" columns.')
    parser.add_argument('-a', '--area', type=float, help='Area in the unit of degree^2.')
    
    args = parser.parse_args()
    
    # checks if the address of Chrome Driver is correct
    if not os.path.isfile(args.chromedriver_address):
        raise FileNotFoundError(f"The Chrome Driver does not exist at '{args.chromedriver_address}'.")
    
    # checks if the folder of results exists
    if not os.path.isdir(args.result_folder):
        raise FileNotFoundError(f"The result folder '{args.result_folder}' does not exist.")
 
    # checks if the file of ras and decs exists       
    if not os.path.isfile(args.positions):
        raise FileNotFoundError(f"The following file does not exit: '{args.positions}'.")

    # checks if the file of ras and decs exists       
    if (args.area < 0) or (42000 <= args.area):
        raise FileNotFoundError(f"The area should be between a and 42000. Given area '{args.area}'.")
        
    # reads the positions as a pandas.DataFrame
    positions_df = pd.read_csv(args.positions)

    # check if the 'ra' column exits in the position file
    if 'ra' not in positions_df.columns.values:
        print(f"There is no column 'ra' in {args.positions} file.")
        sys.exit()

    # check if the 'dec' column exits in the position file
    if 'dec' not in positions_df.columns.values:
        print(f"There is no column 'ra' in {args.positions} file.")
        sys.exit()       
        
    # gets password
    password = getpass.getpass(prompt='password? ')    

    # creates a worker object
    bw = BesanconWorker.BesanconWorker(auth = (args.username, password),
                                       ChromeDriver_address = args.chromedriver_address,
                                       result_folder = args.result_folder)     
    
    # login to https://model.obs-besancon.fr/ws
    bw.login()
    
    # if you prefer to delete all previous jobs
#    bw.delete_all_jobs()
    
    filters_2 = ['R', 'I']
    
    # Creating and running the jobs in a loop:  
    for i, row in positions_df.iterrows():
        ti0 = time.time()
        print(f"job number: {i} ra: {row['ra']}, dec: {row['dec']}")
    
        p_acol = ','.join([f + '-' + 'G' for f in filters_2])
        col_step = ','.join(['1.0'] * len(filters_2))
        col_min = ','.join(['-10.0'] * len(filters_2))
        col_max = ','.join(['99.0'] * len(filters_2))
    
        options = {'p_sendmail' : '0', # not sending email
                   'p_KLEH' : '2', # equatorial coordinate
                   'p_KLEC' : '10', # Johnson-Cousins+GAIA G band
                   'p_KLEI' : '1'} # FITS format output
        
        variables = {'p_acol' : p_acol,
                     'p_col_step' : col_step,
                     'p_col_min' : col_min,
                     'p_col_max' : col_max,
                     'p_Coor1_min' : str(row['ra']),
                     'p_Coor2_min' : str(row['dec']),
                     'p_Coor1_max' : str(row['ra']),
                     'p_Coor2_max' : str(row['dec']),
                     'p_ref_filter' : 'G',
                     'p_SOLI' : str(args.area),
                     'p_band_min' : ','.join(['-99.0'] * 10 + ['10']),
                     'p_band_max' : ','.join(['99.0'] * 10 + ['24']),
                     'p_band_step' : ','.join(['1.0'] * 11),
                     'p_errBand_A' : ','.join(['0.02'] * 11),
                     'p_errBand_B' : ','.join(['0.0'] * 11),
                     'p_errBand_C' : ','.join(['0.0'] * 11)}            
        # creating a job:
        bw.create_job()
        
        # its jobID should be the last one in the job list:
        jobID = bw.jobs_df['jobId'].values[-1]
        
        # setting the job parameters:        
        bw.set_param(jobID = jobID, 
                     options = options,
                     variables = variables)
        
        # running the job and wait until job completation 
        bw.run(jobID = jobID)
        
        # doanloading the results
        bw.download(jobID = jobID)
              
        # deleting completed job
        bw.delete_job(jobID = jobID)
        
        # renaming the result files
        file_name_old = 'output.fits'
        head_name_old = 'output-head'   
        
        fits_file_new = str(i) + '.fits'
        head_file_new = str(i) + '_head.txt'
        args.result_folder
        os.rename( os.path.join(args.result_folder, file_name_old),
                   os.path.join(args.result_folder, fits_file_new))
        os.rename( os.path.join(args.result_folder, head_name_old),
                   os.path.join(args.result_folder, head_file_new))   
              
        # writing a report line for completed jon
        report = ','.join([str(i), str(row['ra']), str(row['dec']), 
                                  str(args.area), fits_file_new, head_file_new,
                                  str(time.time() - ti0)])
        print(report)
        with open(os.path.join(args.result_folder, 'results.csv'), 'a') as w_res:
            w_res.write(report)
            w_res.write('\n')
    
    # printing the total time for running all jobs
    print('total time:', time.time() - t0)


