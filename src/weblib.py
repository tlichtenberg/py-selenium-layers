#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
    library for Selenium RC calls

    Copyright (C) 2012  Tom Lichtenberg
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

'''
import time
import platform
import sys
import os
import subprocess
import imaplib
from threading import Thread
from selenium import selenium
from selenium import webdriver
from selenium.webdriver.remote.command import Command
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

DEBUG = sys.flags.debug

class WebLib:
    
    def __init__(self, sel=None, settings={}):
        self.settings = settings
        self.url = settings.get('url', 'http://www.google.com')
        self.test_host = settings.get('test_host', 'localhost')
        self.test_port = settings.get('test_port', '4444')
        self.browser = settings.get('browser', '*chrome') 
        self.started = False
        self.driver = None
        print(settings)              
        self.sel = selenium(self.test_host, int(self.test_port), self.browser, self.url)
            
    def start_selenium(self,flags=None):
        if self.started == False:
            if flags != None:
                self.sel.start('commandLineFlags=%s' % flags)
            else:
                self.sel.start('commandLineFlags=-disable-web-security') # required for *googlechrome selenium clients
        # self.sel.start('commandLineFlags=-trustAllSSLCertificates') # selenium servers should be started with this flag
    
    def stop_selenium(self, screenshot=True):
        if screenshot == True:
            try:
                screenshots_filename = "screenshot.jpg"           
                self.get_screenshot("%s" % screenshots_filename) 
            except Exception as inst:
                print('error attempting to take screenshot in stop_selenium: %s' % inst)
           
        try: 
            self.sel.stop()
        except Exception as inst:
            print inst

    def get_selenium(self):
        return self.sel
    
    def submit(self):
        raise Exception('there is no submit method in WebLib')
    
    def open(self, url, ignore_exception=True):
        ''' calls selenium's version but swallows the exception '''
        try:
            self.sel.open(url)
            self.check_security()
        except:
            if ignore_exception == False:
                raise
            else:
                pass
            
    def get_network_traffic(self):
        ''' assumes that the selenium.py start method has been hacked to enable captureNetworkTraffic:
             def start(self, browserConfigurationOptions=None, captureNetworkTraffic=True):
              ...
                if captureNetworkTraffic:
                    start_args.append("captureNetworkTraffic=true")
            and it only seems to work for *googlechrome anyway
        '''
        output = self.sel.capture_network_traffic("xml")
        print(output)
    
    def check_security(self):
        if self.browser.find("*ie") >= 0:
            time.sleep(2)
            if self.sel.is_element_present("//a[contains(text(),'Continue to this website')]"):
                self.sel.click("//a[contains(text(),'Continue to this website')]")
                time.sleep(2)
        
    def press_enter(self, locator, timeout=1):
        self.wait_for_element(locator)
        self.sel.key_press(locator, "\\13")
        self.wait(timeout)
        
    def wait(self, timeout=1):
        count = 0
        while count < timeout:
            time.sleep(1)
            count = count + 1
            
    def wait_for_page_to_load(self, timeout=60000, ignore_exception=True):
        ''' calls selenium's version but swallows the exception 
            for ie, just wait a little ...
        '''
        try:
            if self.browser.find("*ie") >= 0:
                if int(timeout) > 10000:
                    tm = int(timeout) / 10000
                    time.sleep(tm)
            else:
                self.sel.wait_for_page_to_load(timeout)
        except:
            if ignore_exception == False:
                raise
            else:
                pass

    def wait_for_element(self, locator, timeout=20):
        count = 0
        while count < timeout:
            if self.sel.is_element_present(locator):
                if self.sel.is_visible(locator): # must be present AND visible!
                    return True
            time.sleep(1)
            count = count + 1
        return False
    
    def wait_for_text(self, text, timeout=20):
        count = 0
        while count < timeout:
            if self.sel.is_text_present(text):
                return True
            time.sleep(1)
            count = count + 1
        return False
              
    def wait_and_click(self, locator, timeout=20):
        found = self.wait_for_element(locator, timeout)
        if found:
            self.sel.click(locator)       
        return False
    
    def wait_and_type(self, locator, text, timeout=20):
        found = self.wait_for_element(locator, timeout)
        if found:
            self.sel.type(locator, text)
            return True
        return False
    
    def type_and_wait(self, locator, text, timeout=1):
        self.wait_for_element(locator)
        self.sel.type(locator, text)
        self.wait(timeout)
            
    def select_and_wait(self, locator, value, timeout=1):
        self.wait_for_element(locator)
        self.sel.select(locator, value)
        self.wait(timeout)
            
    def click_and_wait(self, locator, timeout=1):
        self.wait_for_element(locator)
        self.sel.click(locator)
        self.wait(timeout)
        
    def do_file_chooser(self, browser, locator, filename, url=""):
        if platform.system() == "Windows" and (browser.find("explore") >= 0 or browser.find("ie") >= 0):
            ''' run the Watir script file_upload.rb to do the file chooser stuff for IE '''
            root_directory = self.settings.get('root_directory', None)
            if root_directory == None:
                root_directory = os.getenv('TEST_HOME') + os.sep + "scripts" + os.sep
            script = root_directory + "file_upload.rb"
            if locator.find("id=") >= 0: # parse out the id of the locator ('id' is required for the script)
                idx1 = locator.find("id=") + 4
                idx2 = locator.find("']")
                locator = locator[idx1:idx2]
                print(locator)
                os.system('ruby %s %s %s %s' % (script, url, locator, filename))
                time.sleep(5)
            #===================================================================
            # ''' run AutoIt in its own thread, twice. once for each poster file '''
            # args = { "browser": browser, "filename": filename }
            # autoit = AutoIt("chooser", args)
            # autoit.start()       
            # self.sel.click(locator)
            # time.sleep(5)                  
            #===================================================================
        elif browser.find("*chrome") >= 0 or browser.find("*firefox") >= 0:
            ''' *chrome mode works for direct file input '''
            self.sel.type(locator, filename)
        else:
            return (True, '%s is not supported for File Chooser interactions' % browser)

    def logout(self):
        if self.wait_for_element("link=Sign Out") == True:
            self.sel.click("link=Sign Out")
            
    def type(self, locator, text, timeout=20):
        self.wait_for_element(locator, timeout)
        self.sel.type(locator, text)
            
    def click(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        self.sel.click(locator)
        
    def check(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        self.sel.check(locator)
        
    def uncheck(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        self.sel.uncheck(locator)
        
    def set_checked(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        if self.sel.get_value(locator) == 'off':
            self.sel.check(locator)
        
    def set_unchecked(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        if self.sel.get_value(locator) == 'on':
            self.sel.uncheck(locator)
    
    def fire_event(self, locator, event, timeout=20):
        self.wait_for_element(locator, timeout)
        self.sel.fire_event(locator, event)
        
    def choose_ok_on_next_confirmation(self):
        self.sel.choose_ok_on_next_confirmation()
        
    def accept_confirmation(self):
        ''' same as get_confirmation '''
        self.sel.get_confirmation()
        
    def get_confirmation(self):
        ''' same as accept_confirmation '''
        self.sel.get_confirmation()
        
    def deny_confirmation(self):
        pass # webdriver method
        
    def is_element_present(self, locator):
        return self.sel.is_element_present(locator)
    
    def go_back(self):
        self.sel.go_back()
        
    def get_all_window_names(self):
        return self.sel.get_all_window_names()
    
    def get_all_window_titles(self):
        return self.sel.get_all_window_titles()
    
    def get_title(self):
        return self.sel.get_title()
    
    def select_window(self, identifier):
        self.sel.select_window(identifier)
        
    def get_attribute(self, locator, attribute='value', timeout=20):
        # webdriverlib uses the attribute and timeout parameters
        return self.sel.get_attribute(locator)
    
    def close(self):
        self.sel.close()
        
    def refresh(self):
        self.sel.refresh()
        
    def get_select_options(self, locator):
        return self.sel.get_select_options(locator)
        
    def get_selected_label(self, locator):
        return self.sel.get_selected_label(locator)
    
    def get_selected_labels(self, locator):
        return self.sel.get_selected_labels(locator)
    
    def get_selected_value(self, locator):
        return self.sel.get_selected_value(locator)
    
    def get_selected_values(self, locator):
        return self.sel.get_selected_values(locator)
        
    def select(self, locator, value, timeout=20):
        self.wait_for_element(locator, timeout)
        self.sel.select(locator, value)
        
    def select_by_index(self, locator, index, timeout=20):
        ''' select by index '''
        self.wait_for_element(locator, timeout)
        self.sel.select(locator, index)
        
    def select_by_value(self, locator, value, timeout=20):
        ''' select by value attribute '''
        self.wait_for_element(locator, timeout)
        self.sel.select(locator, value)
        
    def is_text_present(self, text):
        '''  '''
        source = self.get_page_source()
        if source.find(text) >= 0:
            return True
        else:
            return False
    
    def is_visible(self, locator):
        return self.sel.is_text_present(locator)
    
    def get_screenshot(self, filename):
        self.sel.capture_entire_page_screenshot(filename, "")
    
    def get_xpath_count(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        return self.sel.get_xpath_count(locator)
    
    def key_down(self, locator, key, timeout=20):
        self.wait_for_element(locator, timeout)
        self.sel.key_down(locator, key)
        
    def key_up(self, locator, key, timeout=20):
        self.wait_for_element(locator, timeout)
        self.sel.key_up(locator, key)
        
    def get_text(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        return self.sel.get_text(locator).encode('utf-8') 
    
    def select_pop_up(self, which):
        self.sel.select_pop_up(which)
        
    def get_location(self):
        return self.sel.get_location()
    
    def move_to_element(self, locator):
        pass # webdriverlib method
    
    def hover_over_element(self, locator):
        self.sel.mouse_over(locator)
    
    def hover_and_click(self, locator):
        self.sel.mouse_over(locator)
        self.click(locator)
        
    def switch_to_frame_by_id(self, id=''):
        pass # webdriver method
            
    def switch_to_frame(self, index=0):
        pass # webdriver method
    
    def get_page_source(self):
        return self.sel.get_html_source()
