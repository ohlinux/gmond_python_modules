###  This script reports aniwar game metrics to ganglia.
###
###  License to use, modify, and distribute under the GPL
###  http://www.gnu.org/licenses/gpl.txt

import time
import urllib
import subprocess
import traceback

import sys, re
import logging

descriptors = []

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s\t Thread-%(thread)d - %(message)s", filename='/tmp/gmond.log', filemode='w')
logging.debug('starting up')

last_update = 0
last_update_server = 0
aniwar_stats = {}
aniwar_stats_last = {}
server_stats = {}

MAX_UPDATE_TIME = 15

#SCOREBOARD_KEY = ('_', 'S', 'R', 'W', 'K', 'D', 'C', 'L', 'G', 'I', '.')

def update_stats():
	logging.debug('updating stats')
	global last_update, aniwar_stats, aniwar_stats_last
	
	cur_time = time.time()

	if cur_time - last_update < MAX_UPDATE_TIME:
		logging.debug(' wait ' + str(int(MAX_UPDATE_TIME - (cur_time - last_update))) + ' seconds')
		return True
	else:
		last_update = cur_time

	#####
	# Update Aniwar stats
	try:
		aniwar_stats = {}
		logging.debug(' opening URL: ' + str(STATUS_URL))
		f = urllib.urlopen(STATUS_URL)

		for line in f.readlines():
			line = line.strip().split(': ')
			logging.debug('  line: ' + str(line))

			if len(line) == 2:
                                key = line[0]
				val = line[1]
			        aniwar_stats[key] = val

		f.close()
	except:
		logging.warning('error refreshing stats')
		logging.warning(traceback.print_exc(file=sys.stdout))
		return False

	if not aniwar_stats:
		logging.warning('error refreshing stats')
		return False

    	logging.debug('success refreshing stats')
	logging.debug('aniwar_stats: ' + str(aniwar_stats))

	return True

def get_stat(name):
	logging.debug('getting stat: ' + name)

	ret = update_stats()

	if ret:
		if name.startswith('aniwar_'):
			label = name[7:]
		else:
			label = name

		try:
			return int(aniwar_stats[label])
		except:
			logging.warning('failed to fetch ' + name)
			return 0
	else:
		return 0

def metric_init(params):
	global descriptors

	global STATUS_URL
	global REPORT_EXTENDED

	STATUS_URL	= params.get('status_url')
	logging.debug('init: ' + str(params))

	time_max = 60

	descriptions = dict(
               total_sessions = {
                   'value_type':'uint',
                   'units':'Num',
                   'description':'aniwar total sessions number'
                   },
               idle_sessions = {
                   'value_type':'uint',
                   'units':'Num',
                   'description':'aniwar idle sessions number'
                   },

               playback_sessions = {
                   'value_type':'uint',
                   'units':'Num',
                   'description':'aniwar playback sessions number'
                   },
               arena_sessions = {
                   'value_type':'uint',
                   'units':'Num',
                   'description':'aniwar arena sessions number'
                   },
               )

	update_stats()

	for label in descriptions:
		if aniwar_stats.has_key(label):
			d = {
				'name': 'aniwar_' + label,
				'call_back': get_stat,
				'time_max': time_max,
				'value_type': 'uint',
				'units': '',
				'slope': 'both',
				'format': '%u',
				'description': label,
				'groups': 'aniwar'
			}
		else:
			logging.error("skipped " + label)
			continue

		# Apply metric customizations from descriptions
		d.update(descriptions[label])
		descriptors.append(d)

	#logging.debug('descriptors: ' + str(descriptors))

	return descriptors

def metric_cleanup():
	logging.shutdown()
	# pass

if __name__ == '__main__':
	from optparse import OptionParser
	import os

	logging.debug('running from cmd line')
	parser = OptionParser()
        parser.add_option('-U', '--URL',dest='status_url',default='http://localhost:9773/aniwar/stats',help='URL for aniwar status page')
	parser.add_option('-b', '--gmetric-bin', dest='gmetric_bin', default='/usr/bin/gmetric', help='path to gmetric binary')
	parser.add_option('-c', '--gmond-conf', dest='gmond_conf', default='/etc/ganglia/gmond.conf', help='path to gmond.conf')
	parser.add_option('-g', '--gmetric', dest='gmetric', action='store_true', default=False, help='submit via gmetric')
	parser.add_option('-q', '--quiet', dest='quiet', action='store_true', default=False)

	(options, args) = parser.parse_args()

	metric_init({
		'status_url': options.status_url,
	})

	for d in descriptors:
		v = d['call_back'](d['name'])
		if not options.quiet:
			print ' %s: %s %s [%s]' % (d['name'], v, d['units'], d['description'])

		if options.gmetric:
			if d['value_type'] == 'uint':
				value_type = 'uint32'
			else:
				value_type = d['value_type']

			cmd = "%s --conf=%s --value='%s' --units='%s' --type='%s' --name='%s' --slope='%s'" % \
				(options.gmetric_bin, options.gmond_conf, v, d['units'], value_type, d['name'], d['slope'])
			os.system(cmd)

