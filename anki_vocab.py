import shutil
import code
import os
import sqlite3
import json
import sys
import re
from datetime import datetime


def main():
    os.chdir('D:/anki_script')
    websters_dic = parse_webster()
    known_word_dic = parse_master_vocab()
    new_word_dic = parse_kindle_db(websters_dic,known_word_dic)
    master_dic = organizer(new_word_dic)
    writer(master_dic)
# Read in local device websters dictionary json file


def parse_webster():
    with open('english_dictionary.json','r') as f:
        websters_dic = json.loads(f.read())
        for word in websters_dic:
            websters_dic[word.lower()] = websters_dic[word].replace('\n','')
    return websters_dic

# Read in local device master vocab, which is a log of all previously looked up words


def parse_master_vocab():
    known_word_dic = {}

    # Read in csv, created known word dictionary
    with open('master_vocab.csv', 'r', encoding = 'utf-8-sig') as vocab_file:
        for row in vocab_file:
            try:
                row = row.replace('\n', '')
                known_word_dic[row.split('|', 1)[0]] = row.split('|' , 1)[1]
            except IndexError:
                # code.interact(local=locals())
                continue

    return known_word_dic


def parse_kindle_db(websters_dic,known_word_dic):
    os.chdir('D:/system/vocabulary')
    new_word_dic = {}
    # SQL commands to parse kindle db

    conn = sqlite3.connect('vocab.db')
    c = conn.cursor()
    word_list = c.execute('select WORDS.word, WORDS.stem , LOOKUPS.usage, LOOKUPS.timestamp, BOOK_INFO.title, BOOK_INFO.authors '
                          'from LOOKUPS '
                          'inner join BOOK_INFO on BOOK_INFO.id = LOOKUPS.book_key '
                          'inner join WORDS on WORDS.id = LOOKUPS.word_key').fetchall()

    # Sample row:
    # ('autonomous', 'autonomous',
    #  'COMPOSITION OF HOUSEHOLDS HEADED BY PROPRIETORS IN 1827, BY RELIGIOUS STATUS OF HOUSEHOLDERS Perhaps more than any other act, the removal of workmen from the homes of employers created an autonomous working class. ',
    #  1460433293466, "A Shopkeeper's Millennium: Society and Revivals in Rochester, New York, 1815-1837",
    #  'Johnson, Paul E.'), ('communicants', 'communicant',
    #   'But in every church, men increased their proportion of the communicants during revivals, indicating that revivals were family experiences and that women were converting their mean.28 In 1830-31 fully 65 percent of male converts were related to prior members of their churches (computed from surnames within congregations). ',
    #  1460433832186,
    # "A Shopkeeper's Millennium: Society and Revivals in Rochester, New York, 1815-1837",
    # 'Johnson, Paul E.'),

    for row in word_list:
        word = row[0].lower()
        sentence = row[2]
        book_title = re.sub('[\W_]+', '_', row[4])
        author = row[5]
        try:
            if word not in known_word_dic.keys():
                word_def = websters_dic[word].strip('\n')
                new_word_dic[word] = u'{0}|{1}|{2}|{3}|{4}'.format(word_def, sentence, book_title, author, book_title)
        except KeyError as e:
            try:
                word_def = websters_dic[word[:-1].strip('\n')]

            except KeyError as e:
                try:
                    word_def = websters_dic[word[:-2].strip('\n')]
                    continue

                except KeyError as e:
                    try:
                        word_def= websters_dic[word[:-3].strip('\n')]
                        continue
                    except:
                        # Go use online API at this point
                        # r = requests.get('http://api.wordnik.com/v4/words.json/{0}?api_key=)
                        print('could not find {0}'.format(word))

    os.chdir('D:/anki_script')
    return new_word_dic


def organizer(new_word_dic):
    master_dic = {}
    # Master dic layout dic[book_title] = list of new words[]
    # {
    # 'catcher_in_the_rye':   ['str_definition_1',str_definition_2'],
    # 1984':                  ['str_definition_1',str_definition_2']
    # }
    with open('master_vocab.csv', 'a+', encoding='utf-8-sig') as vocab_file:
        for word in new_word_dic:
            # Add new words to master_vocab
            vocab_file.write('{0}|{1}\n'.format(word, new_word_dic[word]))

            row = new_word_dic[word].split('|')
            book_title = row[4]

            try:
                master_dic[book_title].append('{0}|{1}'.format(word,new_word_dic[word]))

            except KeyError as e:
                master_dic[book_title] = []
                master_dic[book_title].append('{0}|{1}'.format(word, new_word_dic[word]))

    return master_dic


def writer(master_dic):
    for book in master_dic:
        with open('{0}_{1}anki.csv'.format(datetime.now().strftime('%Y%m%d_%H%M%S'), book), 'w',
                  encoding='utf-8-sig') as vocab_file:
            for row in master_dic[book]:
                vocab_file.write('{0}\n'.format(row))

main()
