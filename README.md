py-selenium-layers
tom lichtenberg
july 17, 2012
==================

  abstraction layer for python selenium providing a common api between Selenium RC and WebDriver
  
   pysel-webtest is the main entry point to the py-selenium-layers project
   
   the purpose of py-selenium-layers is to be able to run the same tests
   using either Selenium RC or WebDriver, based on a command-line switch.
   
   it often seems to be the case that some websites work better with one
   version of Selenium than the other. this project makes it easy to switch
   between the two competing versions of Selenium (using their python bindings)
   
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