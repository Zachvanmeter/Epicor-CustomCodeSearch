# Epicor-CustomCodeSearch
SQL Tool which querries custom BPM and Customization code to aid diagnositics for specific tables or fields

In order to use this, ensure your windows user has permission to access the SQL server
Download Python 3.6+ and pyodbc if needed. 
run this program using >>>python "CustomCodeSearch.py"
REPLACE the server and database options with the hardware name of your server and the specific server you want to parse

use the lower left field for your primary search criteria like OrderNum, and use the second for an additional rule, like OrderDtl. This search would return all BPMs and Customizations that have both OrderNum and OrderDtl in them at some point, or OrderNum but NOT OrderDtl if you toggle the &! box before searching

Please Contact me if you have any questions
