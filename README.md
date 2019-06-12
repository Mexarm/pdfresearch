# pdfresearch

Search and extract text from PDF Files writes output to csv:

```
usage: pdfresearch.py [-h] [-c CODEC]
                      [--generate-usermodule GENERATE_USRMODULE] [-o OUTPUT]
                      [--password PASSWORD] [--pagenos F [F ...]]
                      [--maxpages MAXPAGES] [--extract-text]
                      [input] [user_module]
pdfresearch.py: error: positional arguments required [input] [user_module]
```

first generate an example user module:

```
$python pdfresearch.py --generate-usermodule mysearch.py
```

and extract some text from the pdf with:

```
$python pdfresearch.py <your pdf file>.pdf --extract-text --maxpages 4
```

now edit mysearch.py, adecuate it to your needs (use the text extracted in the previous step to create the regex):
you can test your regular expresions using this [online tool](http://pythex.org)

```
import re

from research import Search

# search is a list of Search objects
search = [
    Search('DEMOGRAFICO',  # this is the label of this search

           # regex list, regular expresion capture groups are important to extract information,
           # capture groups in regular expresion are the values enclosed in (),
           #  you can test your patterns on http://pythex.org
           # this regex match the text Apreciable <name>:\n\nBienvenido captures the name of the subject
           [r'Apreciable\s(.*)\:\n\n\¡Bienvenido\!'],

           flags=re.MULTILINE,  # optional: flags to pass to re.search

           # optional if you want to store a found value in a global store, this value can be retrieved by any next Search instance
           # like this self.context[key], key also can be a lambda expresion returning the key for example:
           # store_actions = { lambda grps : grps[0][1] : lambda grps: grps[0][0]}
           store_actions={'last_matched_name': lambda grps: grps[0][0]},

           # optional specify how to build the output csv row
           # in this case the label, filename, page, and 2 values captured by the regular expresion are used
           output_map=lambda self: (
               self.label, self.context['file'], self.context['page'], self.groups[0][0], '')
           ),
    # another example
    Search('POLIZA',
           [r'NUMERO\sDE\sPOLIZA\n([A-Z0-9]+)\n', r'SEGURO\sDE\sHOSPITALIZACIÓN',
            r'\n\n(.*)\n\w{4}\d{6}(?:[\w\d]{3}|\n)'],
           flags=re.MULTILINE,
           output_map=lambda self: (
               self.label, self.context['file'], self.context['page'], self.groups[2][0], self.groups[0][0])
           ),
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
