'''
   pysel-webtest is the main entry point to the py-selenium-layers project,
   a python abstraction layer for Selenium
   
   the purpose of py-selenium-layers is to be able to run the same tests
   using either Selenium RC or WebDriver, based on a command-line switch
   it often seems to be the case that some websites work better with one
   version than the other. this project makes it easy to switch between
   the two competing versions of Selenium (using their python bindings)
   
   by default, the WebDriver lib will be used to run Selenium
   to use Selenium RC instead, pass "-w false" as a command-line argument. e.g.:
       python pysel-webtest.py -w false
   
   by default, the application expects a selenium server to be running on localhost:444
   to use a different selenium server, pass "-s host:port" as a command-line argument. e.g:
        python pysel-webtest.py -s 10.2.0.6:4001
   
   by default, the application uses the firefox browser
   to use a different browser, pass "-b browser_name" as a command-line argument. e.g:
         python pysel-webtest.py -b *googlechrome
         
   by default, the application initializes the browser with http://www.google.com
   to use a different initial url, pass "-u url" as a command-line argument. e.g:
        python pysel-webtest.py -u http://my.yahoo.com
'''
import sys
import time
import optparse
from weblib import WebLib
from webdriverlib import WebDriverLib

class PyWebTest:
    
    def __init__(self):
        self.settings = {}
        self.lib = None
        self.url = "http://www.google.com"
      
    def setup(self, args):
        ''' main entry point from command-line '''
        parser = optparse.OptionParser()
        parser.add_option('-b', '--browser', default="*firefox", type='string')
        parser.add_option('-s', '--selenium_server', default="localhost:4444", type='string')
        parser.add_option('-u', '--url', default="http://www.google.com", type='string')
        parser.add_option('-w', '--webdriver', default='true', type='string')   
        options, args_out = parser.parse_args(args)
        sel_server = options.selenium_server.split(":")
        if len(sel_server) == 1:
            self.settings['test_host'] = sel_server[0]
            self.settings['test_port'] = '4444'
        else:
            self.settings['test_host'] = sel_server[0]
            self.settings['test_port'] = sel_server[1]
        self.settings['webdriver'] = self.str2bool(options.webdriver) 
        self.settings['url'] = options.url
        self.settings['browser'] = options.browser         
        self.lib = self.init_selenium()
        
    def str2bool(self, v):
        '''convert string to boolean '''
        return v.lower() in ("yes", "true", "t", "1")

    def init_selenium(self):
        if self.settings['webdriver'] == False:
            lib = WebLib(None, self.settings) 
        else:
            lib = WebDriverLib(self.settings)
        lib.start_selenium()
        return lib
    
    def test_web(self):
        try:
            self.lib.open(self.url)
            found = self.lib.wait_for_element("//input[@id='gbqfq']")
            if found == False:
                print('did not find the google input element')
            else:
                print('found the google input element')
                self.lib.type_and_wait("//input[@id='gbqfq']", "Python Selenium")
                found_text = self.lib.wait_for_text("Python Selenium - Stack Overflow")
                if found_text == False:
                    print 'did not find the expected text: "Python Selenium - Stack Overflow"'
                else:
                    print 'found the expected text: "Python Selenium - Stack Overflow"'
            time.sleep(2)
        except Exception as inst:
            print inst
        finally:
            self.lib.stop_selenium(False) # False => no screenshot
    
    
if __name__ == "__main__":
    ptest = PyWebTest()
    ptest.setup(sys.argv[1:])
    ptest.test_web()