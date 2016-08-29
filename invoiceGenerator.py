#! /usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Invoice Generator
(invoiceGenerator.py)

Author: Samuel Searles-Bryant
Date created: 2016-02-22

Last updated: 2016-08-07

N.B.    This program requires pdflatex.
'''

VERSION = "v0.3.4"

# Import modules
import json, csv, shelve # for opening/saving files and data
import sys, subprocess # for running system operations
import os, shutil # for manipulating files
import logging
import re
logging.basicConfig(level=logging.DEBUG, format='- %(levelname)s - %(message)s') # config logging messages

# Logging options
logging.disable(logging.INFO) # disable all log messages for DEBUG and INFO
#logging.disable(logging.CRITICAL) # disable *all* log messages

# Options
CURRENCY = "GBP" # N.B. this does not yet affect functionality
titleWidth = 50 # width of title bars
pathToSave = os.path.expanduser('~/Dropbox/Invoices/')# set destination directory of generated invoices
pathToCSV = os.path.expanduser('~/Desktop/invoiceData.csv')

# Check we're using python2. If not, create raw_input function. (creating this for python2 would break it)
if sys.version_info[0] > 2:
    def raw_input(prompt):
        '''
        Allows use of deprecated raw_input function in Python3+
        '''
        return input(prompt)

##### Define custom classes #####

class NoInputError(Exception):
    '''
    Exception for when no input is entered.
    '''

    pass


class CustomerAccount(object):
    '''
    Representation of a customer account. Contains customer information.
    '''

    def __init__(self,accountName,name,address,number):
        """
        Initialization function, saves the customer information as attributes.

        accountName: the account code for this customer (string)
        name: The full name of the customer (string)
        address: the full address, lines separated by '\\\\' for TeX (string)
        number: the number of invoices previously issued to this customer (int)
        """

        self.accountName = accountName
        self.name = name
        self.address = address
        self.number = number

    def getAccountName(self):
        '''
        Returns the accountName attribute of the customer account.
        '''

        return self.accountName

    def getName(self):
        '''
        Returns the name attribute of the customer account.
        '''

        return self.name

    def getAddress(self):
        '''
        Returns the address attribute of the customer account.
        '''

        return self.address

    def getNumber(self):
        '''
        Returns the number attribute of the customer account.
        '''

        return self.number
    
    def resetNumber(self):
        '''
        Resets the invoice number if an invoice is cancelled
        '''
    
        self.number -= 1

    def nextInvoiceCode(self,LaTeX=True):
        '''
        Increments the number attribute and returns an invoice code formatted for TeX (raw string) formatted for plain text (string), and the filename for the PDF (string).
        '''

        self.number += 1
#        invoiceNumber = '{:0=3d}'.format(self.getNumber()) # get the next invoice number as 3 digit long string

        invoiceCode = r"\textsc{{{accountName}}}--{number:0=3d}".format(**self.JSONdump())
        plainInvoiceCode = "{accountName}_{number:0=3d}".format(**self.JSONdump())
        filename = "invoice_{accountName}_{number:0=3d}".format(**self.JSONdump())

        return invoiceCode, plainInvoiceCode, filename

    def JSONdump(self):
        '''
        Returns the customer account attributes to be saved in a JSON file (dict)
        '''

        return {'accountName':self.getAccountName(), 'number':self.getNumber(), 'name':self.getName(), 'address':self.getAddress()}


class InvoiceEntry(object):
    '''
    Representation of an entry on an invoice. Contains ID, description, rate and quantity information.
    '''

    def __init__(self,id=None,description=None,rate=None,qty=None):
        '''
        Initialization function
        
        self, description: str
        rate, qty: float
        '''

        if (not id) | (not description) | (not rate) | (not qty): # if something missing, collect it
            print( "\nNew Fee (leave blank to skip)" )

        if id == None:
            id = tryInput("ID: ")
        if description == None:
            description = tryInput("Description: ")
        if rate == None:
            rate = float(numInput("Rate: "))
        if qty == None:
            qty = float(numInput("Quantity: "))

        assert (type(rate) == float) & (type(qty) == float) # check qty and rate are numbers

        amount = rate * qty

        self.id, self.description, self.rate, self.qty, self.amount = id, description, rate, qty, amount

    def getID(self):
        '''
        Returns the ID attribute of the fee.
        '''

        return self.id

    def getDescription(self):
        '''
        Returns the description attribute of the fee.
        '''

        return self.description

    def getRate(self):
        '''
        Returns the rate attribute of the fee.
        '''

        return self.rate

    def getQty(self):
        '''
        Returns the quantity attribute of the fee.
        '''

        return self.qty

    def getAmount(self):
        '''
        Returns the amount attribute of the fee.
        '''

        return self.amount

    def getAllInfo(self):
        '''
        Returns all entry info in a dictionary (dict)
        '''
        
        return {'id':self.id,'description':self.description,'rate':twoDP(self.rate),'qty':self.qty,'amount':twoDP(self.amount)}


class Invoice(object):
    '''
    Representation of an invoice
    '''

    def __init__(self,customerAccounts,accountName=None):
        """
        Initialization function.

        customerAccounts: dictionary of CustomerAccount objects
        accountName: pre-selected customer account name (string)
        """
        
        assert not customerAccounts == {}
        
        print( "New invoice" )
        self.customer = selectCustomer(customerAccounts,accountName)
        self.invoiceCode, self.plainInvoiceCode, self.filename = self.customer.nextInvoiceCode()
        self.entries = []
        self.subTotal = 0.
        self.shipping = 0.
        self.showShipping = False
        self.discount = 0.
        self.showDiscount = False

    def getCustomer(self):
        '''
        Returns the customer attribute of the invoice (CustomerAccount object)
        '''

        return self.customer

    def getSubTotal(self):
        '''
        Returns the sub total attribute of the invoice object (float)
        '''

        return self.subTotal

    def getShipping(self):
        '''
        Returns the shipping attribute of the invoice object (float)
        '''
        
        return float(self.shipping)

    def getShippingLine(self):
        '''
        Returns the shipping attribute of the invoice object in a string formatted for the TeX table (string) is showShipping == True
        '''
        
        if self.showShipping:
            return r"Shipping: & \pounds{{{}}}\\".format(twoDP(self.shipping))
        else:
            return ""

    def getDiscount(self):
        '''
        Returns the discount attribute of the invoice object (float)
        '''

        return self.discount

    def getDiscountLine(self):
        '''
        Returns the shipping attribute of the invoice object in a string formatted for the TeX table (string)
        '''
        
        if self.showDiscount:
            return r"Discount: & \pounds{{{}}}\\".format(twoDP(self.discount))
        else:
            return ""

    def getTotal(self):
        '''
        Returns the total amount to pay for the invoice object (float)
        '''

        total = self.subTotal + self.shipping - self.discount
        return total

    def getEntries(self):
        '''
        Returns the entries attribute of the invoice (list of InvoiceEntry objects)
        '''

        return self.entries

    def getEntry(self,index):
        '''
        Returns the entry 'index' from the entries attribute of the invoice (InvoiceEntry object)
        '''

        return self.entries[index]

    def addEntry(self,entry):
        '''
        Adds an entry (InvoiceObject object) to the entries attribute and updates the sub total.
        '''

        self.entries.append(entry)
        self.subTotal += entry.getAmount()
        
        print( "(new entry: £{})".format(twoDP(entry.getAmount())) )
    
    def addShipping(self,shippingCost):
        '''
        Adds an amount to the shipping total (float)
        '''
    
        self.showShipping = True
        self.shipping += shippingCost

    def addDiscount(self,discount):
        '''
        Adds an amount to the discount total (float)
        '''
            
        self.showDiscount = True
        self.discount += discount

    def getInvoiceCode(self,latex=True):
        '''
        Returns the invoice number attribute of the invoice (string).
        If latex == True (default), this is formatted for LaTeX
        '''
        if latex:
            return self.invoiceCode
        else:
            return self.plainInvoiceCode

    def getFilename(self):
        '''
        Returns the customer attribute of the invoice (CustomerAccount object)
        '''

        return self.filename


##### FUNCTIONS #####
def selectCustomer(customerAccounts,selection=None):
    '''
    Requires the user to select a customer from the set of customer accounts.

    customerAccounts: dictionary of CustomerAccount objects

    Returns a CustomerAccount object selected by the user.
    '''
    
    if selection is None: # if no selection has been provided already
        selection = raw_input("\nPlease select a customer account: ").lower()

    while True:
        if selection == "-ls": # method to list account names
            print( "All customer accounts:" )
            customers = list(customerAccounts.keys()) # get a list of customer account names
            customers.sort() # sort the list alphabetically
            for customer in customers:
                print( customerAccounts[customer].getAccountName() ) # print account names
        else:
            try:
                customer = customerAccounts[selection.lower()]
                return customer
            except:
                print( "There is no account by that name. Please try again. (Type -ls to get a list of available accounts)" )
                selection = raw_input(">> ")

def tryInput(prompt):
    '''
    Requests raw input from the user. Raises NoInputError if no input is entered.
    '''

    input = raw_input(prompt)
    if input == "":
        raise NoInputError
    return input

def numInput(prompt):
    '''
    Requests a number as input from the user. Raises NoInputError if no input is entered or input is not a number.
    '''

    input = raw_input(prompt)
    try:
        input = float(input)
    except ValueError:
        raise NoInputError
    assert type(input) == float
    return input

def addressInput():
    '''
    Requests an address from the user. If no address is given on first line, raises NoInputError. A blank line ends the address.
    Returns an address (string) formatted for LaTeX.
    '''

    inputAddress = ""
    print( "What is the address?" )
    try: # ensure some input is given
        inputAddressLine = tryInput(">> ")
        inputAddress += inputAddressLine
    except NoInputError:
        print( "No address. Returning to main menu." )
        raise NoInputError
        
    try: # ensure some input is given
        while True:
            inputAddressLine = tryInput(">> ")
            inputAddress += r"\\ "
            inputAddress += inputAddressLine
    except NoInputError: # when input left blank, end address
        pass

    return inputAddress

def phoneInput():
    '''
    Requests a phone number from the user. Formats the phone number appropriately and returns it (string).
    If the input is not a phone number, raises NoInputError.
    '''
    inDevelopment('phone number input')
    return tryInput("Phone number: ")

def emailInput():
    '''
    Requests an email address from the user. ensures appropriate formatand returns it (string).
    If the input is not a valid email address, raises NoInputError.
    '''
    inDevelopment('email address input')
    return tryInput("Email address: ")


def generateInvoice(invoice):
    '''
    Process an invoice and generate the PDF using LaTeX.

    invoice: the invoice to be generated (Invoice object)
    '''

    print( "\nGenerating invoice..." )
    
    if len(invoice.getEntries()) == 0:
        raise NoInputError

    numOfEntries = 0
    invoiceInfo = r"\newcommand\subtotal{{{}}}\newcommand\discount{{{}}}\newcommand\shipping{{{}}}\newcommand\grandtotal{{{}}}\newcommand\invoiceInfo{{".format(twoDP(invoice.getSubTotal()),invoice.getDiscountLine(),invoice.getShippingLine(),twoDP(invoice.getTotal()))
    for entry in invoice.getEntries(): # for each invoice entry
        invoiceInfo += r"{id} & {description} & {rate} & {qty} & {amount} \\".format(**entry.getAllInfo())
        numOfEntries += 1
    while numOfEntries < 10: # add padding: make sure there are at least 10 entries, so the invoice table isn't too short (because that looks weird)
        invoiceInfo += r"&~\n~&&&\\"
        numOfEntries += 1
    invoiceInfo += "}"

    # Create directory for temporary files
    try:
        os.makedirs(os.path.join('TEMPfiles'))
    except OSError:
        logging.critical("The TEMPfiles directory already exists. This needs to be deleted before an invoice can be generated.")
        raise OSError("[Errno 17] Directory exists: 'TEMPfiles'")

    # Write TEMPinvoiceNumber.tex
    latexFile = open(os.path.join('TEMPfiles',"TEMPinvoiceNumber.tex"),'w')
    latexFile.write(invoice.getInvoiceCode(latex=True))
    latexFile.close()

    # Write TEMPcustomerAddress.tex
    latexFile = open(os.path.join('TEMPfiles',"TEMPcustomerAddress.tex"),'w')
    latexFile.write(invoice.getCustomer().getName() + r"\\" + invoice.getCustomer().getAddress())
    latexFile.close()

    # Write TEMPinvoiceInfo.tex
    latexFile = open(os.path.join('TEMPfiles',"TEMPinvoiceInfo.tex"),'w')
    latexFile.write(invoiceInfo)
    latexFile.close()

    # Write TEMPconfig.tex
    configData = shelve.open('config')
    userInfo = (configData['userName'],configData['userAddress'],configData['userPhoneNumber'],configData['userEmail'],configData['accountNumber'],configData['sortCodeFormatted'])
    configInfo = r"\newcommand\myName{{{userName}}}\newcommand\myAddress{{{userAddress}}}\newcommand\myPhoneNumber{{{userPhoneNumber}}}\newcommand\myEmail{{{userEmail}}}\newcommand\accountNumber{{{accountNumber}}}\newcommand\sortCode{{{sortCodeFormatted}}}".format(**configData)
    configData.close()

    latexFile = open(os.path.join('TEMPfiles',"TEMPconfig.tex"),'w')
    latexFile.write(configInfo)
    latexFile.close()

    ## Create PDF
    # Create temporary LaTeX file for invoice
    shutil.copyfile('invoiceTemplate.tex',os.path.join('TEMPfiles',"TEMPinvoice.tex"))

    # Run pdflatex on temporary LaTeX file
    os.chdir("./TEMPfiles")
    runLaTeX = subprocess.Popen(['pdflatex','TEMPinvoice'],stdout=subprocess.PIPE)
    runLaTeX.wait()
    os.chdir("../")

    ## Clean up files
    # Set filename as invoice_<customer>_<number> and copy to Dropbox
    shutil.copyfile('TEMPfiles/TEMPinvoice.pdf',os.path.join(pathToSave,invoice.getFilename()+'.pdf'))
    logging.debug('PDF moved to '+os.path.join(pathToSave,invoice.getFilename()+'.pdf'))

    # Delete temporary files
    shutil.rmtree('TEMPfiles')

    print( "Invoice generated successfully! ({}.pdf for £{})".format(invoice.getFilename(), twoDP(invoice.getTotal())) )

    # Save Invoice object in binary file
    # N.B. Not in this version. Will be updated to save each customer account as one binary file with invoices
#    print( "Saving invoice object..." )
#    try:
#        shelfFile = shelve.open(os.path.join('shelved_invoices',invoice.getFilename()))
#        shelfFile['invoice'] = invoice
#        shelfFile.close()
#        print( "Invoice object saved!" )
#    except:
#        logging.error("Operation failed. This invoice object was not saved.")

def printUnderline(text,char="-",width=0):
    '''
    Prints text with underline to correct length
    char: character to use for underline (str)
    width: width of underlined text (int)
    '''

    text = text.center(width)
    print('',text,char*len(text),sep='\n')

def twoDP(num):
    '''
    Takes a number as an input (num: float or int) and returns a string of the number formatted to 2 decimal places
    '''

    return '{0:.2f}'.format(num)

def inDevelopment(featureName="This feature",error=False):
    if error:
        logging.error("{} is not available in this version.".format(featureName))
    else:
        logging.warning("{} is still in development.".format(featureName))


##### END OF SUBROUTINES #####

##### MENUS #####

def newInvoiceMenu(invoice):
    '''
    Menu for processing a new invoice.

    invoice: Invoice object
    '''
    printUnderline("Invoice menu ({})".format(invoice.getInvoiceCode(latex=False)))
    print("""1: Add an entry
    \r2: Add entries from a CSV file
    \r3: Add shipping costs
    \r4: Add a discount
    \r5: Generate the invoice
    \rdel: Return to main menu (without creating an invoice)""")
#    \rexit: Save and return to main menu""") # save and return not in this version

    while True:
        menuChoice = raw_input(">> ")

        if menuChoice == '1': # new entry

            try:
                newEntry = InvoiceEntry()
                invoice.addEntry(newEntry)
            except NoInputError:
                print( "No input given. Please try again." )

            break # return to invoice menu

        elif menuChoice == '2': # add entries from csv
            
            print( "Importing data from csv file..." )

            with open(pathToCSV) as csvFile:
                entryData = csv.reader(csvFile)
                next(entryData, None) #skip header
                for row in entryData:
                    newEntry = InvoiceEntry(id=row[0],description=row[1],rate=float(row[2]),qty=float(row[3]))
                    invoice.addEntry(newEntry)
        
            print( "Entries successfully added!" )

            break # return to invoice menu
          
        elif menuChoice == '3': # add shipping
          
          try:
              newShipping = numInput("\nShipping cost (£): ")
              invoice.addShipping(newShipping)
          except NoInputError:
              print( "No input given. Please try again." )
              
          break # return to invoice menu
              
        elif menuChoice == '4': # add discount
          
          try:
              newDiscount = numInput("\nDiscount (£): ")
              invoice.addDiscount(newDiscount)
          except NoInputError:
              print( "No input given. Please try again." )
          
          break # return to invoice menu

        elif menuChoice == '5': # generate invoice
            try:
                generateInvoice(invoice)
            except NoInputError:
                logging.error("There are no entries in this invoice. The invoice was not generated.")
                break # return to invoice menu
                    
            return # to main menu

        elif menuChoice == '0' or menuChoice.lower() == 'exit': # save and return to main menu
            inDevelopment('Save and return',error=True)
            print( "Invoice discarded." )
            return # to main menu

        elif menuChoice.lower() == 'del': # return to main menu
            invoice.getCustomer().resetNumber()
            print( "Invoice discarded." )
            return # to main menu

        else:
            print( "That is not a valid choice. Please try again:" )

    return newInvoiceMenu(invoice)

def configUtil():
    '''
    Configuration utility
    '''

    printUnderline("Configuration")
    
    try:
        userName = tryInput("User name: ")
        userAddress = addressInput()
        userPhoneNumber = phoneInput()
        userEmail = emailInput()
        accountNumber = tryInput("Account number: ")
        sortCodeRegex = re.compile(r'\d{6}')
        while True: # make sure sort code is 6 digits long (so can be formatted xx--xx--xx)
            sortCode = tryInput("Sort code: ")
            try:
                assert sortCode in sortCodeRegex.search(sortCode).group()
                break
            except:
                print( "This is not a valid sort code. Please try again" )
        sortCodeFormatted = "{}--{}--{}".format(sortCode[0:2],sortCode[2:4],sortCode[4:6])
    except NoInputError:
        print( "No input... \nNo config file has ben created." )
        return

    logging.info("Creating config binary file...")
    configData = shelve.open('config')
    configData['userName'] = userName
    configData['userAddress'] = userAddress
    configData['userPhoneNumber'] = userPhoneNumber
    configData['userEmail'] = userEmail
    configData['accountNumber'] = accountNumber
    configData['sortCode'] = sortCode
    configData['sortCodeFormatted'] = sortCodeFormatted
    configData.close()
    logging.info("Config binary file created")


##### Main Thread #####

if __name__ == "__main__":

    os.chdir(os.path.dirname(__file__)) # cd to the location of this python file (and associated data files)
    os.system('clear')

    print( "%"+"-"*(titleWidth-2)+"%" )
    print( "Invoice Generator".center(titleWidth) )
    print( "%"+"-"*(titleWidth-2)+"%" )
    print( "{}{}".format(VERSION.ljust(titleWidth-len(CURRENCY)), CURRENCY) )
    
    assert(not os.path.exists('TEMPfiles/')) # make sure there are no left over TEMPfiles

    ## Congifuration
    if not os.path.exists('config'):
        print( "No configuration information found. Running configUtil..." )
        configUtil()
    else:
        configData = shelve.open('config')
        print( "Welcome, {userName}!".format(**configData) )
        configData.close()


    ## Import customer data
    print( "\nLoading cutomer data..." )
    customerAccounts = {} # dictionary of customer accounts

    if not os.path.exists('customers.json'): # if no customer data, create a file
        print( "There is no customer data. A new file will be created." )
        newFile = open("customers.json",'w')
        newFile.close()
    else:
        jsonFile = open("customers.json",'r')
        customerData = json.load(jsonFile)
        jsonFile.close()
        for account in customerData: # build dictionary of CustomerAccount objects. NB: keys are lowercase!
            customerAccounts[customerData[account]['accountName'].lower()] = CustomerAccount(customerData[account]['accountName'],customerData[account]['name'],customerData[account]['address'],customerData[account]['number'])

        print( "Customer data loaded successfully!" )

    ## Main menu

    while True:
        printUnderline("Main Menu",char="=",width=15)
        print("""1: New invoice
        \r2: New customer
        \r3: Edit existing invoice
        \r4: Run config util
        \rexit: Save and exit""")

        while True:
            menuChoice = raw_input(">> ")
            if menuChoice == '1': ## New invoice
                
                if customerAccounts == {}:
                    print( "There are no customers registered. Please register a customer before trying to generate an invoice")
                    break

                newInvoice = Invoice(customerAccounts)
                newInvoiceMenu(newInvoice)

                break # return to main menu

            elif menuChoice == '2': ## New customer
                printUnderline( "\nNew customer" )
                try:
                    # Ask for customer name
                    inputName = tryInput("What is the new customer's name? ")

                    # Ask for customer address
                    inputAddress = addressInput()

                    # Ask for account code
                    inputAccountCode = tryInput("Please enter an account code for this customer: ")

                    # Create new customer account
                    customerAccounts[inputAccountCode] = CustomerAccount(inputAccountCode,inputName,inputAddress,0)
                    print( "Successfully created new customer account: {}".format(inputAccountCode) )
                except NoInputError:
                    break

                break # return to main menu

            elif menuChoice == '3': ## Edit existing invoice

                inDevelopment('Edit existing invoice',error=True)

                break # return to main menu

            elif menuChoice == '4': ## Run config util
                
                configUtil()

                break # return to main menu

            elif menuChoice == '0' or menuChoice.lower() == 'exit': ## Save and exit
                print( "\nSaving data..." )

                # Create dictionary for JSON file
                dataToSave = {}
                for account in customerAccounts:
                    dataToSave[customerAccounts[account].getAccountName()] = customerAccounts[account].JSONdump()

                # Save data to JSON file
                jsonFile = open("customers.json", 'w+')
                jsonFile.write(json.dumps(dataToSave))
                jsonFile.close()

                print( "Data saved!" )
                print( "Goodbye!\n" )
                exit() # exit program

            else:
                    print( "That is not a valid choice. Please try again:" )
