import sys
import csv
from os import path
from glob import glob
import argparse

from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams

EXAMPLE_USER_MODULE = r"""
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
"""


def convert_pdf_to_txt(path, settings):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams()
    device = TextConverter(
        rsrcmgr, retstr, codec=settings.codec, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = settings.password
    maxpages = settings.maxpages
    caching = True
    pagenos = set(settings.pagenos)
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
        interpreter.process_page(page)
        txtpage = retstr.getvalue()
        retstr.truncate(0)
        retstr.seek(0)
        yield txtpage
    fp.close()
    device.close()


def parsed_args():
    parser = argparse.ArgumentParser(
        description="busca expresiones regulares en el texto de archivos PDF, la busqueda se realiza en cada pagina")
    parser.add_argument(
        'input', nargs='?', help="PDF file to read (it could be a pattern like ~/path/*.pdf)")
    parser.add_argument('user_module', nargs='?',
                        help="user module name (do not include .py)")
    parser.add_argument("-c", "--codec",
                        help="codec (default ascii)", default='ascii')
    parser.add_argument("--generate-usermodule",
                        help="generate a user module example in the specified file")
    parser.add_argument("-o", "--output", type=argparse.FileType('w'),
                        help="output file name (default: stdout)", default=sys.stdout)
    parser.add_argument('--password', default='',
                        help='password to open the pdf file if required')
    parser.add_argument('--pagenos', metavar='F', type=int, nargs='+',
                        help="lista de paginas", default=[])
    parser.add_argument('--maxpages', type=int,
                        help="maximo numero de paginas a procesar (default: 0 -todas las paginas-)", default=0)
    parser.add_argument('--extract-text', action='store_true',
                        help='output page text and do not evaluate user expressions')
    args = parser.parse_args()
    if args.input:
        args.files = glob(path.expanduser(args.input))

    if args.generate_usermodule:
        with open(args.generate_usermodule, 'w') as handle:
            handle.write(EXAMPLE_USER_MODULE)
        parser.exit()
    elif args.extract_text and args.input:
        return args
    elif not (args.input and args.user_module):
        parser.error('positional arguments required [input] [user_module]')
    return args


def main():
    args = parsed_args()
    of = args.output
    w = csv.writer(of, quotechar='"', quoting=csv.QUOTE_ALL)
    usrmodule = None
    search = None
    if args.user_module:
        usrmodule = __import__(args.user_module)
        assert hasattr(usrmodule, 'search')
        search = usrmodule.search
    global_context = dict()
    for file in args.files:
        args.file = file
        for pnum, txtpage in enumerate(convert_pdf_to_txt(file, args)):
            pageno = args.pagenos[pnum] if args.pagenos else pnum

            if args.extract_text:
                of.write(f'@file: {file}\n')
                of.write(f'@page: {pageno}\n')
                of.write(('-' * 10)+'\n')
                of.write(txtpage)
            else:
                for s in search:
                    context = dict(
                        page=pageno,
                        file=file,
                        text=txtpage,
                        args=args
                    )
                    context.update(global_context)
                    s.search(txtpage, context=context)
                    if not s.groups is None:
                        if s.store_actions:
                            global_context.update(s.get_store_values())
                        w.writerow(s.output_map())
                        of.flush()
                        break
    of.close()


if __name__ == '__main__':
    main()
