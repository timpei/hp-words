import sys
import epub
import codecs
import xmltodict
import json

def extract_text(xmldata):
	text = []
	ps =  xmldata['html']['body']['div']['p']

	for paragraph in ps:
		if '#text' in paragraph:
			text.append(paragraph['#text'])
		elif 'span' in paragraph and '#text' in paragraph['span']:
			text.append(paragraph['span']['#text'])
	return text

file = sys.argv[1]
out = codecs.open('out.txt', 'w', 'utf-8')
book = epub.open_epub(file)

chapters = []

for item in book.opf.manifest.values():
	if not 'Section' in item.identifier:
		continue
	print item.identifier

	try:
		data = book.read_item(item)
	except KeyError:
		continue

	try:	
		xmldata = xmltodict.parse(data)
		print xmldata
		chapters.append(extract_text(xmldata))

	except UnicodeDecodeError:
		continue

chapters = chapters[3:]
out.write(json.dumps(chapters, indent=4))
# for chapter_num, chapter in enumerate(chapters):
# 	for para_num, para in enumerate(chapter):
# 		for sentence_num, sentence in enumerate(para_num.split('.')):
# 			for word_num, word in enumerate(word)
