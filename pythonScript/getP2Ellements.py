# How to use: Python 2.7

from __future__ import print_function
import pandas as pd
import urllib
import simplejson
import sys
import re

# Read csv from input (input unqualified.csv here)
df = pd.read_csv(sys.argv[1])

# Make a new csv file for storing updated elements
# a+: append
# w+: write (plus means it will create a file if not exist)
f = open('/Users/nammeo/Desktop/Vaadin/Projects/web-components-testing/generated-files/updatedElements.csv', 'w+')

# Define a regex for Polymer 2 version which will match these (>=2.0.0-rc.2 <3.0; ^2.0.0; 1.9 - 2; ^1.0.0 || ^2.0.0, 2.0.0, ^2, ^2.0.2, 2.0.0-rc.3, 1 - 2)
polymer2Regex = r"(\^2)|(\-\s*2)|(2\.)"

print('There is a total of %d elements to check' % (len(df)))

# Loop through each row
for index, row in df.iterrows():

	# Define a bool if the element is a Polymer 2 element
	p2 = False

	# Skip already read elements (in case errno54: Connection reset by peer)
	# if index < 572: continue

	# To keep track the progress
	print('%d %s %s' % (index, row['repo'], row['owner']))

	# Generate API link
	metadataURL = 'https://webcomponents.org/api/meta/%s/%s' % (row['owner'], row['repo'])
	#metadataURL = 'https://webcomponents.org/api/meta/vaadin/vaadin-grid'

	try:
		# Open the URL
		response = urllib.urlopen(metadataURL)

		# Load JSON
		jsonData = simplejson.loads(response.read())
	except simplejson.scanner.JSONDecodeError:
		print('No valid JSON!')
		continue


	if 'bower' in jsonData:
		if 'dependencies' in jsonData['bower']:
				if 'polymer' in jsonData['bower']['dependencies']:
					polymerVer = jsonData['bower']['dependencies']['polymer']
					if re.search(polymer2Regex, polymerVer):
						if 'version' in jsonData['bower']:
							f.write(',{0},,{1},{2}\n'.format(row['repo'],row['owner'], jsonData['bower']['version']))
						else:
							f.write(',{0},,{1},{2}\n'.format(row['repo'],row['owner'], row['version']))
						p2 = True
					else:
						continue
				else:
					continue
		else:
			continue
	else:
		continue

	if p2:
		print('^^^')