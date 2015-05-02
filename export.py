import os
import sys
import re
import datetime
import time
import json
import csv

admins = ['leg']

def main():
    # Check arguments
    if len(sys.argv) < 2:
        print("You must pass the log directory as a command line argument.")
        exit(1)
    log_directory = sys.argv[1]

    if not os.path.isdir(log_directory):
        print("The path provided is not a directory.")
        exit(1)

    # Holds all the quotes
    quotes = {}
    deleted_quotes = []

    # Regex
    regex = {
        'filename': re.compile(r'(?P<yyyy>\d\d\d\d)-(?P<mm>\d\d)-(?P<dd>\d\d)\.log'),
        'quote_add': re.compile(r'\[(?P<hh>\d\d):(?P<mm>\d\d):(?P<ss>\d\d)\] <Quotes> '
                                r'\[Quote\] Added quote #(?P<id>\d*) by (?P<author>\S+)'),
        'quote_meta': re.compile(r'\[(?P<hh>\d\d):(?P<mm>\d\d):(?P<ss>\d\d)\] <Quotes> '
                                 r'\[Quote\] #(?P<id>\d*) added by (?P<author>\S+) '
                                 r'((?P<weeks>\d*) weeks? )?'
                                 r'((?P<days>\d*) days? )?'
                                 r'((?P<hours>\d*) hours? )?'
                                 r'((?P<minutes>\d*) minutes? )?'
                                 r'((?P<seconds>\d*) seconds? )?ago.'),
        'quote_text': re.compile(r'.+\[Quote\] (?P<quote>.*)\n'),
        'quote_delete': re.compile(r'.+ <' + '|'.join(admins) + r'> .quote del (?P<id>\d*)\n'),
        'color_codes': re.compile(r'[\x02\x1F\x0F\x16]|\x03(\d\d?(,\d\d?)?)?|\x08', re.UNICODE)
    }

    for filename in sorted(os.listdir(log_directory)):
        filename_match = regex['filename'].match(filename)
        if filename_match:
            with open(os.path.join(log_directory, filename)) as f:
                while 1:
                    line = f.readline()
                    if not line:
                        break

                    # Match regex
                    quote_add_match = regex['quote_add'].match(line)
                    quote_meta_match = regex['quote_meta'].match(line)
                    quote_delete_match = regex['quote_delete'].match(line)

                    if quote_add_match or quote_meta_match:
                        if quote_add_match:
                            quote_match = quote_add_match

                            # Parse the quote time
                            quote_datetime = datetime.datetime(
                                int(filename_match.group('yyyy')),
                                int(filename_match.group('mm')),
                                int(filename_match.group('dd')),
                                int(quote_add_match.group('hh')),
                                int(quote_add_match.group('mm')),
                                int(quote_add_match.group('ss'))
                            )

                            # Get the quote timestamp
                            quote_timestamp = int(time.mktime(quote_datetime.timetuple()))

                        elif quote_meta_match:
                            quote_match = quote_meta_match

                            # Parse the command response time and date
                            print_datetime = datetime.datetime(
                                int(filename_match.group('yyyy')),
                                int(filename_match.group('mm')),
                                int(filename_match.group('dd')),
                                int(quote_meta_match.group('hh')),
                                int(quote_meta_match.group('mm')),
                                int(quote_meta_match.group('ss'))
                            )

                            # Parse the time ago
                            time_ago = datetime.timedelta(
                                seconds=int(quote_meta_match.group('seconds') or 0),
                                minutes=int(quote_meta_match.group('minutes') or 0),
                                hours=int(quote_meta_match.group('hours') or 0),
                                days=int(quote_meta_match.group('days') or 0),
                                weeks=int(quote_meta_match.group('weeks') or 0)
                            )

                            # Get the quote timestamp
                            quote_timestamp = int(time.mktime((print_datetime-time_ago).timetuple()))


                        # Get the quote ID
                        quote_id = int(quote_match.group('id'))

                        # Remove from deleted quotes
                        try:
                            deleted_quotes.remove(quote_id)
                        except ValueError:
                            pass

                        # Retrieve and strip formatting codes from the quote text
                        quote_text = regex['quote_text'].match(f.readline()).group('quote')
                        quote_text = regex['color_codes'].sub('', quote_text)

                        # Create quote object
                        quotes[quote_id] = {
                            'id': quote_id,
                            'date': quote_timestamp,
                            'author': quote_match.group('author'),
                            'text': quote_text
                        }

                    # Check if quote was deleted by one of the admins
                    elif quote_delete_match:
                        quote_id = int(quote_delete_match.group('id'))
                        deleted_quotes.append(quote_id)

    # Filter quotes
    filtered_quotes = {key: value for (key, value) in quotes.items() if key not in deleted_quotes}

    # Write CSV file
    with open('quotes.csv', 'w') as csvfile:
        csvwriter = csv.DictWriter(csvfile, fieldnames=['id', 'date', 'author', 'text'])
        csvwriter.writeheader()
        for key, quote in filtered_quotes.items():
            csvwriter.writerow(quote)

    # Write JSON file
    with open('quotes.json', 'w') as jsonfile:
        json.dump(filtered_quotes, jsonfile, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    main()
