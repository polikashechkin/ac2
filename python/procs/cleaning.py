import os, sys, datetime, time, json, sqlite3
import cx_Oracle
import paramiko
from lxml import etree as ET
from sqlalchemy import delete, insert, select, update, text as T

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
	sys.path.append(path)

from domino.core import log, DOMINO_ROOT
from domino.jobs import Proc

from _system.enums.unit import Unit
from _system.components.licenses import Licenses
from _system.pages import Page as BasePage, Title, Text, Table, Toolbar, Select

from _system.databases.postgres import Postgres

from components.metrics import Metric
from components.ls import from_domino_date, to_domino_date, Product, UNKNOWN, DOMINO, RETAIL_ALCO

from  tables.postgres import Account, Good, GoodParam, License, LicenseObject, LicenseDocument, LicenseDocumentLine


MODULE_ID = 'ac2'
DESCRIPTION = 'Реорганизация данных'
PROC_ID = 'procs/cleaning.py'

SW_SFT_TEST = {'scheme':'SW_SFT_TEST', 'dsn':'192.168.1.24:1521/ORCL'}

def on_activate(account_id, msg_log):
	Proc.create(account_id, MODULE_ID, PROC_ID, description=DESCRIPTION, url='procs/cleaning')

class Page(BasePage):
	def __init__(self, application, request):
		super().__init__(application, request)
		self.proc = Proc.get(self.account_id, MODULE_ID, PROC_ID)

	def __call__(self):
		Title(self, f'{self.proc.ID}, {DESCRIPTION}')


