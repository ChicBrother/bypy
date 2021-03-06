#!/usr/bin/env python
# encoding: utf-8

# primitive sanity tests

from __future__ import unicode_literals

import os
import sys
import shutil
import re
# store the output, for further analysis
class StorePrinter(object):
	def __init__(self, opr):
		self.opr = opr
		self.q = []

	def pr(self, msg):
		self.q.append(msg)
		self.opr(msg)

	def empty(self):
		del self.q[:]

	def getq(self):
		return self.q

def banner(msg):
	title = "{0} {1} {0}".format('=' * 8, msg)
	line = '=' * len(title)
	print(line)
	print(title)
	print(line)

def ifany(list, require):
	for element in list:
		if require(element):
			return True

	return False

def filterregex(list, regex):
	rec = re.compile(regex)
	return filter(lambda x: rec.search(x), list)

# TODO: this is a quick hack, need to re-structure the directory later
# http://stackoverflow.com/questions/11536764/attempted-relative-import-in-non-package-even-with-init-py/27876800#27876800
bypydir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#sys.path.insert(0, bypydir)
sys.path.append(bypydir)
#print(sys.path)
configdir = 'configdir'
downloaddir = 'downdir'
testdir = 'testdir'
import bypy
# monkey patch all the way
mpr = StorePrinter(bypy.pr)
bypy.pr = mpr.pr
# create some dummy files
zerofilename = os.path.join(testdir, 'allzero.1m.bin')
if not os.path.exists(configdir):
	os.mkdir(configdir)
shutil.copy('bypy.json', configdir)
by = bypy.ByPy(configdir=configdir, debug=1, verbose=1)

def prepare():
	# preparation
	if 'refresh' in sys.argv:
		by.refreshtoken()
	# we must upload something first, otherwise, listing / deleting the root directory will fail
	banner("Uploading a file")
	assert by.upload(testdir + '/a.txt') == bypy.ENoError
	print("Response: {}".format(by.response.json()))
	banner("Listing the root directory")
	assert by.list('/') == bypy.ENoError
	print("Response: {}".format(by.response.json()))
	mpr.empty()

def emptyremote():
	banner("Deleting all the files at PCS")
	assert by.delete('/') == bypy.ENoError
	assert 'request_id' in by.response.json()
	mpr.empty()
	with open(zerofilename, 'wb') as f:
		zeros = bytearray(1024 * 1024)
		f.write(zeros)

def uploaddir():
	# upload
	banner("Uploading the local directory")
	assert by.upload(testdir, testdir) == bypy.ENoError
	assert filterregex(mpr.getq(),
					   r"RapidUpload: 'testdir[\\/]allzero.1m.bin' =R=\> '/apps/bypy/testdir/allzero.1m.bin' OK")
	assert filterregex(mpr.getq(), r"'testdir[\\/]a.txt' ==> '/apps/bypy/testdir/a.txt' OK.")
	assert filterregex(mpr.getq(), r"'testdir[\\/]b.txt' ==> '/apps/bypy/testdir/b.txt' OK.")
	print("Response: {}".format(by.response.json()))
	mpr.empty()

def getquota():
	# quota
	banner("Getting quota")
	assert by.info() == bypy.ENoError
	resp = by.response.json()
	print("Response: {}".format(resp))
	#assert resp['used'] == 1048626
	assert resp['quota'] == 2206539448320L
	mpr.empty()

def assertsame():
	bypy.pr(by.result)
	assert len(by.result['diff']) == 0
	assert len(by.result['local']) == 0
	assert len(by.result['remote']) == 0
	assert len(by.result['same']) == 6

def compare():
	# comparison
	banner("Comparing")
	assert by.compare(testdir, testdir) == bypy.ENoError
	assertsame()
	mpr.empty()

def downdir():
	# download
	banner("Downloading dir")
	shutil.rmtree(downloaddir, ignore_errors=True)
	assert by.downdir(testdir, downloaddir) == bypy.ENoError
	assert by.compare(testdir, downloaddir) == bypy.ENoError
	assertsame()
	mpr.empty()

def syncup():
	banner("Syncing up")
	emptyremote()
	assert by.syncup(testdir, testdir) == bypy.ENoError
	assert by.compare(testdir, testdir) == bypy.ENoError
	assertsame()
	mpr.empty()

def syncdown():
	banner("Syncing down")
	shutil.rmtree(downloaddir, ignore_errors=True)
	assert by.syncdown(testdir, downloaddir) == bypy.ENoError
	assert by.compare(testdir, downloaddir) == bypy.ENoError
	shutil.rmtree(downloaddir, ignore_errors=True)
	assertsame()
	mpr.empty()

def main():
	prepare()
	emptyremote()
	uploaddir()
	getquota()
	compare()
	downdir()
	syncup()
	syncdown()
	os.remove(zerofilename)
	shutil.rmtree(configdir, ignore_errors=True)

# this is barely a sanity test, more to be added
if __name__ == "__main__":
	main()
