#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
    library for selenium/browser calls
'''
import time
import platform
import sys
import os
import subprocess
import imaplib
import logging
import ptest_utils
import urllib2
import cookielib
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
USE_HUB = True # True for Grid 2 WebDriver, False for local WebDriver
log = logging.getLogger()

class WebLib:
    
    def __init__(self, settings={}, sel=None):
        self.settings = settings
        self.extra = settings.get('extra', None)
        self.url = settings.get('url', 'http://www.google.com')
        self.test_host = settings.get('test_host', 'localhost')
        self.test_port = settings.get('test_port', '4444')
        self.browser = settings.get('browser', '*chrome') 
        self.started = False
        self.driver = None
        log.debug(settings)
        if self.extra == 'rc': # can use WebDriverBackedSelenium as of Selenium 2.19
            if self.browser.find("firefox") >= 0 or self.browser.find("*chrome") >= 0:
                self.dc = DesiredCapabilities.FIREFOX
                #profile = webdriver.FirefoxProfile()
                #profile.native_events_enabled = False # TODO: only as of selenium 2.19 ?? http://code.google.com/p/selenium/issues/detail?id=3369
                self.driver = RemoteWebDriver(desired_capabilities = self.dc) #, browser_profile=profile )
            elif self.browser.find("googlechrome") >= 0:
                self.dc = DesiredCapabilities.CHROME
                self.driver = RemoteWebDriver(desired_capabilities = self.dc)
            elif self.browser.find("android") >= 0:
                self.dc = DesiredCapabilities.ANDROID   
                self.driver = RemoteWebDriver(desired_capabilities = self.dc)                       
            elif self.browser.find("ie") >= 0:
                self.dc = DesiredCapabilities.INTERNETEXPLORER
                self.driver = RemoteWebDriver(desired_capabilities = self.dc)
            elif self.browser.find("*mock") >= 0:
                self.dc = DesiredCapabilities.HTMLUNIT
                self.driver = RemoteWebDriver(desired_capabilities = self.dc)
                
            if self.driver != None:
                self.sel = selenium(self.test_host, self.test_port, '*webdriver', self.url)
                self.sel.start(driver=self.driver)
                self.started = True
        elif sel == None:     
            if self.browser.find("*ie") >= 0:
                self.browser = '*iexplore'
            self.sel = selenium(self.test_host, int(self.test_port), self.browser, self.url)
        else:
            self.sel = sel
            
    def start_selenium(self, flags=None):
        if self.started == False:
            if flags != None:
                self.sel.start('commandLineFlags=%s' % flags)
            else:
                if self.browser.find("ie") < 0:
                    self.sel.start('commandLineFlags=--disable-web-security') # required for *googlechrome selenium clients and *firefox Selenium RC
                else:
                    self.sel.start()
        # self.sel.start('commandLineFlags=-trustAllSSLCertificates') # selenium servers should be started with this flag
    
    def stop_selenium(self):
        try:
            screenshots_home = os.getenv('TEST_HOME') + os.sep + "resources" + os.sep + "images" + os.sep + "screenshots" + os.sep
            screenshots_filename = "screenshot.jpg"
            test_name = ptest_utils.get_calling_test()
            if test_name != None:
                screenshots_filename = test_name + "_" + screenshots_filename
            self.get_screenshot("%s%s" % (screenshots_home, screenshots_filename)) 
        except Exception as inst:
            log.error('error attempting to take screenshot in stop_selenium: %s' % inst)
            
        self.sel.stop()
        # kill any IE instances that might have gotten stuck - windows specific!
        if self.browser.find("ie") >= 0:
            killer = IEKiller()
            killer.start()
        
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
        log.info(output)
    
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
    
    def get_transaction_id(self, aria_url, user_account, ariaUser, ariaPW, transid, timeout=20):
        plan = ""
        channel_name = ""
        self.sel.open(aria_url)
        self.wait_for_element("//*[@id='username']", 20)
        if self.is_element_present("//*[@id='username']"):
            self.wait_and_type("//input[@id='username']", ariaUser)
            self.wait_and_type("//input[@id='password']", ariaPW)
            time.sleep(5)
            self.click("//input[@type='submit']")
            self.wait_for_page_to_load(30000)
        time.sleep(3)
        self.type_and_wait("//*[@name='inSearchString']", user_account)
        self.click("//*[@type='submit']")
        time.sleep(5)
        self.sel.open(aria_url)
        if transid == None:
            transaction = self.get_text("xpath=(//tr[contains(@class,'dataRow')][last()-1])")
            trans_data = transaction.split(' ') #get the details
            transaction_id = trans_data[0]
            price = trans_data[len(trans_data)-1].replace('(','').replace(')','')
        else:
            self.click_and_wait("//*[contains(text(),'%s')]" % transid) # select the transaction
            time.sleep(3)
            if self.is_element_present("//tr[contains(@class,'dataRow0')]//a"):
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
        self.sel.open(shop_admin_tax_url)
        self.wait_for_element("//*[@id='username']", 20)
        if self.is_element_present("//*[@id='username']"):
            self.type_and_wait("//*[@id='username']", magentoUser)
            self.type_and_wait("//*[@id='login']", magentoPW) 
            self.wait_and_click("//*[@title='Login']")
            self.wait_for_page_to_load(60000)
        self.type_and_wait("//*[@id='filter_tax_postcode']", zipcode)
        self.press_enter("//*[@id='filter_tax_postcode']", 10)
#        self.click_and_wait("//*[@onclick='tax_rate_gridJsObject.doFilter()']")
        tax_rate = self.get_text("//td[contains(@class,'last')]") 
        tax_percentage = float(tax_rate) / 100.000
        price = float(line_items[0]) - float(line_items[2])
        tax = tax_percentage * price
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
        self.type_and_wait("//*[@id='filter_tax_postcode']", zipcode)
        time.sleep(5)
        self.press_enter("//*[@id='filter_tax_postcode']", 10)
        time.sleep(5)
        if not self.is_element_present("//td[contains(@class,'last')]"):
            return True
        return False
    
    def verify_web_tax(self, tax_url, state, city, zipcode, tax):
#        tax_url = 'http://www.bestplaces.net/economy/zip-code'
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
        self.sel.open(shop_admin_url)
        self.wait_for_element("//*[@id='username']", 20)
        if self.is_element_present("//*[@id='username']"):
            self.type_and_wait("//*[@id='username']", magentoUser)
            self.type_and_wait("//*[@id='login']", magentoPW) 
            self.wait_and_click("//*[@title='Login']")
            self.wait_for_page_to_load(45000)   
        self.wait_for_element("//*[@id='filter_real_order_id']", 60)
        self.type_and_wait("//*[@id='filter_real_order_id']", order_num)
        self.press_enter("//*[@id='filter_real_order_id']", 10)
#        self.sel.click("//*[@onclick='sales_order_gridJsObject.doFilter()']")
        while count < timeout:
            if self.sel.is_text_present("Total 1 records found"):
                count = timeout
                if line_items != []:
                    self.sel.click("//td[contains(text(),'%s')]" % order_num)
                    self.wait_for_page_to_load(30000)
                    if not self.is_text_present(line_items[1]):
                        return False
                self.wait_and_click("//a[@class='link-logout']") # logout or the next pass we will be stuck at the dashboard page
                return True
            time.sleep(1)
            count = count + 1
        return False
    
    def verify_order_ns(self, netsuite_url, cus_name, order_num, priority, carrier, nsUser, nsPW, timeout=300):
        count = 0
        found_it = False
        self.sel.open(netsuite_url)
        self.wait_for_element("//input[@name='email']", 20)
        if self.is_element_present("//input[@name='email']"):
            self.type_and_wait("//input[@name='email']", nsUser)
            self.type_and_wait("//input[@name='password']", nsPW) 
            self.wait_and_click("//input[@name='submitButton']")
            self.wait_for_page_to_load(45000)
        while count < timeout:
            if not self.is_text_present("Sales Order: "):
#            if not self.is_element_present("//a[@class='textwhitenolink']"):
#                if self.is_element_present("//input[@name='_searchstring']"):
                self.sel.refresh()
                time.sleep(5)
                self.type_and_wait("//input[@name='_searchstring']", order_num[:3])
                self.type_and_wait("//input[@name='_searchstring']", order_num)
                self.sel.click("//input[@id='_searchSubmitter']")
                time.sleep(2)
                count = count + 1
            else:
                found_it = True
                count = timeout
                self.run_ns_deployment_script()
        count = 0
        if found_it:
            self.type_and_wait("//input[@name='_searchstring']", order_num)
            self.sel.click("//input[@id='_searchSubmitter']")
            self.wait_for_element("//input[@id='continue']")
            if self.is_element_present("//input[@id='continue']"):
                self.sel.click("//input[@id='continue']")
            time.sleep(5)
            self.sel.click("//a[contains(text(),'View')]")
            time.sleep(30)
            self.refresh()
            self.sel.click("//*[@id='s_sysinfotxt']")
            time.sleep(10)
            if str(carrier).find('day'):
                carrier = carrier.replace('day','Day')#different string in NS than magento
            if self.sel.is_text_present(str(carrier)):
                count = 0
                priority_present = self.is_text_present(priority)
                while count < timeout:
                    log.info("is priority %s present? %s" % (priority, priority_present))
                    self.refresh()
                    self.click("//*[@id='s_sysinfotxt']")
                    time.sleep(10)
                    priority_present = self.is_text_present(priority)
                    if priority_present == True:
                        count = timeout
                        return True
                    count = count + 1   
                if self.is_text_present(priority):
                    return True            
        return False
    
    def run_ns_deployment_script(self, timeout=300):
        count = 0
        self.open('https://system.sandbox.netsuite.com/app/common/scripting/scriptrecordlist.nl?whence=')
        while count < timeout:
            if self.get_text("//tr[@id='row0']").find('Completed') >= 0:   
                if self.get_text("//tr[@id='row1']").find('Scheduled') >= 0 or self.get_text("//tr[@id='row1']").find('Completed') >= 0:
                    self.click_and_wait("//a[@class='dottedlink']")
                    time.sleep(5)
                    self.sel.mouse_over("//*[@class='bntBgB multiBnt']")
                    self.click_and_wait("//*[contains(@href,'submitexecute')]")
                    time.sleep(30)
                    count = timeout
                return True    
            else:
                count = count + 1
        return False
    
    def set_backorder(self, shop_admin_backorder_url, qty, magentoUser, magentoPW, timeout=20):
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
    
    def set_fraud(self, shop_admin_fraud_url, ip_address, magentoUser, magentoPW, timeout=20):
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
            if not self.sel.is_text_present("The configuration has been saved."):
                return False
            self.click_and_wait("//a[contains(text(),'Cache Management')]")
            self.click_and_wait("//*[contains(text(),'Flush Cache Storage')]")
            self.get_confirmation()
            time.sleep(5)
            self.click_and_wait("//a[@class='link-logout']") # logout or the next pass we will be stuck at the dashboard page
            count = count + 1
            return True
        return False
    
    def verify_order_st(self, smartturn_url, order_num, priority, carrier, smartturnUser, smartturnPW, timeout=20):
        count = 0
        loop = 0
        self.sel.open(smartturn_url)
        self.wait_for_element("//*[@id='username']", 20)
        self.type_and_wait("//*[@id='username']", smartturnUser)
        self.type_and_wait("//*[@id='password']", smartturnPW)
        time.sleep(10) 
        self.wait_and_click("//input[@class='button']")
        time.sleep(10)
        self.sel.click("//*[@id='outboundOrdersLink']")
        time.sleep(10) 
        found_page = self.is_text_present('Ship to customer')
        if found_page == False: # try again. sometimes that click doesn't work!
            self.sel.click("//*[@id='outboundOrdersLink']")
            time.sleep(10)
        while not self.sel.is_text_present(order_num) and loop < 20: 
            self.sel.refresh()
            time.sleep(30)
            loop = loop + 1
        if self.sel.is_text_present(order_num) == False:
            return (False, "did not find the order_num %s" % order_num) # give up if we still haven't found the order number       
        else:
            log.info("found the order_num %s" % order_num)
            self.sel.double_click("//*[contains(text(),'%s')]" % order_num)        
            time.sleep(10)
            order_info = self.get_text("//div[@class='extended_page-2-column-fields']")
            try:
                order_info = order_info[order_info.find('Priority'):order_info.find('Warehouse')]
            except:
                order_info = self.get_text("//div[@class='extended_page-2-column-fields']")
            log.info("looking for priority %s and carrier %s" % (priority, carrier))
            if self.sel.is_text_present(priority):
                if self.sel.is_text_present(carrier):
                    return (True, '')
                else:
                    return (False, "did not find the expected carrier: %s, but got this order info: %s" % (carrier, order_info))          
            else:
                return (False, "did not find the expected priority: %s, but got this order info: %s" % (priority, order_info))
            
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
            scripts_directory = os.getenv('TEST_HOME') + os.sep + "scripts" + os.sep
            script = scripts_directory + "file_upload.rb"
            if locator.find("id=") >= 0: # parse out the id of the locator ('id' is required for the script)
                idx1 = locator.find("id=") + 4
                idx2 = locator.find("']")
                locator = locator[idx1:idx2]
                log.debug(locator)
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
        if self.wait_for_element("link=Sign Out", 2) == True:
            self.sel.click("link=Sign Out")
            
    def type(self, locator, text, timeout=20):
        self.wait_for_element(locator, timeout)
        self.sel.type(locator, text)
        
    def right_click(self, locator):
        self.context_click(locator)
        
    def context_click(self, locator):
        self.wait_for_element(locator)
        self.sel.context_menu(locator)
            
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
            
    def is_selected(self, locator, timeout=20):
        self.wait_for_element(locator, timeout)
        if self.sel.get_value(locator) == 'on':
            return True
        else:
            return False
    
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
        
    def get_attribute(self, locator):
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
        '''internationalize it '''
        source = self.get_page_source().encode('utf-8')
        if source.find(text) >= 0:
            return True
        else:
            return False
        # return self.sel.is_text_present(text)
    
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

    def find_element_by_link_text(self, locator):
        return None # webdriverlib method
    
    def hover_over_element(self, locator):
        self.sel.mouse_over(locator)
    
    def hover_and_click(self, locator):
        self.sel.mouse_over(locator)
        self.click(locator)
        
    def switch_to_frame_by_id(self, id=''):
        pass # webdriver method
            
    def switch_to_frame(self, index=0):
        pass # webdriver method
    
    def switch_to_default_content(self):
        pass # webdriver method
    
    def get_page_source(self):
        return self.sel.get_html_source()
    
    def scroll_to_bottom(self):
        self.sel.get_eval("window.scrollTo(0, document.body.scrollHeight);")
        
    def maximize(self):       
        pass # webdriver method
        
    def do_javascript(self, script):
        ''' execute raw javascript '''
        return self.sel.get_eval(script)

            
class Selenium2(Thread):
    ''' used for a secondary selenium instance, when a test needs two '''    
    def __init__(self, args={}):
        Thread.__init__(self)
        self.running = False
        self.settings = args
        url = self.settings['url']
        test_host = self.settings['test_host']
        test_port = self.settings['test_port']
        browser = self.settings['browser']  
        log.info('init # 2')
        self.sel = selenium(test_host, int(test_port), browser, url)
    
    def get_selenium_client(self):
        return self.sel
                             
    def run(self):        
        try:
            log.info('selenium2 thread starting')
            self.running = True
            #===================================================================
            # self.sel.start()
            # while self.running == True:
            #    print 'sel2'
            #    time.sleep(5)
            # print 'selenium2 thread ending'
            #===================================================================
        except Exception as inst:
            log.error(inst)
    
    def stop(self):
        self.running = False
        self.sel.stop()
        
class AutoIt(Thread):
    ''' used for Windows native actions, requires AutoItX3 control registered in C:\Windows\system32 '''    
    def __init__(self, method, args={}):
        from win32com.client import Dispatch
        Thread.__init__(self)
        self.file_choosers = { "firefox" :'upload', "googlechrome": "Open", "iexplore": 'Upload', 'safari': "fuckifiknow"}
        self.autoit = Dispatch("AutoItX3.Control")
        self.autoit.Opt("WinTitleMatchMode", 2) # match any
        self.method = method
        self.args = args
        self.timeout = args.get('timeout', 10)
        self.autoit.opt("trayicondebug", 1)
        
    def get_file_chooser(self, browser="firefox"):
        if browser.find("firefox") >= 0:
            return self.file_choosers['firefox']
        elif browser.find("google") >= 0:
            return self.file_choosers['google']
        elif browser.find("*ie") >= 0 :
            return self.file_choosers['iexplore']
        elif browser.find("iexplore") >= 0 :
            return self.file_choosers['iexplore']
        elif browser.find("safari") >= 0:
            return self.file_choosers['safari']
        elif browser.find("*chrome") >= 0: # chrome but not googlechrome
            return self.file_choosers['firefox']
        else:
            return ''
               
    def run(self):        
        try:
            log.info('autoit thread starting')
            if self.method == "chooser":
                self.run_chooser(self.args)
            elif self.method == "file_download":
                self.run_file_download(self.args)
            log.info('autoit thread ending')
        except Exception as inst:
            log.error(inst)
            
    def run_file_download(self, args={}):
        self.autoit.WinWait("File Download", "", self.timeout)
        self.autoit.WinActivate("File Download")
        time.sleep(1)
        self.autoit.ControlClick("File Download", "", "[CLASS:Button; INSTANCE:2]")
    
    def run_chooser(self, args={}):
        try:
            browser = args.get('browser', 'iexplore')
            filename = args.get('filename', '')
            coordinates = args.get('coordinates', None)
            log.info("%s, %s" % (browser, filename))
            if filename == '':
                return
            else:
                chooser_name = self.get_file_chooser(browser)
                log.info('chooser_name = %s' % chooser_name)     
                if coordinates != None:
                    self.autoit.MouseClick("left", coordinates[0], coordinates[1])           
                self.autoit.WinWait(chooser_name, "", self.timeout)
                self.autoit.WinActivate(chooser_name)
                log.info('autoit waited')
                time.sleep(1)
                self.autoit.ControlSetText(chooser_name, "", "Edit1", filename)
                self.autoit.ControlSend(chooser_name, "", "Button2", "{ENTER}")
                log.info('autoit sent')
        except Exception as inst:
            log.error(inst)
        
class IEKiller(Thread):
    def __init__(self):
        Thread.__init__(self)
               
    # kill any IE instances
    def run(self):    
        cmd = "taskkill /IM iexplore.exe"
        try:
            time.sleep(2)
            self.process = subprocess.call(cmd.split())   # synchronous   
            time.sleep(2)
            log.info('*** all done %s' % cmd)                     
        except Exception as inst:
            log.error(inst)                    
    
    def stop(self):
        try:
            self.process.kill()
        except:
            pass
        