class LicensesDB:
	def __init__(self, job):
		self.job = job
		self.postgres = job.postgres
		self.log = job.log
		self.count = 0
		#--------------------------------
		self.goods = {}
		query = self.postgres.query(Good).filter(Good.object_type_id != None)
		for good in query:
			key = (good.license_product_id, good.object_type_id)
			self.goods[key] = good
		self.log(f'Продуктов {len(self.goods)}')
		#--------------------------------
		self.locations_by_guid = {}
		self.obj_by_account_type_key = {}
		for obj in self.postgres.query(LicenseObject):
			if obj.object_type == LicenseObject.Type.Подразделение:
				if obj.guid:
					self.locations_by_guid[obj.guid] = (obj.code, obj.name, obj.address)
			self.obj_by_account_type_key[(obj.account_id, obj.t_id, obj.code)] = obj
		self.log(f'Объектов {len(self.obj_by_account_type_key)}, в т.ч. локаций {len(self.locations_by_guid)}')

		self.documents = {}

	def reg_good(self, product, object_type):
		key = (product.id, object_type.id)
		good = self.goods.get(key)
		if not good:
			good = Good()
			if object_type != LicenseObject.Type.Hasp:
				good.by_piece_accountind = datetime.date.today()
			good.code = f'{product.id.lower()}/{object_type.id.lower()}'
			good.name = f'{product.name}/{object_type.id.lower()}'
			good.unit_id = product.unit.id
			good.license_product_id = product.id
			good.object_type_id = object_type.id
			good.good_type_id = product.good_type.id
			self.postgres.add(good)
			self.postgres.commit()
			self.log(f'Создан товар {good}')
			self.goods[key] = good
		return good

	def get_products(self, options):
		if options:
			products = []
			for option in options.split(','):
				option = option.strip()
				products.append(Product.find_by_uid(option, UNKNOWN))
			return products
		else:
			return [DOMINO]

	def get_location_info(self, cur, account, guid):
		assert guid
		r = self.locations_by_guid.get(guid)
		if not r:
			cur.execute('select code, name, address from depts where account_id=? and guid=?', [account.id, guid])
			r = cur.fetchone()
			if r is None:
				self.log(f'НЕ НАЙДЕНО ПОДРАЗДЕЛЕНИЕ {guid}')
				return None, None, None
			code, name, address = r
			self.locations_by_guid[guid] = (code, name, address)
		else:
			code, name, address = r
		return code, name, address

	def get_computer_info(self, cur, account, key):
		cur.execute('select  name, description, address from devices where account_id=? and key=?', [account.id, key])
		r = cur.fetchone()
		if r is None:
			self.log(f'НЕ НАЙДЕН КОМПЬЮТЕР {key}')
			return None, None, None
		else:
			name, description, address = r
			return name, description, address

	def reg_obj(self, cur, account, object_type, key, serial_no = None, mark_no = None, hasp_party = None, hasp_type = None, pwd1= None, pwd2 = None, description=None, address=None, name=None, guid = None):
		# особый случай KEY это GUID по которому надо найти код		
		if object_type == LicenseObject.Type.Подразделение:
			guid = key
			key, name, address = self.get_location_info(cur, account, guid)
			if not key:
				return None

		# проверкаЮ что объект уже существует
		obj = self.obj_by_account_type_key.get((account.id, object_type.id, key))
		if obj:
			return obj
		
		# получение дополнительный данных объекта
		if object_type == LicenseObject.Type.Компьютер:
			name, description, address = self.get_location_info(cur, account, key)

		# созданеи объекта
		obj = LicenseObject(account_id = account.id, object_type_id = object_type.id, code = key, 
			serial_no = serial_no, mark_no = mark_no,
			hasp_party = hasp_party, hasp_type = hasp_type, pwd1 = pwd1, pwd2 = pwd2, 
			description = description, name = name, address = address, guid = None
			)
		self.postgres.add(obj)
		self.postgres.commit()
		self.log(f'Создан объект {obj.id} : {obj}')

		self.obj_by_account_type_key[(account.id, object_type.id, key)] = obj
		return obj

	def reg_document(self, account, good):
		doc = self.documents.get((account.id, good.id))
		if doc: return doc
		doc = LicenseDocument(account_id=account.id, good_id = good.id)
		self.postgres.add(doc)
		self.documents[(account.id, good.id)] = doc
		self.postgres.commit()
		return doc

	def reg_license(self, account, products, obj, exp_date, qty = 1, name = None):
		assert obj 
		if not exp_date:
			exp_date = datetime.date(day=1, month=1, year=2100)
		for product in products:
			self.count += 1
			good = self.reg_good(product, obj.object_type)
			assert good 
			document = self.reg_document(account, good)
			assert document
			line = LicenseDocumentLine(document_id=document.id, object_id = obj.id, exp_date=exp_date, qty = qty)
			self.postgres.add(line)

			#lis = self.postgres.query(License).filter(License.account_id == account.id, License.good_id == good.id, License.object_id == obj.id).first()
			#if lis:
			#	if not lis.exp_date or lis.exp_date < exp_date:
			#		lis.exp_date = exp_date 
			#		self.postgres.commit()
					#self.log(f'Обновление {lis}')
			#else:
			#	lis = License(account_id = account.id, good_id = good.id, object_id = obj.id, exp_date = exp_date, name=name, qty=qty)
			#	self.postgres.add(lis)
			#	self.postgres.commit()
				#self.log(f'Создание {lis}')
			#return lis

