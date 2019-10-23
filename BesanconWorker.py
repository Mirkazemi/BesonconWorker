#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 11:54:25 2019

@author: mirkazemi
"""

from selenium import webdriver
from selenium.webdriver.support.ui import Select
import xml.etree.ElementTree as ET
import os
import sys
import time
import pandas as pd


def XMLstring2pandas(xmlRoot):
    """
    converts xml table to pandas.DataFrame
      
    Parameters
    ----------
    xmlRoot : str
        table in XML format
    """

    colnames = []
    _df = pd.DataFrame()
    
    if 0 < len(xmlRoot):
        for col in xmlRoot[0]:
            colnames.append(col.text)
            _df[col.text] = []

        if 1 < len(xmlRoot):
            for i, _colname in enumerate(colnames):
                _df[_colname] = [x[i].text for x in xmlRoot[1:]]
                
    return _df

            
            
            

class BesanconWorker():
    """
    Worker for managing job at https://model.obs-besancon.fr/ws/
    
    By this class one can create, delete, and run a serie of jobs using 
    Python scripting. It can also edit the parameters and download the
    result files.
    
    Attributes
    ----------
    jobs_df : pandas.DataFrame
        a table containing existing jobs and their status

    Methods
    -------
    login()
        Logins into https://model.obs-besancon.fr/ws/
        
    create_job()
        Creates a new job
        
    delete_job(jobID = None):
        Deletes a job with job = jobID if it exists.
    
    delete_all_jobs()
        Deletes all exicting jobs.
        
    set_param(jobID, options = {}, variables = {})
        Sets the options and variable for the job with job ID = jobID.
        
    run(jobID)    
        Runs the job with job ID = jobID and wait until it is completed.
        
    download(jobID)
        Downloads the output and header of the job with ID = jobID.
        
    """
    
    def __init__(self, auth, ChromeDriver_address, result_folder):
        """
        Parameters
        ----------
        auth : tuple
            A tuple consisting the username and the password in str
            
        ChromeDriver_address: str
            the address of the Chrome Driver exective file
            
        result_folder : str
            the folder address for downloading the result files
        """
        
        self.auth = auth
        self.result_folder = result_folder
        
        # setting the download folder
        prefs = {"download.default_directory" : result_folder}      
        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_experimental_option("prefs",prefs)
        
        # creating Chrome WebDriver
        self.driver = webdriver.Chrome(executable_path=ChromeDriver_address, chrome_options=chromeOptions)
        
    def login(self):
        """
        Logins into https://model.obs-besancon.fr/ws/ and updates the
        jobs_df by reading job list.
        """
        
        self.driver.get('https://model.obs-besancon.fr/ws/')
        
        try:
            # entering username
            user_box = self.driver.find_element_by_id('login_user')
            user_box.clear()
            user_box.send_keys(self.auth[0])
            
            # entering password 
            pass_box = self.driver.find_element_by_id('login_pass')
            pass_box.clear()
            pass_box.send_keys(self.auth[1])
            
            # clicking on login button
            login_button = self.driver.find_element_by_xpath("//input[@value='login']")
            login_button.click()
            time.sleep(2)
            self.read_job_list()
            
        except:
            print('Username or password are not correct!')
            sys.exit()
            
        
    def create_job(self):
        """
        Creates a new job and updates the jobs_df.
        """
        
        _n = len(self.jobs_df)
        self.driver.find_element_by_xpath("//*[contains(text(), 'New job')]").click()
        
        # waiting until the job list is updated on the web
        while _n == len(self.jobs_df):
            time.sleep(0.1)
            self.read_job_list()
        
    def read_job_list(self):
        """
        Reads the job list and save it in jobs_df attribute as a
        pandas.DataFrame
        """
        
        _job_table = self.driver.find_element_by_xpath("//*[@id='listjobs_table']")
        self.jobs_df =  XMLstring2pandas(xmlRoot = 
                                         ET.fromstring(_job_table.get_attribute('outerHTML')))

    def click_job(self, jobID = None):
        """
        Clicks on a job with given job ID
        
        Parameters
        ----------
        jobID : str
            ID of the job that is supposed to be clicked.
        """
        
        self.driver.find_elements_by_xpath("//*[contains(text(), '"+ jobID +"')]")[0].click()
        time.sleep(1)
        
    def delete_job(self, jobID = None):
        """
        Clicks on a job with given job ID
        
        Parameters
        ----------
        jobID : str
            ID of the job that is supposed to be deleted.
        """      
        
        if jobID in self.jobs_df['jobId'].values:
            _l = len(self.driver.find_elements_by_xpath("//*[contains(text(), '"+ jobID +"')]"))
            self.click_job(jobID = jobID)
            self.driver.find_elements_by_xpath("//*[contains(text(), 'Delete')]")[0].click()
            self.driver.switch_to.alert.accept()
            while _l == len(self.driver.find_elements_by_xpath("//*[contains(text(), '"+ jobID +"')]")):
                time.sleep(0.2)
            self.read_job_list()
        else:
            print('No such a jobID:', jobID)
    
    def delete_all_jobs(self):
        """
        Deletes all existing jobs
        """
        
        jobIDs = self.jobs_df['jobId'].values
        for i, jobID in enumerate(jobIDs):
            self.click_job(jobID = jobID)
            self.delete_job(jobID = jobID)

            
    def set_param(self, jobID, options = {}, variables = {}):
        """
        Sets the input variables and options for job with jobID.
        The variables and options are specified by 'id' of the element
        in the source of webpage. The options are spesified by 'value'
        in the source too (integer). 
        
        Parameters
        ----------
        jobID : str
            ID of the target job. The job should be already created.
            
        options : {}
            A dictionary of options that needed to be change from default
            values.
            
        variables : {}
            A dictionary of variable that needed to be change from default
            values.            
        """
        
        self.click_job(jobID = jobID)
        for _key, _value in options.items():
            Select(self.driver.find_element_by_id(_key)).select_by_value(_value)
            
        for _key, _value in variables.items():
#            print(_key, _value)
            self.driver.find_element_by_id(_key).clear()
            self.driver.find_element_by_id(_key).send_keys(_value)
        time.sleep(2)
        try:
            self.driver.find_elements_by_xpath("//*[contains(text(), 'Save changes')]")[0].click()
            time.sleep(1)
        except:
            pass
    
    def if_completed(self, jobID, total_time = 300):
        """
        waits until the job is completed. If the job completes within
        total_time in seconds, True and duration time are returned. 
        Otherwise, False and duration time are returned.
        
        Parameters
        ----------
        jobID : str
            ID of the target job. The job should be already run.
            
        total_time : float
            maximum time to wait for completing the job.        
        """
        
        t0 = time.time()
        for t in range(0,total_time, 2):
            self.driver.find_elements_by_xpath("//*[contains(text(), 'Refresh')]")[0].click()
            time.sleep(1)
            self.read_job_list()
            if self.jobs_df.loc[self.jobs_df['jobId'] == jobID, 'phase'].values[0] == 'COMPLETED':
                return True, time.time() - t0
            time.sleep(1)
        return False, time.time() - t0
            
    def run(self, jobID):
        """
        Runs the job.
        
        Parameters
        ----------
        jobID : str
            ID of the target job. The job should be already creaeted.
        """
        
        self.click_job(jobID = jobID)
        self.driver.find_elements_by_xpath('//*[@id="jobdetails_box"]/div[2]/a[1]/span')[0].click()
        self.driver.switch_to.alert.accept()
        time.sleep(2)
        ifcomplete, t = self.if_completed(jobID = jobID, total_time = 300)
         
        if ifcomplete:
            pass
        else:
            print(f'The run of job with jobID = {jobID} was not completed in {t} second.')
            sys.exit()
            
            
        
    def download(self, jobID):
        """
        Downloads the output and header files.
        The output should be already set to fits format by set_param 
        method (set_param({'p_KLEI' : '1'})). The files are downloaded
        by 'output.fits' and 'output-head' names. If there is any
        file with such names exists in the download folder, it will be
        deleted before downloading.
        
        Parameters
        ----------
        jobID : str
            ID of the target job. The job should be already creaeted.
        """        
        
        # clicking on the job
        self.click_job(jobID = jobID)
        
        file_name = 'output.fits'
        head_name = 'output-head'
        
        file_address = os.path.join(self.result_folder, file_name)
        head_address = os.path.join(self.result_folder, head_name)
        
        # Delete any file with name of 'output.fits' or 'output-head'
        if os.path.isfile(file_address):
            os.remove(file_address)
            
        if os.path.isfile(head_address):
            os.remove(head_address)
        
        # Downloading catalog file
        self.driver.find_element_by_link_text(file_name).click()
        # Waiting until download completion
        while not os.path.exists(file_address):
            time.sleep(0.5)
            
        # Downloading header file    
        self.driver.find_element_by_link_text(head_name).click()
        # Waiting until download completion
        while not os.path.exists(file_address):
            time.sleep(0.5)
