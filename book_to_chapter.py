import sys
import epub
import codecs
import json
import xmltodict
import nltk

import sqlite3

#TODO
# lemmatization of words
# lowercase of words


# takes xml dictionary and get text arrays (paragraphs)
def extract_text(xmldata):
	# stores paragraphs
	text = []

	# traverses through dict to all the paragraphs with potential relevant text
	# note: currently ignoring header tags
	ps =  xmldata['html']['body']['div']['p']

	for paragraph in ps:
		if '#text' in paragraph:
			text.append(paragraph['#text'])
		elif 'span' in paragraph and '#text' in paragraph['span']:
			text.append(paragraph['span']['#text'])

	# some unicode symbols can be replaced by ascii-compatible characters
	# this helps with the NLP later
	text = [x.replace(u'\u00ad', '')	# word-wrap hyphens
			 .replace(u'\u2019', "'")
			 .replace(u'\u201c', '"')	# opening quotes
			 .replace(u'\u201d', '"')	# ending quotes
			 .replace(u'\u2014', '-')
			 .replace(u'\u2026', '...') for x in text]
	return text

file = sys.argv[1]
book = epub.open_epub(file)

db_conn = sqlite3.connect('data.db')
c = db_conn.cursor()
c.execute('''
		CREATE TABLE IF NOT EXISTS sentences
		(
		sentence_id INT,
		sentence TEXT,
		sentence_index INT,
		paragraph INT, 
		chapter INT, 
		title TEXT,
		PRIMARY KEY (sentence_id, title)
		)
	''')
c.execute('''
		CREATE TABLE IF NOT EXISTS words
		(
		word_id INT,
		word TEXT, 
		word_index INT, 
		sentence_id INT, 
		chapter INT, 
		title TEXT, 
		part_of_speech TEXT,
		PRIMARY KEY (word_id, title)
		)
	''')

chapters = []

epub_manifest_items = book.opf.manifest.values()
cover_page_xml = xmltodict.parse(book.read_item(epub_manifest_items[0]))
title = cover_page_xml['ncx']['docTitle']['text']

for item in epub_manifest_items:
	if not 'Section' in item.identifier:
		continue
	print item.identifier

	try:
		data = book.read_item(item)
	except KeyError:
		continue

	try:	
		xmldata = xmltodict.parse(data)
		chapters.append(extract_text(xmldata))

	except UnicodeDecodeError:
		continue

chapters = chapters[3:]
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

sentence_count = 0
word_count = 0
for chapter_num, chapter in enumerate(chapters):
	for para_num, para in enumerate(chapter):
		for sentence_num, sentence in enumerate(tokenizer.tokenize(para)):
			c.execute('INSERT INTO sentences VALUES (?, ?, ?, ?, ?, ?)', (sentence_count, sentence, sentence_num, para_num, chapter_num, title))
			words = nltk.word_tokenize(sentence)
			for word_num, word in enumerate(nltk.pos_tag(words)):
				c.execute('INSERT INTO words VALUES (?, ?, ?, ?, ?, ?, ?)', (word_count, word[0], word_num, sentence_count, chapter_num, title, word[1]))
				word_count += 1
			sentence_count += 1
db_conn.commit()
db_conn.close()




