Try directly in:

[![Binder](http://mybinder.org/badge.svg)]

GOTO: ~/prog/google_apps_accounts/gssis/utilities
MAIN FILE:
csvreader_udea.py

Convert a csv file obtained with the export feature of the profiles of
google scholar into another csv with additional info about
Insitutional Research Groups, Insitutional authors,
National/International type of the publication, issn, and Colciencias 
journal ranking.

To just update the output file, set flag update=True in main program

Donwload newcitations.csv and upload to google docs with conversion set on. 
Copy and paste in Articulos.

From now on, it could be enough to export the articles form google scholar only for the last year,
only the new citations will be updated.

The last update log is in newcitationslog_2016_01.py


Check the implementation in the pycitations notebook and specially in csvreader_udea.ipynb


