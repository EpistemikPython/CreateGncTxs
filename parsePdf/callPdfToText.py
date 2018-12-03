
import os, subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
args = ["/usr/local/bin/pdftotext",
        '-enc',
        'UTF-8',
        "{}/my-pdf.pdf".format(SCRIPT_DIR),
        '-']
res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output = res.stdout.decode('utf-8')
