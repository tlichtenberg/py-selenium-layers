#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
    library for Selenium WebDriver calls

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
import os
import sys
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

class WebDriverLib:   
    def __init__(self, settings={}):
        self.settings = settings
        self.browser = settings.get('browser','*chrome')
        self.test_host = settings.get('test_host','localhost')
        self.test_port = settings.get('test_port', '4444')
        self.url = settings.get('url', 'http://www.google.com')
        self.dc = DesiredCapabilities()
        remote_url = "http://%s:%s/wd/hub" % (self.test_host, self.test_port)
        print("web driver url = %s" % remote_url)
        try:
            if self.browser.find("firefox") >= 0 or self.browser.find("*chrome") >= 0:
                self.dc = DesiredCapabilities.FIREFOX
                profile = webdriver.FirefoxProfile()
                profile.set_preference("browser.download.folderList",2)
                profile.set_preference("browser.download.manager.showWhenStarting",False)
                profile.set_preference("browser.download.dir", os.getcwd())
                profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream,text/html,text/x-csv,application/x-download,application/vnd.ms-excel,application/pdf")
                #profile.native_events_enabled = False # TODO: only as of selenium 2.19 ?? http://code.google.com/p/selenium/issues/detail?id=3369
                if self.browser.find("*firefox3.6") >= 0: # *firefox3_6 on Linux
                    self.dc['version'] = "3.6"
                    self.dc['platform'] = 'LINUX'
                elif self.browser.find("*firefox3") >= 0: # *firefox3_6 on Windows
                    self.dc['version'] = "3"
                    self.dc['platform'] = 'WINDOWS'
                else:
                    self.dc['version'] = "13"
                    self.dc['platform'] = 'WINDOWS'
                self.sel = webdriver.Remote(str(remote_url), self.dc, browser_profile=profile)            
            elif self.browser.find("googlechrome") >= 0:
                self.dc = DesiredCapabilities.CHROME
                self.dc["chrome.switches"] = ["--ignore-certificate-errors"]
                self.sel = webdriver.Remote(str(remote_url), self.dc)
            elif self.browser.find("*mock") >= 0:
                self.dc = DesiredCapabilities.HTMLUNIT
                self.sel = webdriver.Remote(str(remote_url), self.dc)
            elif self.browser.find("android") >= 0:
                self.dc = DesiredCapabilities.ANDROID
                self.sel = webdriver.Remote(str(remote_url), self.dc)                             
            elif self.browser.find("ie") >= 0:
                self.dc = DesiredCapabilities.INTERNETEXPLORER
                self.dc['browserName'] = "iexplore"
                if self.browser == "*ie8":
                    self.dc['version'] = "8"
                elif self.browser == "*ie9":
                    self.dc['version'] = "9"
                else: # default
                    self.dc['version'] = "9"
                self.sel = webdriver.Remote(str(remote_url), self.dc)  
            else: # default to IE
                self.dc = DesiredCapabilities.INTERNETEXPLORER
                self.sel = webdriver.Remote(str(remote_url), self.dc)
        except Exception as inst:
            print(inst)
            
        self.action_chains = ActionChains(self.sel) 
        #self.sel.implicitly_wait(5) # set an implicit wait on all finds
            
    def start_selenium(self):
        ''' self.sel.start() -> webdriver has no start method '''
        pass
    
    def stop_selenium(self, screenshot=True):
        ''' get a final screenshot and quit selenium '''
        if screenshot == True:
            try:
                screenshots_filename = "screenshot.jpg"
                self.get_screenshot("%s" % screenshots_filename) 
            except Exception as inst:
                print('error attempting to take screenshot in stop_selenium: %s' % inst)
            
        # quit selenium
        try:
            self.sel.quit()
        except Exception as inst:
            print('error attempting to quit selenium: %s' % inst)
            
    def submit(self, locator):
        element = self.sel.find_element_by_xpath(locator)
        element.submit()
        
    def get_selenium(self):
        return self.sel
    
    def set_desired_capabilities(self):
        self.dc.FIREFOX()
        
    def close(self):
        self.sel.close() # closes the current window
    
    def open(self, url, ignore_exception=True):
        ''' calls webdriver's version but swallows the exception '''
        try:
            self.sel.get(url)
            self.check_security()
        except:
            if ignore_exception == False:
                raise
            else:
                pass
            
    def check_security(self):
        ''' ie support only '''
        if self.browser.find("ie") >= 0 :
            time.sleep(2)
            try:
                found = self.is_element_present("//*[@id='overridelink']")
                if found == True:
                    self.click("//*[@id='overridelink']")
                time.sleep(2)
            except:
                pass
                
    def wait_for_page_to_load(self, timeout=60):
        ''' use javascript to determine when the page is ready '''
        if timeout > 1000:  # convert milliseconds to seconds
            timeout = timeout / 1000
        w = WebDriverWait(self.sel, timeout)
        w.until(lambda d: d.execute_script("return document.readyState == 'complete'"))
        
    def wait_for_element(self, locator, timeout=20):
        try:
            w = WebDriverWait(self.sel, timeout)
            w.until(lambda d: d.find_element_by_xpath(locator).is_displayed())
            return True
        except:
            return False           
    
    def wait_for_text(self, text, timeout=20):
        try:
            w = WebDriverWait(self.sel, timeout)
            w.until(lambda d: d.find_element_by_tag_name('body').is_displayed())
            t = self.sel.find_element_by_tag_name('body').text
            if t.find(text) >= 0:
                return True               
            return False
        except:
            return False
        
    def wait_and_click(self, locator, timeout=20):
        for i in range(timeout):
            try:
                if locator.find('link=') == 0:
                    locator_string = locator[5:len(locator)]
                    element = self.sel.find_element_by_link_text(locator_string)
                elif locator.find('xpath=') == 0: # array of elements
                    element = self.get_xpath_element(locator)
                else:
                    element = self.sel.find_element_by_xpath(locator)
                    
                if element != None:
                    element.click()  
                return 
            except:
                time.sleep(1)       
    
    def wait_and_type(self, locator, text, timeout=20):
        try:
            if locator.find('xpath=') == 0: # array of elements
                element = self.get_xpath_element(locator)
            else:
                self.wait_for_element(locator, timeout)
                element = self.sel.find_element_by_xpath(locator)
              
            if element != None:  
                element.clear()
                element.send_keys(text)
        except:
            pass
        
    def type(self, locator, text, timeout=20):
        if locator.find('xpath=') == 0: # array of elements
            element = self.get_xpath_element(locator)
        else:
            self.wait_for_element(locator, timeout)
            element = self.sel.find_element_by_xpath(locator)
            
        if element != None:
            element.clear()
            element.send_keys(text)
    
    def type_and_wait(self, locator, text, timeout=1):
        if locator.find('xpath=') == 0: # array of elements
            element = self.get_xpath_element(locator)
        else:
            self.wait_for_element(locator, timeout)
            element = self.sel.find_element_by_xpath(locator)
            
        if element != None:
            element.clear()
            element.send_keys(text)
            time.sleep(timeout)
            
    def select_and_wait(self, locator, value, timeout=1, reverse=False):
        self.select(locator, value)
        time.sleep(timeout)
            
    def click_and_wait(self, locator, timeout=1):
        if locator.find('link=') == 0:
            locator_string = locator[5:len(locator)]
            element = self.sel.find_element_by_link_text(locator_string)
        elif locator.find('xpath=') == 0: # array of elements
            element = self.get_xpath_element(locator)
        else:
            element = self.sel.find_element_by_xpath(locator)
            
        if element != None:
            element.click()       
            time.sleep(timeout)
        
    def do_file_chooser(self, browser, locator, filename, url=""):
        ''' this just works for webdriver - major improvement over selenium 1 '''
        print('do_file_chooser called with locator=%s, filename=%s' % (locator, filename))
        element = self.sel.find_element_by_xpath(locator)
        element.send_keys(filename)

    def logout(self, link_text="SIGN OUT"):
        try:
            element = WebDriverWait(self.sel, 10).until(lambda driver : self.sel.find_element_by_link_text(link_text).is_displayed())
            element.click()
        except:
            pass
            
    def click(self, locator):
        if locator.find('link=') == 0:
            locator_string = locator[5:len(locator)]
            element = self.sel.find_element_by_link_text(locator_string)
        elif locator.find('xpath=') == 0: # array of elements
            element = self.get_xpath_element(locator)
        else:
            element = self.sel.find_element_by_xpath(locator)
            
        if element != None:
            element.click()     
        
    def check(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        if element and element.is_selected() == False:
            element.click()     
        
    def uncheck(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        if element and element.is_selected() == True:
            element.click()   
            
    def set_checked(self, locator, timeout=20):
        self.check(locator, timeout)
        
    def set_unchecked(self, locator, timeout=20):
        self.uncheck(locator, timeout)
    
    def fire_event(self, locator, event):
        '''  '''
        self.sel.fire_event(locator, event)
        
    def choose_ok_on_next_confirmation(self):
        '''  '''
        # self.sel.choose_ok_on_next_confirmation()
        
    def accept_confirmation(self):
        ''' same as get_confirmation '''
        alert = self.sel.switch_to_alert()
        alert.accept();
        
    def get_confirmation(self):
        '''  same as accept_confirmation '''
        alert = self.sel.switch_to_alert()
        alert.accept();
        
    def deny_confirmation(self):
        '''  '''
        alert = self.sel.switch_to_alert()
        alert.dismiss()
        
    def is_element_present(self, locator, timeout=5):
        try:
            found = self.wait_for_element(locator, timeout)
            print('is_element_present is returning %s after %s seconds' % (found, timeout))
            if found: 
                return True
            else:
                return False
        except:
            return False
    
    def go_back(self):
        self.sel.back()
        
    def get_all_window_names(self):
        ''' same as titles '''
        titles = []
        handles = self.sel.window_handles
        for h in handles:
            self.sel.switch_to_window(h)
            titles.append(self.sel.title)
        self.sel.switch_to_window(handles[0])
        return titles
    
    def get_all_window_titles(self):
        ''' same as names'''
        titles = []
        handles = self.sel.window_handles
        for h in handles:
            try:
                self.sel.switch_to_window(h)
                titles.append(self.sel.title)
            except:
                continue
        self.sel.switch_to_window(handles[0])
        return titles
    
    def get_title(self):
        return self.sel.title
    
    def select_window(self, identifier):
        ''' match the name with the handle '''
        all_titles = []
        handles = self.sel.window_handles
        for h in handles:
            self.sel.switch_to_window(h)
            all_titles.append(self.sel.title)
        count = 0
        for t in all_titles:
            if t.find(identifier) >= 0:    
                self.sel.switch_to_window(handles[count])
            count = count + 1
        
    def get_attribute(self, locator, timeout=20):
        ''' finds the attribute 'value' '
            needs to be fixed for attributes in general, 
            but xpath= parsing would have to calculate based on that
        '''
        #FIXME for any given attribute
        if locator.find('xpath=') == 0: # array of elements
            element = self.get_xpath_element(locator)
        else:
            self.wait_for_element(locator, timeout)
            element = self.sel.find_element_by_xpath(locator)
        
        if element != None:
            return element.get_attribute('value')
        else:
            return ''
    
    def do_select(self, element, value, press_enter=False):
        try:
            if element.text.find(value) >= 0:
                allOptions = element.find_elements_by_tag_name("option")
                for option in allOptions:
                    if option.text == value:
                        option.click()   
                        if press_enter == True: 
                            element.send_keys(option.text, Keys.RETURN) 
                        return True       
        except:
            pass  
        return False    
    
    def get_id_from_locator(self, locator):
        if locator.find("@id=") >= 0:
            index1 = locator.find("@id=") + 5
            index2 = locator.find("']", index1)
            id = locator[index1:index2]
            print("weblib.get_id_from_locator: id = %s" % id)
            return id
        else:
            return ''
    
    def get_select_options(self, locator):
        select = Select(self.sel.find_element_by_id(self.get_id_from_locator(locator)))
        return select.options
        
    def get_selected_label(self, locator):       
        select = Select(self.sel.find_element_by_id(self.get_id_from_locator(locator)))
        option = select.first_selected_option
        return option.text
    
    def get_selected_labels(self, locator):
        labels = []
        select = Select(self.sel.find_element_by_id(self.get_id_from_locator(locator)))
        options = select.all_selected_options
        for o in options:
            labels.append(o.text)
        return labels
    
    def get_selected_value(self, locator):
        select = Select(self.sel.find_element_by_id(self.get_id_from_locator(locator)))
        option = select.first_selected_option
        return option.get_attribute('value')
    
    def get_selected_values(self, locator):
        values = []
        select = Select(self.sel.find_element_by_id(self.get_id_from_locator(locator)))
        options = select.all_selected_options
        for o in options:
            values.append(o.get_attribute('value'))
        return values

    def select(self, locator, value, timeout=1):
        ''' select by visible text '''
        select = Select(self.sel.find_element_by_id(self.get_id_from_locator(locator)))
        select.select_by_visible_text(value)
        
    def select_by_index(self, locator, index):
        ''' select by index '''
        select = Select(self.sel.find_element_by_id(self.get_id_from_locator(locator)))
        select.select_by_index(index)
        
    def select_by_value(self, locator, value):
        ''' select by value attribute '''
        select = Select(self.sel.find_element_by_id(self.get_id_from_locator(locator)))
        select.select_by_value(value)
        
    def is_text_present(self, text):
        '''  '''
        source = self.get_page_source()
        if text.find(source) >= 0:
            return True
        else:
            return False
        
    def is_visible(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        return element.is_displayed()
    
    def get_screenshot(self, filename):
        self.sel.get_screenshot_as_file(filename)
        
    def get_xpath_count(self, locator):
        try:
            elements = self.sel.find_elements_by_xpath(locator)
            return len(elements)
        except:
            return 0
        
    def key_down(self, locator, key, timeout=20):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        ActionChains.key_down(self.action_chains, element)
        
    def key_up(self, locator, key, timeout=20):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        ActionChains.key_up(self.action_chains, element)
        
    def get_text(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        text = element.text       
        if text == None or len(text) == 0: # might just be the value attribute of the element
            text = element.get_attribute('value')
        if text != None:
            return text.encode('utf-8') 
        else:
            return ''
    
    def get_page_source(self):
        return self.sel.page_source # not a method, but a property
        
    def select_pop_up(self, which):
        ''' attempt to close a popped up window '''
        # self.sel.select_pop_up(which)
        self.sel.switch_to_window(which)
        self.sel.close()
              
    def get_location(self):
        return self.sel.current_url # not a method but a property
    
    def hover_over_element(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        action = ActionChains(self.sel)
        action.move_to_element(element)
        action.perform()
        
    def hover_and_click(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        action = ActionChains(self.sel)
        action.click(element) # move_to and click
        action.perform()
    
    def get_network_traffic(self):
        ''' assumes that the selenium.py start method has been hacked to enable captureNetworkTraffic:
             def start(self, browserConfigurationOptions=None, captureNetworkTraffic=True):
              ...
                if captureNetworkTraffic:
                    start_args.append("captureNetworkTraffic=true")
            and it only seems to work for *googlechrome anyway
        '''
        #output = self.sel.capture_network_traffic("xml")
        print('get_network_traffic is a noop for webdriverlib')
          
    def double_click(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        action = ActionChains(self.sel)
        action.double_click(element)
        action.perform()
        
    def double_click_on_element(self, element):
        action = ActionChains(self.sel)
        action.double_click(element)
        action.perform()
        
    def refresh(self):
        self.sel.refresh()
        
    def press_enter(self, locator, timeout=1):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        element.send_keys(Keys.RETURN);
        time.sleep(timeout)
        
    def move_to_element(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        self.action_chains.move_to_element(element)
        
    def switch_to_frame_by_id(self, id=''):
        self.sel.switch_to_frame(self.sel.find_element_by_id(id)); 
            
    def switch_to_frame(self, index=0):       
        self.sel.switch_to_frame(index)
        
    def get_xpath_element(self, locator):
        ''' used when locator is passed in the form of
            "xpath=(//button[contains(@onclick,'addToCart')])[3]"
        '''
        if locator.find('xpath=') == 0: # array of elements
            lindex = 7
            rindex = locator.rfind(')') # right most closing paren
            new_locator = locator[lindex:rindex]
            elements = self.sel.find_elements_by_xpath(new_locator)
            try:
                array_index = int(locator[rindex + 2: len(locator) - 1])
                element = elements[array_index]
            except Exception as inst:
                print(inst)
                element = elements[0] # default to
            return element
        else:
            return None