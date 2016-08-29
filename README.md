# Invoice Generator
_by Samuel J. Searles-Bryant, last updated 2016-08-01._

A Python script to generate PDF invoices from a LaTeX template.

This program contains the following files:
  
* invoiceGenerator.py
* invoiceTemplate.tex

The script will create a 'config' file and 'customers.json' during the first time it is run.

## Dependencies
- Python 3+ (the script should be compatible with Python 2.7, but this is not guaranteed).
- Python packages: `json`, `csv`, `shelve`, `sys`, `subprocess`, `os`, `shutil`, `logging`, `re`.
- A working installation of LaTeX; uses pdfLaTeX to generate the document.
- LaTeX packages: `array`, `xcolor`, `fontenc`, `multicol`, `longtable`. These should be packaged with most LaTeX distributions.

### Localisation
- Currently written for UK users (GBP and A4 paper)

## Notes
- The invoice will be saved in the location specified by `pathToSave` (line 33). This is set by default to _~/Dropbox/Invoices/_.
- The file name will be *invoice\_\[accountCode\]\_\[number\]*.
- The path to the csv file to import entries from is specified by `pathToCSV` (line 44). This is set by default to _~/Desktop/invoiceData_.
- This script works on Mac OS X 10.11.5. I have not tested it on Windows

### Upcoming features
- Create option to allow other localisations (e.g. USD and letter paper)


### MIT licence
Copyright (c) 2016 Samuel J. Searles-Bryant

<sub>Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:</sub>

<sub>The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.</sub>

<sub>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.</sub>
