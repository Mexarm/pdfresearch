# pdfresearch

Search and extract text from PDF Files writes output to csv:

```
usage: pdfresearch.py [-h] [-c CODEC]
                      [--generate_usrmodule GENERATE_USRMODULE] [-o OUTPUT]
                      [--password PASSWORD] [--pagenos F [F ...]]
                      [--maxpages MAXPAGES] [--text_output]
                      [input] [user_module]
pdfresearch.py: error: positional arguments required [input] [user_module]
```

first generate an example user module:

```
$python pdfresearch.py --generate_usrmodule mysearch.py
```

and extract some text from the pdf with:

```
$python pdfresearch.py <your pdf file>.pdf --text_output --maxpages 4
```

now edit mysearch.py, adecuate it to your needs (use the text extracted in the previous step to create the regex):
you can test your regular expresions using this [online tool](http://pythex.org)

```
# search is a list of Search objects
search = [
    Search('P1',  # this is the label of this search

           # regular expresion capture groups are important to extract information,
           # capture groups en regular expresion are the values enclosed in (),
           #  you can practice on http://pythex.org
           r'(\d{5}|\d{4}).*Número de póliza\n(\w{5}\d{10})',

           flags=re.MULTILINE | re.DOTALL,  # optional: flags to pass to re.search

           # optional if you want to store a found value in a global store, this value can be used later on other search output
           # { 'your-key' : lambda groups: groups[index]}
           # then it can be used in other search like this self.context['your-key']
           store_actions={'p1_poliza': lambda grps: grps[1]},

           # optional specify how to build the output csv row
           # in this case the label, filename, page, and 2 values captured by the regular expresion are used
           output_map=lambda self: (self.label, self.context['file'], self.context['page'], self.groups[1], self.groups[0])),
]
```

and then run the search:

```
$python pdfresearch.py <your pdf file>.pdf mysearch
```

(note: not .py extension in user_module [mysearch])

example output:

```
"P1","my.pdf","0","XXXXX0000543308","9920"
"P2","my.pdf","1","XXXXX0000543308",""
"P3","my.pdf","2","XXXXX0000543308",""
"P4","my.pdf","3","XXXXX0000543308",""
```
