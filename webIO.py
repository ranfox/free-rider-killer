# -*- coding: utf8 -*-
import bs4
import cookielib
import gzip
import json
import StringIO
import time
import urllib
import urllib2

#============================================================
# Function Name: adminLogin
# Parameter:
# config = {
#     'username' : 'username',
#     'password' : 'password'
# }
# Return: Boolean
#------------------------------------------------------------
# Function Name: deleteThread
# Parameter:
# configData = {
#     'kw' : 'c语言',
#     'fid' : 22545
# }
# threadData = {
#     'tid' : 4304106830,
#     'pid' : 82457746974
# }
# Return: Boolean
#------------------------------------------------------------
# Function Name: blockID
# Parameter:
# configData = {
#     'fid' : 22545
# }
# threadData = {
#     'author' : 'author'
# }
# Return: Boolean
#------------------------------------------------------------
# Function Name: getThreadDataList
# Parameter:
# configData = {
#     'kw' : 'c语言'
# }
# Return: threadDataList
#------------------------------------------------------------
# Function Name: isLogined
# Return: Boolean
#============================================================
# global variable list:
# _cj

def adminLogin(config):
	_initialization()

	print '--- Logining ---'
	postdata = {
		'token' : _getToken(),
		'tpl' : 'pp',
		'username' : config['username'],
		'password' : config['password'],
	}
	_genericPost('https://passport.baidu.com/v2/api/?login', postdata)

	if isLogined():
		print "--- Login succeessful ---"
		return True
	else:
		print "--- Login failed ---"
		return False


def deleteThread(threadData, configData):
	print '--- Deleting ---'

	postdata = {
		'tbs' : _getTbs(),
		'kw' : configData['kw'],
		'fid' : configData['fid'],
		'tid' : threadData['tid'],
		'pid' : threadData['pid'],
		'commit_fr' : 'pb',
		'ie' : 'utf-8',
		'is_vipdel' : '0',
		'is_finf' : 'false'
	}
	data = _genericPost('http://tieba.baidu.com/f/commit/post/delete', postdata)
	err_code = json.loads(_decodeGzip(data))['err_code']

	if err_code == 0:
		print '--- Delete succeessful ---'
		#TODO: split log, log function should be called by main
		_recordHistory(threadData, 'delete')
		return True
	else:
		print '--- Delete failed ---'
		logFile = open('error.log', 'a')
		logFile.write(time.asctime() + '\n')
		logFile.write('Delete failed error code' + err_code + '\n\n')
		logFile.close()
		return False

def blockID(threadData, configData):
	print '--- Blocking ---'

	constantPid = '82459413573'
	postdata = {
		'tbs' : _getTbs(),
		'fid' : configData['fid'],
		'user_name[]' : threadData['author'],
		'pids[]' : constantPid, 
		'day' : '1',
		'ie' : 'utf-8',
		'reason' : '根据帖子标题或内容，判定出现 伸手，作业，课设，作弊，二级考试，广告，无意义水贴，不文明言行或对吧务工作造成干扰等（详见吧规）违反吧规的行为中的至少一种，给予封禁处罚。如有问题请使用贴吧的申诉功能。'
	}
	data = _genericPost('http://tieba.baidu.com/pmc/blockid', postdata)
	err_code = json.loads(_decodeGzip(data))['err_code']

	if err_code == 0:
		print '--- Block succeessful ---'
		_recordHistory(threadData, 'block')
		return True
	else:
		print '--- Block failed ---'
		logFile = open('error.log', 'a')
		logFile.write(time.asctime() + '\n')
		logFile.write('Block failed error code' + err_code + '\n\n')
		logFile.close()
		return False

def getThreadDataList(configData):
	data = _genericGet('http://tieba.baidu.com/f?kw=' + configData['kw'])

	# if there is a special utf-8 charactor in html that cannot decode to 'gbk' (eg. 🐶), 
	# there will be a error occured when you trying to print threadData['abstract'] to console
	html = data.decode('utf8').encode('gbk','replace').decode('gbk')
	soup = bs4.BeautifulSoup(html, 'html5lib')
	threadList = soup.select('.j_thread_list')
	topThreadNum = len(soup.select('.thread_top'))

	threadDataList = []
	for thread in threadList[topThreadNum:]:
		dataField = json.loads(thread['data-field'])
		threadData = {
			'title' : thread.select('a.j_th_tit')[0].string,
			'author' : dataField['author_name'],
			'abstract' : thread.select('div.threadlist_abs')[0].string,
			'tid' : dataField['id'],
			'pid' : dataField['first_post_id'],
			'goodThread' : dataField['is_good'],
			'topThread' : dataField['is_top'],
			'replyNum' : dataField['reply_num']
		}
		#threadData['abstract'] maybe None, and this may cause a lot of problems!!!
		threadData['abstract'] = (u'None' if threadData['abstract'] == None else threadData['abstract'])
		threadDataList.append(threadData)

	return threadDataList


def isLogined():
	if 'BDUSS' in str(_cj):
		return True
	else:
		return False

#Local function

def _initialization():
	_initializeCookieJar()

	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(_cj))
	urllib2.install_opener(opener)

	#Geting Cookie
	_genericGet('http://www.baidu.com/')

	return

def _initializeCookieJar():
	global _cj
	_cj = cookielib.CookieJar()

	return

def _genericPost(url, postdata):
	request = urllib2.Request(url, urllib.urlencode(postdata))
	request.add_header('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
	request.add_header('Accept-Encoding','gzip,deflate,sdch')
	request.add_header('Accept-Language','zh-CN,zh;q=0.8')
	request.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36')
	request.add_header('Content-Type','application/x-www-form-urlencoded')

	return _genericGet(request)

def _genericGet(url):
	connection = urllib2.urlopen(url, timeout = 5)
	data = connection.read()
	connection.close()

	return data

def _decodeGzip(data):
	fileObj = StringIO.StringIO(data)
	gzipObj = gzip.GzipFile(fileobj = fileObj)
	gzipData = gzipObj.read()
	fileObj.close()
	gzipObj.close()

	return gzipData

def _getTbs():
	data = _genericGet('http://tieba.baidu.com/dc/common/tbs')
	tbs = json.loads(data)['tbs']

	return tbs

def _getToken():
	data = _genericGet('https://passport.baidu.com/v2/api/?getapi&tpl=pp&apiver=v3&class=login')
	token = json.loads(data.replace('\'', '"'))['data']['token']

	return token








#TODO: split
def _recordHistory(threadData, logType):
	logFile = open('history.log', 'a')

	if logType == 'delete':
		logFile.write('{\n')
		logFile.write('    "type" : "delete",\n')
		logFile.write('    "data" : {\n')
		logFile.write('        "time" : "' + time.asctime() + '",\n')
		logFile.write('        "title" : "' + threadData['title'].encode('utf-8') + '",\n')
		logFile.write('        "author" : "' + threadData['author'].encode('utf-8') + '",\n')
		logFile.write('        "abstract" : "' + threadData['abstract'].encode('utf-8') + '",\n')
		logFile.write('    }\n')
		logFile.write('},\n')
	elif logType == 'block':
		logFile.write('{\n')
		logFile.write('    "type" : "block",\n')
		logFile.write('    "data" : {\n')
		logFile.write('        "time" : "' + time.asctime() + '",\n')
		logFile.write('        "author" : "' + threadData['author'].encode('utf-8') + '",\n')
		logFile.write('    }\n')
		logFile.write('},\n')

	logFile.close()

