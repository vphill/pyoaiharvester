pyoaiharvester
==============

Simple command line oai-pmh harvester written in Python.

Usage
-----

Harvest a repository to a file named untsw.dc.xml

```
python pyoaiharvest.py -l http://digital.library.unt.edu/explore/collections/UNTSW/oai/ -o untsw.dc.xml
```

Harvest the untl metadata format to a file named untsw.untl.xml

```
python pyoaiharvest.py -l http://digital.library.unt.edu/explore/collections/UNTSW/oai/ -o untsw.untl.xml -m untl
```

Options
-----  

**-f**  
**--from**  
&nbsp;&nbsp;&nbsp;&nbsp; harvest records from this date, format: yyyy-mm-dd  

**-l**  
**_--link_**  
&nbsp;&nbsp;&nbsp;&nbsp; URL of repository  

**-m**  
**--mdprefix**  
&nbsp;&nbsp;&nbsp;&nbsp; use the specified metadata format, default="oai_dc"  

**-o**  
**--filename**  
&nbsp;&nbsp;&nbsp;&nbsp; write repository to file  

**-s**  
**--setName**  
&nbsp;&nbsp;&nbsp;&nbsp; harvest the specified set  

**-u**  
**--until**  
&nbsp;&nbsp;&nbsp;&nbsp; harvest records until this date, format: yyyy-mm-dd  
