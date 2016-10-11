#! /usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Invoice Generator
(invoiceGenerator.py)

Author: Samuel Searles-Bryant
Date created: 2016-02-22

Last updated: 2016-10-07

N.B.    This program requires pdflatex.
'''

VERSION = "v0.3.5"

# Import modules
import json, csv # for opening/saving files and data
import sys, subprocess # for running system operations
import os, shutil # for manipulating files
import logging
import re
from invoiceObjects import *

# Logging options
logging.basicConfig(level=logging.DEBUG, format='- %(levelname)s - %(message)s') # config logging messages
logging.disable(logging.INFO) # disable all log messages for DEBUG and INFO
#logging.disable(logging.CRITICAL) # disable *all* log messages

# Options
CURRENCY = "GBP" # N.B. this does not yet affect functionality
titleWidth = 50 # width of title bars
pathToSave = os.path.expanduser('~/Dropbox/Invoices/')# set destination directory of generated invoices
pathToCSV = os.path.expanduser('~/Desktop/invoiceData.csv')

# Check we're using Python3
try:
    assert sys.version_info[0] >= 3
except:
    print("This program will only run using Python 3.")

##### Define method for generating invoice #####
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
    while numOfEntries < 8: # add padding: make sure there are at least 8 entries, so the invoice table isn't too short (because that looks weird)
        invoiceInfo += r"&~\n~&&&\\"
        numOfEntries += 1
    invoiceInfo += "}"
    logging.debug("invoiceInfo: "+invoiceInfo[100:])

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
    logging.debug("TEMPinvoiceNumber written")

    # Write TEMPcustomerAddress.tex
    latexFile = open(os.path.join('TEMPfiles',"TEMPcustomerAddress.tex"),'w')
    latexFile.write(invoice.getCustomer().getName() + r"\\" + invoice.getCustomer().getAddress())
    latexFile.close()
    logging.debug("TEMPcustomerAddress written")

    # Write TEMPinvoiceInfo.tex
    latexFile = open(os.path.join('TEMPfiles',"TEMPinvoiceInfo.tex"),'w')
    latexFile.write(invoiceInfo)
    latexFile.close()
    logging.debug("TEMPinvoiceInfo written")

    # Write TEMPconfig.tex
    logging.debug("Opening config")
    configFile = open('config.json','r')
    configData = json.load(configFile)
    userInfo = (configData['userName'],configData['userAddress'],configData['userPhoneNumber'],configData['userEmail'],configData['accountNumber'],configData['sortCodeFormatted'])
    configInfo = r"\newcommand\myName{{{userName}}}\newcommand\myAddress{{{userAddress}}}\newcommand\myPhoneNumber{{{userPhoneNumber}}}\newcommand\myEmail{{{userEmail}}}\newcommand\accountNumber{{{accountNumber}}}\newcommand\sortCode{{{sortCodeFormatted}}}".format(**configData)
    logging.debug("configInfo collected")
    configFile.close()
    logging.debug("config file closed")

    latexFile = open(os.path.join('TEMPfiles',"TEMPconfig.tex"),'w')
    latexFile.write(configInfo)
    latexFile.close()
    logging.debug("TEMPconfig written")

    ## Create PDF
    # Create temporary LaTeX file for invoice
    shutil.copyfile('invoiceTemplate.tex',os.path.join('TEMPfiles',"TEMPinvoice.tex"))
    logging.debug("TEMPinvoice created")

    # Run pdflatex on temporary LaTeX file
    os.chdir("./TEMPfiles")
    logging.debug("cd to ./TEMPfiles")
    logging.debug("Running LaTeX...")
    runLaTeX = subprocess.Popen(['pdflatex','TEMPinvoice'],stdout=subprocess.PIPE)
    runLaTeX.wait()
    logging.debug("LaTeX ran.")
    os.chdir("../")

    ## Clean up files
    # Set filename as invoice_<customer>_<number> and copy to Dropbox
    logging.debug("Cleaning up")
    shutil.copyfile('TEMPfiles/TEMPinvoice.pdf',os.path.join(pathToSave,invoice.getFilename()+'.pdf'))
    logging.debug('PDF moved to '+os.path.join(pathToSave,invoice.getFilename()+'.pdf'))

    # Delete temporary files
    shutil.rmtree('TEMPfiles')

    print( "Invoice generated successfully! ({}.pdf for £{})".format(invoice.getFilename(), twoDP(invoice.getTotal())) )


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
        menuChoice = input(">> ")

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
    configData = {}
    configData['userName'] = userName
    configData['userAddress'] = userAddress
    configData['userPhoneNumber'] = userPhoneNumber
    configData['userEmail'] = userEmail
    configData['accountNumber'] = accountNumber
    configData['sortCode'] = sortCode
    configData['sortCodeFormatted'] = sortCodeFormatted

    # Save data to JSON file
    jsonFile = open("config.json", 'w+')
    jsonFile.write(json.dumps(configData))
    jsonFile.close()

    logging.info("Config JSON file created")


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
    if not os.path.exists('config.json'):
        print( "No configuration information found. Running configUtil..." )
        configUtil()
    else:
        jsonFile = open("config.json",'r')
        configData = json.load(jsonFile)
        jsonFile.close()
        print( "Welcome, {userName}!".format(**configData) )


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
            menuChoice = input(">> ")
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
