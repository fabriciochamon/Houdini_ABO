import hou
import sqlite3, requests, os
from pathlib import Path

db_file = hou.text.expandString('$ABO/db/abo.db')

# get entries in the database
def get_all(where='', records_per_page=36, page=1):
	global db_file

	with sqlite3.connect(db_file) as conn:
		conn.row_factory = lambda cursor, row: {col[0] : row[i] for i,col in enumerate(cursor.description)}
		cursor = conn.cursor()

		offset = (page-1)*records_per_page
		if where.strip() != '':

			# search specific field
			if ":" in where:
				field = where.split(':')[0].strip()
				where = where.split(':')[1].strip()
				cursor.execute(f'SELECT * FROM listings WHERE {field} LIKE ? LIMIT ? OFFSET ?', 
								(
									'%'+where+'%', 
									records_per_page, 
									offset
								)
							)

			# search everywhere
			else:
				cursor.execute('SELECT * FROM listings WHERE item_keywords LIKE ? OR material LIKE ? OR product_type LIKE ? OR color LIKE ? OR fabric_type LIKE ? OR finish_type LIKE ? OR style LIKE ? LIMIT ? OFFSET ?', 
								(
									'%'+where+'%', 
									'%'+where+'%', 
									'%'+where+'%', 
									'%'+where+'%', 
									'%'+where+'%', 
									'%'+where+'%', 
									'%'+where+'%', 
									records_per_page, 
									offset
								)
							)
		else:
			cursor.execute('SELECT * FROM listings LIMIT ? OFFSET ?', (records_per_page, offset))

		records = cursor.fetchall()

	return records

# retrieve images (thumbnails) from amazon cdn or from local cached data
def get_or_download_image(image_id, image_res=128):
	
	image = f'{image_id}._US{image_res}_.jpg'
	local_filename = hou.text.expandString(f'$ABO/thumbs/{image}')

	# check cached image exists
	if os.path.isfile(local_filename):
		ret = local_filename

	# otherwise download it
	else:
		file_url = f'https://m.media-amazon.com/images/I/{image}'
		response = requests.get(file_url, stream=True)
		
		ret = None
		if response.status_code == 200:
			os.makedirs(os.path.dirname(local_filename), exist_ok=True)
			
			with open(local_filename, 'wb') as f:
				for chunk in response.iter_content(chunk_size=8192):
					f.write(chunk)

			ret = local_filename
		else:
			# use placeholder image if image url not found
			ret = hou.text.expandString('$ABO/thumbs/noimage.jpg')

	return ret

		