class Job(Proc.Job): 
	def __init__(self, ID):
		super().__init__(ID)
		self.postgres = None

	def __call__(self):
		self.proc = Proc.get(self.account_id, MODULE_ID, PROC_ID)
		self.log('НАЧАЛО РАБОТЫ')
		start = time.perf_counter()
		stop_reason = ''
		self   .postgres = Postgres().session(self.account_id)
		#self.db_conn = cx_Oracle.connect(user = SW_SFT_TEST['scheme'], password = SW_SFT_TEST['scheme'], dsn= SW_SFT_TEST['dsn'], encoding = "UTF-8", nencoding = "UTF-8") 
		#self.db_cur = self.conn.cursor()
		try:
			self.dowork()
			self.postgres.commit()
		except BaseException as ex:
			log.exception(__file__)
			self.postgres.rollback()
			stop_reason = f'{ex}'
			raise Exception(stop_reason)
		finally:
			self.postgres.close()
			#self.conn.close()
		time_s = round(time.perf_counter() - start, 3)
		self.log(f'ОКОНЧАНИЕ РАБОТЫ {stop_reason} : {time_s} s')

	def dowork(self):
		self.licenses = LicensesDB(self)
		#--------------------------------
		account_db = os.path.join(DOMINO_ROOT, 'data', 'account.db')
		self.account_db_cur = sqlite3.connect(account_db).cursor()
		self.log(f'connect to "{account_db}"')
		
		# установление связи и копирование БД account.db
		self.ssh = paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		self.log(f"ssh.connect('demo39.domino.ru', username = 'root' , password = 'ljvbyj')")
		self.ssh.connect('demo39.domino.ru', username = 'root' , password = 'ljvbyj')
		
		# копирование account.db во временный файл и открытие его 
		demo_account_db = os.path.join(self.temp, 'account.db')
		stdin, stdout, stderr = self.ssh.exec_command(f'cat /DOMINO/data/account.db')
		self.log(f"copy ssh:/DOMINO/data/account.db => '{demo_account_db}'")
		with open(demo_account_db, 'wb') as f:
			f.write(stdout.read())
		self.demo_account_db_cur = sqlite3.connect(demo_account_db).cursor()
		self.log(f"connect to '{demo_account_db}'")

		#обработка учетных записей
		for account in self.postgres.query(Account):
			self.do_account(account)

	def ssh_listdir(self, path):
		files = []
		stdin, stdout, stderr = self.ssh.exec_command(f'ls {path}')
		for file_name in stdout:
			if not file_name.startswith('_') and not file_name.startswith('.'):
				files.append(file_name.strip())
		self.log(f'ssh.listdir({path}) => {files}')
		return files

	def ssh_read(self, path):
		stdin, stdout, stderr = self.ssh.exec_command(f'cat {path}')
		return stdout.read()

	def do_account(self, account):
		start = time.perf_counter()
		self.license_count = 0
		self.check_for_break()
		#if account.id != '00691000': return 
		self.log(f'{account.id} {account.name.upper()}')
		self.count = 0

		# DEMO.DOMINO.RU -----------------------------------------
		folder = f'/DOMINO/accounts/{account.id}/sft/trials'
		for file_name in self.ssh_listdir(folder):
			self.do_demo_trial(f'{folder}/{file_name}', self.demo_account_db_cur, account)
		self.log(f'Обработано {self.license_count} лицензий')

		#trials_folder = os.path.join(DOMINO_ROOT, 'accounts', self.account_id, 'backups', 'demo', 'accounts', account.id, 'sft', 'trials')
		#if os.path.isdir(trials_folder):
		#		self.log(f'{trials_folder.upper()} : ')
		#	for trial_file in os.listdir(trials_folder):
		#		self.log(f'Обработано {self.license_count} лицензий')

		#final_sft_file = os.path.join(DOMINO_ROOT, 'accounts', self.account_id, 'backups', 'demo', 'accounts', account.id, 'sft', f'{account.id}.final.sft.xml')
		#if os.path.isfile(final_sft_file):
		#	self.do_final_sft(self.demo_account_db_cur, account, final_sft_file)
		#self.log(f'Обработано {self.license_count} лицензий')

		# -------------------------------------------
		folder = os.path.join(DOMINO_ROOT, 'accounts', account.id, 'sft', 'trials')
		if os.path.isdir(folder):
			file_names = os.listdir(folder)
			self.log(f'listdir({folder}) => {file_names}')
			for file_name in file_names:
				self.do_trial(os.path.join(folder, file_name), self.account_db_cur, account)
			self.log(f'Обработано {self.license_count} лицензий')

		final_sft_file = os.path.join(DOMINO_ROOT, 'accounts', account.id, 'sft', f'{account.id}.final.sft.xml')
		if os.path.isfile(final_sft_file):
			self.log(f'{final_sft_file}')
			self.do_final_sft(self.demo_account_db_cur, account, final_sft_file)
		# -------------------------------------------
		time_ms = round(time.perf_counter() - start, 3)
		self.log(f'{account.id} : обработано {self.license_count} лицензий : {time_ms} s')

	def get_object_type(self, TYPE):
		if TYPE is None:
			raise Exception (f'Не определен тип объекта')
		object_type = LicenseObject.Type.get(TYPE.text)
		if object_type is None:
			raise Exception(f'Неизвестный тип {TYPE.text}')
		return object_type

	def do_trial(self, file, cur, account):
		self.license_count += 1
		#self.log(file)
		# <CFG>
		# <TRIAL>2018-12-20</TRIAL>
		# <CFG_KEY>01c58dd2-e031-4187-b380-f0ee3fadbcb6</CFG_KEY>
		# <DATE_LIMIT>25/01/2022</DATE_LIMIT>
		# <CFG_TYPE>48431409[63111174]</CFG_TYPE>
		# <OPTIONS>4653069[63111171]</OPTIONS>
		# </CFG>     
		xml = ET.parse(file)

		CFG_TYPE 		= xml.find('CFG_TYPE')

		options         = xml.find('OPTIONS').text
		products		= self.licenses.get_products(options)
		object_type     = self.get_object_type(CFG_TYPE)
		exp_date        = from_domino_date(xml.find('DATE_LIMIT').text)
		cfg_key         = xml.find('CFG_KEY').text
		
		#-----------------------------------------
		obj = self.licenses.reg_obj(cur, account, object_type, cfg_key)
		if obj:
			self.licenses.reg_license(account, products, obj, exp_date)

	def do_demo_trial(self, frial_file, cur, account):
		self.license_count += 1
		#self.log(file)
		# <CFG>
		# <TRIAL>2018-12-20</TRIAL>
		# <CFG_KEY>01c58dd2-e031-4187-b380-f0ee3fadbcb6</CFG_KEY>
		# <DATE_LIMIT>25/01/2022</DATE_LIMIT>
		# <CFG_TYPE>48431409[63111174]</CFG_TYPE>
		# <OPTIONS>4653069[63111171]</OPTIONS>
		# </CFG>        
		xml = ET.fromstring(self.ssh_read(frial_file))

		CFG_TYPE		= xml.find('CFG_TYPE')

		options         = xml.find('OPTIONS').text
		products		= self.licenses.get_products(options)
		object_type     = self.get_object_type(CFG_TYPE)
		exp_date        = from_domino_date(xml.find('DATE_LIMIT').text)
		cfg_key         = xml.find('CFG_KEY').text
		#-----------------------------------------
		obj = self.licenses.reg_obj(cur, account, object_type, cfg_key)
		if obj:
			self.licenses.reg_license(account, products, obj, exp_date)

	def do_final_sft(self, cur, account, file):
		try:
			with open(file, encoding='cp1251') as f:
				s = f.read()
				xml = ET.fromstring(s)
		except Exception as ex:
			log.exception(f'{file}')
			log.debug(f'TRY UNICODE')
			try:
				with open(file) as f:
					s = f.read()
				xml = ET.fromstring(s)
				log.debug(f'ПРОКАТИЛО')
			except Exception as ex:
				log.exception(f'{file}')
				self.log(f'{ex}')
				return
		#<HASP>
		#    <PWD1>13181</PWD1>
		#    <PWD2>2904</PWD2>
		#    <HASP_PARTY>MIZIZ</HASP_PARTY>
   		#    <HASP_TYPE>48431409[48431112]</HASP_TYPE>
		#    <HASP_ID>1339910237</HASP_ID>
		#    <SERIAL_NO>IS-K:0167</SERIAL_NO>
		#    <MARK_NO>5535</MARK_NO>
		#    <LICENSE_COUNT>1</LICENSE_COUNT>
		#    <LICENSEE_NAME>ООО ИС - Адлер, ИНН 2317076370</LICENSEE_NAME>
		#    <DATE_LIMIT>25/01/2022</DATE_LIMIT> ???
		#    <OPTIONS>4653069[63111171]</OPTIONS> ???
		#</HASP>
		for HASP in xml.findall('HASP'):

			PWD1            = HASP.find('PWD1')
			PWD2            = HASP.find('PWD2')
			HASP_PARTY      = HASP.find('HASP_PARTY')
			HASP_TYPE       = HASP.find('HASP_TYPE')
			HASP_ID         = HASP.find('HASP_ID')
			SERIAL_NO       = HASP.find('SERIAL_NO')
			MARK_NO         = HASP.find('MARK_NO')
			LICENSE_COUNT   = HASP.find('LICENSE_COUNT')
			LICENSEE_NAME   = HASP.find('LICENSEE_NAME')
			OPTIONS         = HASP.find('OPTIONS')
			DATE_LIMIT      = HASP.find('DATE_LIMIT')

			metric = Metric.find(HASP_TYPE.text)
			hasp_type = metric.name 
			if metric.is_memohasp:
				object_type = LicenseObject.Type.MemoHasp
			else:
				object_type = LicenseObject.Type.Hasp

			hasp_party 	= HASP_PARTY.text
			pwd1		= PWD1.text
			pwd2		= PWD2.text
			hasp_id 	= HASP_ID.text
			exp_date  	= from_domino_date(DATE_LIMIT.text) if DATE_LIMIT else None
			serial_no 	= SERIAL_NO.text if SERIAL_NO is not None else None
			mark_no 	= MARK_NO.text if MARK_NO is not None else None
			options 	= OPTIONS.text if OPTIONS else None
			products 	= self.licenses.get_products(options)
			name 		= LICENSEE_NAME.text if LICENSEE_NAME is not None else None

			if LICENSE_COUNT is None:
				self.log(f'НЕ ОПРЕДЕЛЕНГО КОЛИЧЕСТВА ДЛЯ "{object_type}" {hasp_id}')
				continue

			qty 		= int(LICENSE_COUNT.text)
			
			obj = self.licenses.reg_obj(cur, account, object_type, hasp_id, 
				serial_no = serial_no, mark_no = mark_no, hasp_type = hasp_type, hasp_party = hasp_party, pwd1 = pwd1, pwd2 = pwd2)
			
			if obj:
				#log.debug(f'reg_license({account}, {products}, {obj}, {qty}, {exp_date})')
				self.licenses.reg_license(account, products, obj, exp_date, qty=qty, name=name)
			self.license_count += 1

		#<CFG>
		#    <SERIAL_NO>IS-K:0192</SERIAL_NO>
		#    <MARK_NO>IS.TULA-4</MARK_NO>
		#    <CFG_KEY>127951295</CFG_KEY>
		#    <DATE_LIMIT>01/01/2100 00:00:00</DATE_LIMIT>
		#    <CFG_TYPE>48431409[63111169]</CFG_TYPE>
		#    <OPTIONS>4653069[2]</OPTIONS>
		#    <LICENSEE_NAME>ИП Сюрина Г.И., ИНН 323300465109</LICENSEE_NAME>
		#</CFG>
		for CFG in xml.findall('CFG'):

			CFG_TYPE		= CFG.find('CFG_TYPE')

			options         = CFG.find('OPTIONS').text
			products		= self.licenses.get_products(options)
			object_type     = self.get_object_type(CFG_TYPE)
			exp_date        = from_domino_date(CFG.find('DATE_LIMIT').text)
			cfg_key         = CFG.find('CFG_KEY').text
			xserial_no      = CFG.find('SERIAL_NO')
			xmark_no        = CFG.find('MARK_NO')

			serial_no       = xserial_no.text if xserial_no else None
			mark_no         = xmark_no.text if xmark_no else None
			xlicense_name   = CFG.find('LICENSEE_NAME')
			license_name    = xlicense_name.text if xlicense_name else None

			obj = self.licenses.reg_obj(cur, account, object_type, cfg_key, serial_no = serial_no, mark_no = mark_no)
			if obj:
				self.licenses.reg_license(account, products, obj, exp_date, name=license_name)
			self.license_count += 1

		#<METRICS>
		#	<METRIC>
		#		<TYPE>63111198[63111169]</TYPE>
		#		<ID>ФСРАР ID</ID>
		#		<VALUE>020000662604</VALUE>
		#		<DATE_LIMIT>25.01.2021</DATE_LIMIT>
		#	</METRIC>
		#</METRICS>
		METRICS = xml.find('METRICS')
		if METRICS:
			for METRIC in METRICS.findall('METRIC'):
				
				TYPE 		= METRIC.find('TYPE')
				VALUE 		= METRIC.find('VALUE')
				DATE_LIMIT	= METRIC.find('DATE_LIMIT')
				ID 			= METRIC.find('ID')

				try:
					object_type = self.get_object_type(TYPE)
					fsrar_id 	= VALUE.text
					exp_date  	= from_domino_date(DATE_LIMIT.text)

					obj = self.licenses.reg_obj(cur, account, object_type, fsrar_id)
					if obj:
						self.licenses.reg_license(account, [RETAIL_ALCO], obj,  exp_date)
					
					self.license_count += 1

				except Exception as ex:
					log.exception(__file__)
					self.log(f'METRIC TYPE = {TYPE.text if TYPE else None} : {ex}')

if __name__ == "__main__":
	try:
		with Job(sys.argv[1]) as job:
			job()
	except:
		log.exception(__file__)
	