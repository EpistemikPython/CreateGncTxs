
from tika import parser

raw = parser.from_file('sample.pdf')
print(raw['content'])
