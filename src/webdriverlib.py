#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
    library for selenium/browser calls
'''
import time
import os
import sys
import imaplib
import logging
import ptest_utils
import urllib2
import cookielib
import datetime
from weblib import IEKiller
from threading import Thread
from selenium import selenium
from selenium import webdriver
from selenium import common
from selenium.webdriver.remote.command import Command
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.common.by import By

DEBUG = sys.flags.debug
USE_HUB = True # True for Grid 2 WebDriver, False for local WebDriver
resources_home = os.getenv('TEST_HOME') + os.sep + "resources" + os.sep 
log = logging.getLogger()

class WebDriverLib:   
    def __init__(self, settings={}):
        self.settings = settings
        self.browser = settings.get('browser','*chrome')
        self.test_host = settings.get('test_host','localhost')
        self.test_port = settings.get('test_port', '4444')
        self.url = settings.get('url', 'http://www.google.com')
        self.dc = DesiredCapabilities()
        self.sel = None
        remote_url = "http://%s:%s/wd/hub" % (self.test_host, self.test_port)
        log.debug("web driver url = %s" % remote_url)
        log.debug("browser is %s" % self.browser)
        try:
            if self.browser.find("firefox") >= 0 or self.browser.find("*chrome") >= 0:
                self.dc = DesiredCapabilities.FIREFOX
                if USE_HUB == False:
                    self.sel = webdriver.Firefox()
                else:
                    profile = webdriver.FirefoxProfile()
                    profile.set_preference("browser.download.folderList",2)
                    profile.set_preference("browser.download.manager.showWhenStarting",False)
                    profile.set_preference("browser.download.dir", os.getcwd())
                    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-rar,application/x-rar-compressed,application/x-tar-gz,application/zip,application/x-tar,application/x-gzip,binary/octet-stream,application/octet-stream,text/html,text/x-csv,application/x-download,application/vnd.ms-excel,application/pdf")
                    #profile.native_events_enabled = False # TODO: only as of selenium 2.19 ?? http://code.google.com/p/selenium/issues/detail?id=3369
                    #===========================================================
                    # if self.browser.find("*firefox3.6") >= 0: # *firefox3_6 on Linux
                    #    self.dc['version'] = "3.6"
                    #    self.dc['platform'] = 'LINUX'
                    # elif self.browser.find("*firefox3") >= 0: # *firefox3_6 on Windows
                    #    self.dc['version'] = "3"
                    #    self.dc['platform'] = 'WINDOWS'
                    # else:
                    #===========================================================
                    self.dc['version'] = ""
                    self.dc['platform'] = 'WINDOWS'
                    self.sel = webdriver.Remote(str(remote_url), self.dc, browser_profile=profile)            
            elif self.browser.find("googlechrome") >= 0:
                self.dc = DesiredCapabilities.CHROME
                self.dc['browserName'] = "chrome"
                self.dc["chrome.switches"] = ["--ignore-certificate-errors", "--user-data-dir=%s" %  resources_home]
                if USE_HUB == False:
                    self.sel = webdriver.Chrome()
                else:
                    self.sel = webdriver.Remote(str(remote_url), self.dc)
            elif self.browser.find("*mock") >= 0:
                self.dc = DesiredCapabilities.HTMLUNIT
                self.sel = webdriver.Remote(str(remote_url), self.dc)
            elif self.browser.find("android") >= 0:
                self.dc = DesiredCapabilities.ANDROID
                if USE_HUB == False:
                    log.info('unsupported webdriver.Android. USE_HUB instead')
                else:
                    self.sel = webdriver.Remote(str(remote_url), self.dc)                             
            elif self.browser.find("ie") >= 0:
                self.dc = DesiredCapabilities.INTERNETEXPLORER
                if USE_HUB == False:
                    self.sel = webdriver.Ie()
                else:
                    self.dc['browserName'] = "ie"
                    if self.browser == "*ie8":
                        self.dc['version'] = "8"
                    elif self.browser == "*ie9":
                        self.dc['version'] = "9"
                    elif self.browser == "*ie10":
                        self.dc['version'] = "10"
                    elif self.browser == "*ie11":
                        self.dc['version'] = "11"
                    #else: # default
                    #    self.dc['version'] = "11"
                    self.sel = webdriver.Remote(str(remote_url), self.dc)  
            else: # default to IE
                self.dc = DesiredCapabilities.INTERNETEXPLORER
                if USE_HUB == False:
                    self.sel = webdriver.Ie()
                else:
                    self.sel = webdriver.Remote(str(remote_url), self.dc)
        except Exception as inst:
            log.error(inst)
            
        if(self.sel == None):
            raise ("failed to instantiate WebDriverLib")           
        self.action_chains = ActionChains(self.sel) 
        #self.sel.implicitly_wait(5) # set an implicit wait on all finds
            
    def start_selenium(self, flags=None):
        ''' self.sel.start() -> webdriver has no start method. flags ignored here  '''
        pass
    
    def stop_selenium(self):
        ''' get a final screenshot and quit selenium '''
        try:
            screenshots_home = os.getenv('TEST_HOME') + os.sep + "resources" + os.sep + "images" + os.sep + "screenshots" + os.sep
            screenshots_filename = "screenshot.jpg"
            test_name = ptest_utils.get_calling_test()
            if test_name != None:
                screenshots_filename = test_name + "_" + screenshots_filename
            self.get_screenshot("%s%s" % (screenshots_home, screenshots_filename)) 
        except Exception as inst:
            pass
            # log.error('error attempting to take screenshot in stop_selenium: %s' % inst)
        
        # quit selenium
        try:
            for handle in self.sel.window_handles:
                log.debug("switch to window '%s' and close it" % handle)
                self.sel.switch_to_window(handle)
                self.close()
            self.sel.quit()
            # kill any IE instances that might have gotten stuck - windows specific!
            #if self.browser.find("ie") >= 0:
            #    killer = IEKiller()
            #    killer.start()
        except Exception as inst:
            log.error('error attempting to quit selenium: %s' % inst)
            
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
            #self.check_security() # no longer used, was IE-specific
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
                found = self.is_element_present("//*[@id='overridelink']", 5)
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
        
    def wait_for_element(self, locator, timeout=15):
        try:
            w = WebDriverWait(self.sel, timeout)
            w.until(lambda d: d.find_element_by_xpath(locator).is_displayed())
            return True
        except Exception as x: # e.g. selenium.common.exceptions.StaleElementReferenceException
            log.debug(x)
            return False 
        return False          
    
    def wait_for_text(self, text, timeout=15):
        try:
            #w = WebDriverWait(self.sel, timeout)
            #w.until(lambda d: d.find_element_by_tag_name('body').is_displayed())
            count = 0
            while count < timeout:
                t = self.sel.find_element_by_tag_name('body').text
                if t.find(text) >= 0:
                    return True  
                else:
                    count = count + 1
                    time.sleep(1)             
            return False
        except:
            return False
        
    def wait_and_click(self, locator, timeout=5):
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
    
    def wait_and_type(self, locator, text, timeout=5):
        time.sleep(timeout)
        
        if self.browser.find('*ie') >= 0: # workaround for Internet Explorer. send_keys is much too slow
            if self.do_text_input_ie(locator, text) == True:
                return
           
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
        
    def type(self, locator, text, timeout=5):
        if self.browser.find('*ie') >= 0: # workaround for Internet Explorer. send_keys is much too slow
            if self.do_text_input_ie(locator, text) == True:
                return
            
        if locator.find('xpath=') == 0: # array of elements
            element = self.get_xpath_element(locator)
        else:
            self.wait_for_element(locator, timeout)
            element = self.sel.find_element_by_xpath(locator)
            
        if element != None:
            element.clear()
            element.send_keys(text)
    
    def type_and_wait(self, locator, text, timeout=1):
        if self.browser.find('*ie') >= 0: # workaround for Internet Explorer. send_keys is much too slow
            log.debug("calling do_text_input_ie")
            if self.do_text_input_ie(locator, text) == True:
                time.sleep(timeout)
                return
        
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
            
    def find_element_by_link_text(self, locator):
        return self.sel.find_element_by_link_text(locator)
        
    def do_file_chooser(self, browser, locator, filename, url=""):
        ''' this just works for webdriver - major improvement over selenium 1 '''
        log.debug('do_file_chooser called with locator=%s, filename=%s' % (locator, filename))
        if self.browser.find("*ie") >= 0:
            self.sel.switch_to_alert()
        element = self.sel.find_element_by_xpath(locator)
        element.send_keys(filename)

    def logout(self):
        try:
            locator = "Sign Out"
            element = WebDriverWait(self.sel, 2).until(lambda driver : self.sel.find_element_by_link_text(locator).is_displayed())
            element.click()
        except:
            pass
        
    def right_click(self, locator):
        self.context_click(locator)
        
    def context_click(self, locator):
        if locator.find('link=') == 0:
            locator_string = locator[5:len(locator)]
            element = self.sel.find_element_by_link_text(locator_string)
        elif locator.find('xpath=') == 0: # array of elements
            element = self.get_xpath_element(locator)
        else:
            element = self.sel.find_element_by_xpath(locator)
            
        if element != None:
            action = ActionChains(self.sel)
            action.context_click(element)
            action.perform()
            
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
        
    def check(self, locator, timeout=5):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        if element and element.is_selected() == False:
            element.click()     
        
    def uncheck(self, locator, timeout=5):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        if element and element.is_selected() == True:
            element.click()   
            
    def is_selected(self, locator, timeout=5):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        return element.is_selected()
            
    def set_checked(self, locator, timeout=5):
        self.check(locator, timeout)
        
    def set_unchecked(self, locator, timeout=5):
        self.uncheck(locator, timeout)
    
    def fire_event(self, locator, event):
        ''' ?? '''
        self.sel.fire_event(locator, event)
        
    def choose_ok_on_next_confirmation(self):
        ''' ?? '''
#        self.sel.choose_ok_on_next_confirmation()
        
    def accept_confirmation(self):
        ''' same as get_confirmation '''
        alert = self.sel.switch_to_alert()
        alert.accept();
        
    def get_confirmation(self):
        '''  same as accept_confirmation '''
        alert = self.sel.switch_to_alert()
        alert.accept();
        
    def deny_confirmation(self):
        ''' ?? '''
        alert = self.sel.switch_to_alert()
        alert.dismiss()
        
    def is_element_present(self, locator, timeout=5):
        try:
            found = self.wait_for_element(locator, timeout)
            log.debug('is_element_present is returning %s after %s seconds' % (found, timeout))
            if found: 
                return True
            else:
                return False
        except Exception as x: # e.g. selenium.common.exceptions.StaleElementReferenceException
            log.debug(x)
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
        
    def get_attribute(self, locator, timeout=5, attribute='value'):
        ''' finds the attribute 'value' '
            needs to be fixed for attributes in general, but xpath= parsing would have to calculate based on that
        '''
        #FIXME for any given attribute
        if locator.find('xpath=') == 0: # array of elements
            element = self.get_xpath_element(locator)
        else:
            self.wait_for_element(locator, timeout)
            element = self.sel.find_element_by_xpath(locator)
        
        if element != None:
            return element.get_attribute(attribute)
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
            log.debug("weblib.get_id_from_locator: id = %s" % id)
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
        
    def is_text_present(self, text, encode=False):
        '''internationalize it '''
        try:
            source = self.get_page_source().encode('utf-8')
            if encode == True:
                if source.find(text) >= 0:
                    return True
                else:
                    return False
            else:  # decode both strings
                if ptest_utils.strfind(source, text) >= 0:
                    return True
                else:
                    return False
        except Exception as x: # e.g. selenium.common.exceptions.StaleElementReferenceException
            log.error ("Exception in WebDriverLib.is_text_present. may need to set unicode param to False: %s" % x)
            return False 
        
    def is_visible(self, locator, timeout=5):
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
        
    def key_down(self, locator, key, timeout=5):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        ActionChains.key_down(self.action_chains, element)
        
    def key_up(self, locator, key, timeout=5):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        ActionChains.key_up(self.action_chains, element)
        
    def get_text(self, locator, timeout=5):
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
    
    def hover_over_element(self, locator, timeout=5):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        action = ActionChains(self.sel)
        action.move_to_element(element)
        action.perform()
        
    def hover_and_click(self, locator, timeout=5):
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
        log.info('get_network_traffic is a noop for webdriverlib')
        
    def get_transaction_id(self, aria_url, user_account, ariaUser, ariaPW, transid, timeout=5):
        plan = ""
        channel_name = ""
        self.open(aria_url)
        self.wait_for_element("//*[@id='username']", 20)
        if self.is_element_present("//*[@id='username']"):
            self.wait_and_type("//input[@id='username']", ariaUser)
            self.wait_and_type("//input[@id='password']", ariaPW)
            time.sleep(5)
            self.click("//input[@type='submit']")
            self.wait_for_page_to_load(30000)
        time.sleep(10)
        self.type_and_wait("//*[@name='inSearchString']", user_account)
#        self.type_and_wait("//*[@id='quick-search']/form/input[1]", user_account)
        self.click("//*[@type='submit']")
        time.sleep(5)
        self.open(aria_url)
        if transid == None:
            transaction = self.get_text("xpath=(//tr[contains(@class,'dataRow')][last()-1])")
            trans_data = transaction.split(' ') #get the details
            transaction_id = trans_data[0]
            price = trans_data[len(trans_data)-1].replace('(','').replace(')','')
        else:
            self.click_and_wait("//*[contains(text(),'%s')]" % transid) # select the transaction
            time.sleep(3)
            if self.is_element_present("//tr[contains(@class,'dataRow0')]//a"): #wacky, there are at times 2 here, one for .99
                self.click_and_wait("//tr[contains(@class,'dataRow0')]//a") # select invoice #
            invoice = self.get_text("//tr[contains(@class,'dataRow0')]")
            invoice_num = invoice.split(' ') #get the details
            channel_name = invoice_num[2]
            plan = invoice_num[invoice_num.index('Plan')+1]
            price = invoice_num[len(invoice_num)-1]
            transaction_id = transid
        return transaction_id, price, plan, channel_name
        
    def verify_order_email(self, gmail_url, order_num, line_items, gmailUser, gmailPW, timeout=20):
        mail = imaplib.IMAP4_SSL(gmail_url)
        mail.login(gmailUser, gmailPW)
        mail.list()
        mail.select("inbox")
        result, data = mail.uid('search', None, '(HEADER Subject "%s")' % order_num)
        latest_email_uid = data[0].split()[-1]
        result, data = mail.uid('fetch', latest_email_uid, '(RFC822)')
        for i in line_items:
            if str(data).find(i) < 0:
                log.error('did not find expected "%s" in "%s"' % (i, data))
                return False
        return True
        
    def verify_tax(self, shop_admin_tax_url, zipcode, line_items, magentoUser, magentoPW):
        self.open(shop_admin_tax_url)
        self.wait_for_element("//*[@id='username']", 20)
        if self.is_element_present("//*[@id='username']"):
            self.type_and_wait("//*[@id='username']", magentoUser)
            self.type_and_wait("//*[@id='login']", magentoPW) 
            self.wait_and_click("//*[@title='Login']")
            self.wait_for_page_to_load(60000)
        self.type_and_wait("//*[@id='tax_rate_grid_filter_tax_postcode']", zipcode)
        self.press_enter("//*[@id='tax_rate_grid_filter_tax_postcode']", 10)
        tax_rate = self.get_text("//td[contains(@class,'last')]")
        tax_percentage = float(tax_rate) / 100.000
        discounted = float(line_items[0])-float(line_items[2])
        tax = tax_percentage * float(discounted)
        rounded = round(tax,2)
        if rounded == float(line_items[1]):
            return tax_rate
        return False
    
    def verify_no_tax(self, shop_admin_tax_url, zipcode, line_items, magentoUser, magentoPW):
        self.open(shop_admin_tax_url)
        self.wait_for_element("//*[@id='username']", 20)
        if self.is_element_present("//*[@id='username']"):
            self.type_and_wait("//*[@id='username']", magentoUser)
            self.type_and_wait("//*[@id='login']", magentoPW) 
            self.wait_and_click("//*[@title='Login']")
            self.wait_for_page_to_load(60000)
        self.type_and_wait("//*[@id='tax_rate_grid_filter_tax_postcode']", zipcode)
        self.press_enter("//*[@id='tax_rate_grid_filter_tax_postcode']", 10)
        if not self.is_element_present("//td[contains(@class,'last')]"):
            return True
        return False
    
    def verify_web_tax(self, tax_url, state, city, zipcode, tax):
        state = state.replace(" ","_")
        city = city.replace(" ","_")
        url = '%s/%s/%s/%s' % (tax_url,state,city,zipcode)
        jar = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        log.info(url)
        html = opener.open(url).read()
        tax_web_rate = round(float(html[html.find('sales tax rate is ')+18:html.find('sales tax rate is ')+22]),2)
        log.info('the taxes found on the web are %s, magento %s' % (tax_web_rate,round(float(tax),2)))
        if tax_web_rate == round(float(tax),2):
            return True
        return False
        
    def verify_order(self, shop_admin_url, order_num, magentoUser, magentoPW, line_items=[], timeout=20):
        count = 0
        self.open(shop_admin_url)
        self.wait_for_page_to_load(45000)
        self.wait_for_element("//*[@id='username']") # 2014.02.12 toml: used to be waiting for 60 seconds
        if self.is_element_present("//*[@id='username']"):
            self.type_and_wait("//*[@id='username']", magentoUser)
            self.type_and_wait("//*[@id='login']", magentoPW) 
            self.wait_and_click("//*[@title='Login']")
            self.wait_for_page_to_load(45000)
        self.wait_for_element("//*[@id='sales_order_grid_filter_real_order_id']") # 2014.02.12 toml: used to be waiting for 60 seconds
        self.type_and_wait("//*[@id='sales_order_grid_filter_real_order_id']", order_num)
        self.press_enter("//*[@id='sales_order_grid_filter_real_order_id']", 10)
        while count < timeout:
            if self.is_text_present("Total 1 records found"):
                if line_items != []:
                    self.click_and_wait("//td[contains(text(),'%s')]" % order_num, 5)
                    self.wait_for_page_to_load(60000)
                    if not self.is_text_present(line_items[1]):
                        return False
                self.click_and_wait("//a[@class='link-logout']") # logout or the next pass we will be stuck at the dashboard page
                return True
            time.sleep(1)
            count = count + 1
        return False
    
    def verify_order_ns(self, netsuite_url, cus_name, order_num, priority, carrier, nsUser, nsPW, timeout=100):
        count = 0
        found_it = False
        self.open(netsuite_url)
        self.wait_for_element("//input[@name='email']", 20)
        if self.is_element_present("//input[@name='email']"):
            self.type_and_wait("//input[@name='email']", nsUser)
            self.type_and_wait("//input[@name='password']", nsPW) 
            self.wait_and_click("//input[@name='submitButton']")
            self.wait_for_page_to_load(30000)
        #now handle the case for the additional authentication
        if self.is_text_present("In what city or town was your first job?"):
            self.type_and_wait("//input[@class='input hidepassword']", "santa clara") 
            self.wait_and_click("//input[@type='submit']")
            self.wait_for_page_to_load(30000)
        elif self.is_text_present("In what city did you meet your spouse/significant other?"):
            self.type_and_wait("//input[@class='input hidepassword']", "saratoga") 
            self.wait_and_click("//input[@type='submit']")
            self.wait_for_page_to_load(30000)
        elif self.is_text_present("What was your childhood nickname?"):
            self.type_and_wait("//input[@class='input hidepassword']", "photobridge") 
            self.wait_and_click("//input[@type='submit']")
            self.wait_for_page_to_load(30000)
        # run cron scripts to get priority and shipping email
        time.sleep(3)
        log.info(time.gmtime())
        
        # run the deployment script at least once
        # enter the order number, and if the popupsuggest element shows up, break out and move on
        while count < timeout:
            log.info("run deployment script")
            self.run_ns_deployment_script()
            self.type_and_wait("//input[@name='_searchstring']", order_num, 3)
            if not self.is_element_present("//div[@class='popupsuggest']"): #("//a[@class='textwhitenolink']"):
                log.info("popupsuggest not found")
                count = count + 1
                time.sleep(1)
            else:
                log.info("found it")
                log.info(time.gmtime())
                found_it = True
                self.click("//input[@id='_searchSubmitter']")
                self.wait_for_page_to_load(45000)
                break # count = timeout
            
        if found_it == True:        
        #=======================================================================
        # while count < timeout:
        #     if not self.is_element_present("//div[@class='popupsuggest']"): #("//a[@class='textwhitenolink']"):
        #         self.type_and_wait("//input[@name='_searchstring']", order_num)
        #         count = count + 1
        #     else:
        #         found_it = True
        #         log.info(time.gmtime())
        #         count = timeout
        #         self.run_ns_deployment_script()
        #         log.info("ran deployment script, count = %s, found_it = %s" % (count, found_it))
        #=======================================================================

        #=======================================================================
        # if found_it:
        #     self.type_and_wait("//input[@name='_searchstring']", order_num)
        #     self.wait_for_element("//input[@id='_searchSubmitter']")
        #     if self.is_element_present("//input[@id='_searchSubmitter']"):
        #         log.info("click on _searchSubmitter")
        #         self.click("//input[@id='_searchSubmitter']")
        #         self.wait_for_page_to_load(45000)
        #=======================================================================
            #===================================================================
            # if self.is_element_present("//input[@name='email']"): # got kicked out? element non-editable?
            #     try:
            #         log.info("found email input object")
            #         self.type_and_wait("//input[@name='email']", nsUser)
            #         self.type_and_wait("//input[@name='password']", nsPW) 
            #         self.wait_and_click("//input[@name='submitButton']")
            #         self.wait_for_page_to_load(45000)
            #     except:
            #         log.info("ok. exception on looking for email input object")
            #         pass
            #===================================================================
            log.info("sleep 20")
            time.sleep(20)
            log.info("wake up")
            the_date = datetime.datetime.now().strftime('X%m/X%d/%Y').replace('X0','X').replace('X','')#hehe
            log.info("looking for date %s" % the_date)
            if self.is_element_present("//*[contains(text(),'%s')]" % the_date):               
                log.info('click on Record')
                self.wait_and_click("//*[contains(text(),'%s')]" % the_date)
                time.sleep(30)
            log.info('click on System Information')
            self.click("//*[@id='s_sysinfotxt']")
            log.info('clicked System Information')
            time.sleep(10)
            if carrier.find('day') >= 0:
                carrier = carrier.replace('day','Day') # different string in NS than magento
            carrier_present = self.is_text_present(carrier, False)
            log.info("is carrier %s present? %s" % (carrier, carrier_present))
            if carrier_present == True:
                priority_present = self.is_text_present(priority, False)
                count = 0
                while count < timeout:
                    log.info("is priority %s present? %s" % (priority, priority_present))
                    self.refresh()
                    self.click("//*[@id='s_sysinfotxt']")
                    time.sleep(10)
                    self.type_and_wait("//input[@id='systemnotes_SystemNote_FIELD_display']", "Order Priority")
                    self.click("//*[@id='SystemNote_FIELD_popup_muli']")  # was an <input, now an <a, so just do wildcard
                    priority_present = self.is_text_present(priority, False)
                    if priority_present == True:
                        count = timeout
                        return True
                    count = count + 1         
        return False
    
    def run_ns_deployment_script(self, timeout=20):
        count = 0
        self.open('https://system.sandbox.netsuite.com/app/common/scripting/scriptrecord.nl?id=3&scripttype=102&e=T')
        log.info('.. run_ns_deployment_script')
        while count < timeout:
            element = self.sel.find_element_by_xpath("//*[@class='bntBgB multiBnt']") 
            mouse = webdriver.ActionChains(self)
            mouse.move_to_element(element)
            element.click()
            time.sleep(3)
            self.click("//*[contains(@href,'submitexecute')]")
            log.info("deployment script clicked on submitexecute, now waiting 30 seconds")
            time.sleep(30)
            count = timeout
            if self.is_text_present('a'):
                return True    
            else:
                count = count + 1
        return False
        
    def set_fraud(self, shop_admin_fraud_url, ip_address, magentoUser, magentoPW, timeout=5):
        count = 0
        self.open(shop_admin_fraud_url)
        log.info('setting fraud IP to %s' % ip_address)
        self.wait_for_element("//*[@id='username']", 60)
        if self.is_element_present("//*[@id='username']"):
            self.type_and_wait("//*[@id='username']", magentoUser)
            self.type_and_wait("//*[@id='login']", magentoPW) 
            self.wait_and_click("//*[@title='Login']")
        if not self.is_element_present("//*[@id='frauddetection_debug_force_ip']"):
            self.click_and_wait("//a[@id='frauddetection_debug-head']", 5)
        self.wait_for_element("//*[@id='frauddetection_debug_force_ip']", 60)
        self.type_and_wait("//*[@id='frauddetection_debug_force_ip']", ip_address)
        self.click_and_wait("//*[@onclick='configForm.submit()']", 5)
        while count < timeout:
            if not self.is_text_present("The configuration has been saved."):
                return False
            #on dmo, we do not invalidate cache for fraud updates now.  who knew?
#            self.click_and_wait("//a[contains(text(),'Cache Management')]")
#            self.click_and_wait("//*[contains(text(),'Flush Cache Storage')]")
#            self.get_confirmation()
            time.sleep(5)
            self.click_and_wait("//a[@class='link-logout']") # logout or the next pass we will be stuck at the dashboard page
            return True
            time.sleep(1)
            count = count + 1
        return False
    
    def set_backorder(self, shop_admin_backorder_url, qty, magentoUser, magentoPW, timeout=5):
        count = 0
        self.open(shop_admin_backorder_url)
        log.info('setting backorder for Roku 3')
        self.wait_for_element("//*[@id='username']", 60)
        if self.is_element_present("//*[@id='username']"):
            self.type_and_wait("//*[@id='username']", magentoUser)
            self.type_and_wait("//*[@id='login']", magentoPW) 
            self.wait_and_click("//*[@title='Login']")
        self.wait_for_element("//*[@id='product_info_tabs_inventory']", 60)
        self.click_and_wait("//*[@id='product_info_tabs_inventory']", 5)
        if self.get_selected_value("//select[@id='inventory_manage_stock']") == '0':
            self.select_by_value("//select[@id='inventory_manage_stock']", '1')
            self.set_unchecked("//input[@id='inventory_use_config_backorders']")
        self.type_and_wait("//*[@id='inventory_qty']", qty[0])
        self.select_by_value("//select[@id='inventory_stock_availability']", qty[1])#0 out, 1 in
        self.select_by_value("//select[@id='inventory_backorders']", qty[2]) #0 none, 2 notify
        self.click_and_wait("//*[@onclick='productForm.submit()']", 5)
        while count < timeout:
            if not self.is_text_present("The product has been saved."):
                return False
            self.click_and_wait("//a[contains(text(),'Cache Management')]")
            self.click_and_wait("//*[contains(text(),'Flush Cache Storage')]")
            self.get_confirmation()
            time.sleep(5)
            self.click_and_wait("//a[@class='link-logout']") # logout or the next pass we will be stuck at the dashboard page
            return True
            time.sleep(1)
            count = count + 1
        return False
    
    def verify_order_st(self, smartturn_url, order_num, priority, carrier, smartturnUser, smartturnPW, timeout=20):
        count = 0
        loop = 0
        log.debug('going to smartturn at : %s' % smartturn_url)
        self.open(smartturn_url)
        self.wait_for_element("//*[@id='username']", 60)
        log.debug('logging in with %s/%s' % (smartturnUser, smartturnPW))
        self.type_and_wait("//*[@id='username']", smartturnUser)
        self.type_and_wait("//*[@id='password']", smartturnPW)
        time.sleep(10) 
        element = self.sel.find_element_by_xpath("//input[@type='submit']")
        element.click()
        time.sleep(10)
        self.click("//*[@id='outboundOrdersLink']")
        time.sleep(10)
        found_page = self.is_text_present('Ship to customer')
        if found_page == False: # try again. sometimes that click doesn't work!
            self.click("//*[@id='outboundOrdersLink']")
            time.sleep(10)
        while not self.is_text_present(order_num, False) and loop < 20: 
            self.refresh()
            time.sleep(30)
            loop = loop + 1
            
        if self.is_text_present(order_num, False) == False:
            return (False, "did not find the expected order_num %s" % order_num) # give up if we still haven't found the order number
        
        elements = self.sel.find_elements_by_tag_name("span")
        for e in elements:
            if e.text.find(order_num, False) >= 0: # found it, now double_click it
                self.double_click_on_element(e)
                break
        log.info("found the order_num %s" % order_num)
        time.sleep(10)
        order_info = self.get_text("//div[@class='extended_page-2-column-fields']")
        try:
            order_info = order_info[order_info.find('Priority'):order_info.find('Warehouse')]
        except:
            order_info = self.get_text("//div[@class='extended_page-2-column-fields']")
        log.info("looking for priority %s and carrier %s" % (priority, carrier))
        if self.is_text_present(priority, False):
            log.info("found the priority %s" % priority)
            log.info("now looking for the carrier %s" % carrier)
            if self.is_text_present(carrier, False):
                log.info("found the carrier %s" % carrier)
                return (True, '')
            else:
                return (False, "did not find the expected carrier: %s, but got this order info: %s" % (carrier, order_info)) 
        else:
            return (False, "did not find the expected priority: %s, but got this order info: %s" % (priority, order_info))   
    
    def double_click(self, locator, timeout=5):
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
        
    def move_to_element(self, locator, timeout=5):
        self.wait_for_element(locator, timeout)
        element = self.sel.find_element_by_xpath(locator)
        self.action_chains.move_to_element(element)
        
    def switch_to_frame_by_id(self, id=''):
        self.sel.switch_to_frame(self.sel.find_element_by_id(id)); 
        
    def switch_to_default_content(self):
        self.sel.switch_to_default_content()
            
    def switch_to_frame(self, index=0):       
        self.sel.switch_to_frame(index)
        
    def maximize(self):
        self.sel.maximize_window()
        
    def scroll_to_bottom(self):
        self.sel.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
    def get_xpath_element(self, locator):
        ''' used when locator is passed in the form of
            "xpath=(//button[contains(@onclick,'addToCart')])[3]"
        '''
        if locator.find('xpath=') == 0: # array of elements
            lindex = 7
            rindex = locator.rfind(')') # right most closing paren
            rindex2 = locator.rfind(']', rindex) # right most closing bracket
            #log.debug('rindex = %s' % rindex)
            #log.debug('rindex2 = %s' % rindex2)
            new_locator = locator[lindex:rindex]
            #log.debug('new_locator = %s' % new_locator)
            elements = self.sel.find_elements_by_xpath(new_locator)
            try:
                array_index = int(locator[rindex + 2: rindex2])
                #log.debug('array_index = %s' % array_index)
                element = elements[array_index]
            except Exception as inst:
                #log.error(inst)
                element = elements[0] # default to
            return element
        else:
            return None
        
    def do_javascript(self, script):
        ''' execute raw javascript '''
        if script.find("return ") != 0:  # for webdriver, javascript must begin with 'return '
            script = "return " + script
        return self.sel.execute_script(script)
    
    def get_element_id_from_locator(self, locator):
        ''' assumes 'locator' is in the form of "//*[@id='UserName']"
            where the id field is an exact match and is the only field
            in the locator
        '''
        idx1 = locator.find('@id=')
        if idx1 > 0:
            idx2 = len(locator) - 2
            return locator[idx1+5:idx2]
        else:
            return None
        
    def get_element_name_from_locator(self, locator):
        ''' assumes 'locator' is in the form of "//*[@name='UserName']"
            where the id field is an exact match and is the only field
            in the locator
        '''
        idx1 = locator.find('@name=')
        if idx1 > 0:
            idx2 = len(locator) - 2
            return locator[idx1+7:idx2]
        else:
            return None
        
    def get_element_type_from_locator(self, locator):
        ''' assumes 'locator' is in the form of "//*[@type='text']"
            where the id field is an exact match and is the only field
            in the locator
        '''
        idx1 = locator.find('@type=')
        if idx1 > 0:
            idx2 = len(locator) - 2
            return locator[idx1+7:idx2]
        else:
            return None
        
    def do_text_input_ie(self, locator, text):
        if self.browser.find('*ie') >= 0: # workaround for Internet Explorer. send_keys is much too slow
            elem_id = self.get_element_id_from_locator(locator)
            if elem_id != None:
                script = "return document.getElementById('%s').value='%s'" % (elem_id, text)
                self.do_javascript(script) 
                return True
            else:
                elem_name = self.get_element_name_from_locator(locator)
                if elem_name != None:
                    script = "return document.getElementsByName('%s')[0].value='%s'" % (elem_name, text)
                    self.do_javascript(script) 
                    return True
        return False
            