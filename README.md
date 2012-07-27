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
