#! /usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Invoice Objects for Invoice Generator
(invoiceObjects.py)

Author: Samuel Searles-Bryant
Date created: 2016-09-09

This module contains the python objects for the Invoice Generator program:
Invoice
InvoiceEntry
CustomerAccount
NoInputError (Exception)

Last updated: 2016-09-10
'''
# Required packages

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
        #invoiceNumber = '{:0=3d}'.format(self.getNumber()) # get the next invoice number as 3 digit long string

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
        selection = input("\nPlease select a customer account: ").lower()

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
                selection = input(">> ")

def tryInput(prompt):
    '''
    Requests raw input from the user. Raises NoInputError if no input is entered.
    '''

    userInput = input(prompt)
    if userInput == "":
        raise NoInputError
    return userInput

def numInput(prompt):
    '''
    Requests a number as input from the user. Raises NoInputError if no input is entered or input is not a number.
    '''

    userInput = input(prompt)
    try:
        userInput = float(userInput)
    except ValueError:
        raise NoInputError
    assert type(userInput) == float
    return userInput

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
    import logging
    if error:
        logging.error("{} is not available in this version.".format(featureName))
    else:
        logging.warning("{} is still in development.".format(featureName))


##### END OF SUBROUTINES #####


if __name__ == "__main__":
    # Tests

    pass
