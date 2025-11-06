# ------------------------------------------------------------------------------------------ #
# THIS SCRIPT CREATES A SINGLE JSON FILE BASED ON ALL LISTINGS INCLUDED IN "abo-listings.tar"
# (IT WILL IGNORE PRODUCTS THAT DON'T HAVE A 3D MODEL ASSOCIATED)
# ------------------------------------------------------------------------------------------ #
import json, csv

# THE FOLDER CONTAINIG EXTRACTED ORIGINAL LISTINGS JSONS
listings_root_folder = 'C:/Users/Fabricio/Downloads/abo-listings/listings/metadata'

# WHICH KEYS TO INCLUDE IN THE FINAL JSON ? (will be fields on the sqlite table)
keys = [
	'item_id',
	'item_name',
	'item_shape',
	'brand',
	'bullet_point',
	'color',
	'color_code',
	'country',
	'domain_name',
	'fabric_type',
	'finish_type',
	'pattern',
	'item_keywords',
	'main_image_id',
	'other_image_id',
	'spin_id',
	'material',
	'model_name',
	'node',
	'product_type',
	'product_description',
	'style',
	'3dmodel_id',
]


def get_data(d, k, separator='\n'):

	if k in ['item_keywords', 'node', 'other_image_id']: separator=','

	ret = None
	if k in d.keys():
		ret = d[k]
		ret_orig = ret
		if isinstance(ret, list):
			# en_US lang values takes precedence over all other languages
			if 'language_tag' in ret[0]:
				ret = separator.join([item['value'] for item in ret if item['language_tag'].lower()=='en_us' and item['value'].strip()!=''])
				if ret.strip()=='':
					ret = ret_orig[0]['value']
			else:
				ret = [item for item in ret if item is not None]
				try:
					if isinstance(ret[0], dict): ret = [item['value'] for item in ret]
				except:
					if isinstance(ret[0], dict): ret = [item['node_name'] for item in ret]

				ret = [item for item in ret if item is not None]
				ret = separator.join(ret)
				
			# ignore unicode chars
			ret = ret.encode('ascii', 'ignore').decode('ascii')

	if ret is None: ret = ''

	return ret


listings_files = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
products = []
csv_file = '3dmodels.csv'
with open(csv_file, newline='') as csvfile:
	csv_reader = list(csv.reader(csvfile, delimiter=','))

for listing_file in listings_files:
	json_file = listings_root_folder+f'/listings_{listing_file}.json'
	print (f'READING: {json_file}')
	with open(json_file, 'r') as f:
		lines = f.readlines()
		for i, line in enumerate(lines):
			print (f'LINE: {i+1} of {len(lines)}')
			data = json.loads(line)

			if '3dmodel_id' in data.keys():
				product = {}
				for k in keys:
					label = k
					# rename this field as sqlite does not allow table fields to start with numbers
					if label == '3dmodel_id': label = 'model_id'
					
					product[label] = get_data(data, k)

				# get 3d model path from csv (this is the path to extract the model inside "abo-3dmodels.tar")
				for row in csv_reader:
					if row[0]==product['model_id']:
						product['model_path'] = row[1]

				products.append(product)

print('writing final listings json:')

products_file = 'listings.json'
with open(products_file, 'w') as f:
	json.dump(products, f, indent=2)

print('---- DONE ----')


