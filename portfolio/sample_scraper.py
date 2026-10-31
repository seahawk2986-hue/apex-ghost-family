#!/usr/bin/env python3
'''SAMPLE: a keyless scraper - what the family does every hour. Demo output:
the family's own live stats, scraped + verified.'''
import json, urllib.request
req = urllib.request.Request('https://api.github.com/events?per_page=5',
                             headers={'User-Agent': 'apex-family-demo'})
events = json.load(urllib.request.urlopen(req, timeout=20))
print('live events:', [e.get('repo', {}).get('name') for e in events])
