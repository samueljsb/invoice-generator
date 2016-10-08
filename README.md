# Invoice Generator
_by Samuel J. Searles-Bryant, last updated 2016-09-16._

A Python script to generate PDF invoices from a LaTeX template.

This program contains the following files:

* invoiceGenerator.py
* invoiceTemplate.tex

The script will create a 'config' file and 'customers.json' during the first time it is run.

## Dependencies
- Python 3+.
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
