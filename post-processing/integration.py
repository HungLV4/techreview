from dateutil import parser
import sys
import unicodedata
import json
import distance
import locale

abre_list = [u"WIFI + 3G", u"WI FI + 3G", u"3G + WIFI", u"3G + WI FI",
			u"WIFI + CELLULAR", u"WI FI + CELLULAR", u"CELLULAR + WIFI", u"CELLULAR + WI FI",
			u"CDMA", u"GSM", u"WIFI", u"WI-FI", u"WI FI", u"4G", 
			u"3G", u"CELLULAR", u"VERIZON", u"ATT", u"AT T", "GENERATION", u"GEN"]

gen_list = [{u"1ST":u"1"}, {u"2ND": u"2"}, {u"3RD": u"3"}, {u"4TH": u"4"}, {u"5TH":u"5"},
			{u"6TH":u"6"}, {u"7TH":u"7"}, {u"8TH":u"8"}, {u"9TH":u"9"}]

punc_tbl = dict((i, u" " ) for i in xrange(sys.maxunicode) if unicodedata.category(unichr(i)).startswith('P'))

def standardize(input_str):
	# lower case all character
	input_str = input_str.upper()

	# replace all punctuation by whitespace
	input_str = input_str.translate(punc_tbl)

	for abre in abre_list:
		input_str = input_str.replace(abre, "")

	for gen in gen_list:
		for key, value in gen.iteritems():
			input_str = input_str.replace(key, value)

	return input_str.strip()

def grams(input_str):
	words = input_str.split()
	results = []

	for word in words:
		for i in range(len(word)):
			results += [word[i : i + n] for n in xrange(1, len(word) - (i - 1))]

	return results

def ngrams(input_str, n):
	words = input_str.split()
	results = []
	for word in words:
		if len(word) >= n:
			results += [word[i:i+n] for i in range(len(word) - (n - 1))]
		elif n > 0:
			results += ngrams(word, n - 1)

	return results

def readData(inputFile):
	locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

	with open(inputFile) as data_file:
		data = json.load(data_file)
	if "product" in data[0].keys():
		data = [e for e in data if e["product"] == "Cellphones" or e["product"] == "Tablets"]

	results = {}

	data_by_brand = {}
	for entry in data:
		brand = standardize(entry["brand"])
		if brand not in data_by_brand.keys():
			data_by_brand[brand] = [entry]
		else:
			data_by_brand[brand].append(entry)

	for brand in data_by_brand.keys():
		results[brand] = []

		devices = sorted(data_by_brand[brand], key=lambda k: standardize(k['name']))

		while len(devices) > 0:
			device = devices[0]
			del(devices[0])

			device["std_name"] = standardize(brand + " " + device["name"])
			
			stats = [locale.atoi((device["stats"])[i]) for i in range(len(device["stats"]))]
			del(device["stats"])
			device["hit"] = sum(stats)
			
			while len(devices) > 0:
				ref_device = devices[0]
				ref_name = standardize(ref_device["name"])

				d = distance.jaccard(ref_name.split(), device["std_name"].split())
				if d == 0:
					del(devices[0])
					if "another_name" not in device.keys():
						device["another_name"] = [ref_device["name"]]
					else:
						device["another_name"].append(ref_device["name"])
				else:
					break
			
			results[brand].append(device)

	return results

if __name__ == '__main__':
	# read data
	pa_data = readData('../data/phonearena.json')
	ga_data = readData('../data/gsmarena.json')
	en_data = readData('../data/engadget.json')

	# mapping
	with open('data/devices.json', 'w') as fp:
		keys = en_data.keys()

		fp.write('{"results": [')
		for key in en_data.keys():			
			en_devices = en_data[key]

			ga_devices = None
			if key in ga_data.keys():
				ga_devices = ga_data[key]
			
			pa_devices = None
			if key in pa_data.keys():
				pa_devices = pa_data[key]

			for device in en_devices:

				name = device["std_name"]

				dt = parser.parse("1990-05-25T00:00:00", fuzzy=True)
				if "released" in device.keys() and device["released"] != "":
					dt = parser.parse(device["released"], fuzzy=True)
				device["released"] = {}
				(device["released"])["iso"] = dt.strftime('%Y-%m-%dT%H:%M:%S')
				(device["released"])["__type"] = "Date"

				device["searchable_name"] = grams(name)

				device["images"] = [device["images"]]
				device["thumbnail"] = [device["thumbnail"]] 

				if ga_devices != None:
					for ga in ga_devices:
						if ga["std_name"] == name:
							for k in ga.keys():
								if k in device.keys():
									if not isinstance(device[k], basestring):
										device[k] += ga[k]
								else:
									device[k] = ga[k]
							break

				if pa_devices != None:
					for pa in pa_devices:
						if pa["std_name"] == name:
							for k in pa.keys():
								if k in device.keys():
									if not isinstance(device[k], basestring):
										device[k] += pa[k]
								else:
									device[k] = pa[k]
							break

				out = json.dumps(device)
				fp.write(out + ',\n')
		fp.write(']}')