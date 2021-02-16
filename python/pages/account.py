import sys, os, datetime
from sqlalchemy import insert
from lxml import etree as ET

from domino.core import log, DOMINO_ROOT
from domino.page_controls import TabControl

from _system.pages import Title, Text, Toolbar, Select, Table, Button, Rows, DeleteIconButton, TextWithComments, FlatButton, DangerButton, PrimaryButton
from _system.pages import Page as BasePage

from _system.tables.postgres.account import Account
from _system.components.licenses import Licenses
from _system.enums.unit import Unit
#from _system.tables.postgres.good import Good
from _system.tables.postgres.good_param import GoodParam

from tables.postgres import License, Good, LicenseObject, LicenseDocument

from components.metrics import Metric
from components.ls import from_domino_date, to_domino_date, Product

Tabs = TabControl('tabs')
Tabs.item('licenses_tab', 'Лицензии')
Tabs.item('documents_tab', 'Изменения')
Tabs.item('objects_tab', 'Объекты')
Tabs.item('sft_tab', 'Сертификаты')

class LicenseGroups:
	class Item:
		def __init__(self, lis, good):
			self.good = good
			self.qty = 0
			self += lis
		
		def __iadd__(self, lis):
			self.qty += lis.qty if lis.qty else 1

		def __repr__(self):
			return f'<LicenseGroups.Item good={self.good}, qty={self.qty}>'

	
	def __init__(self, postgres, account_id):
		self.items = {}
		count = 0
		for lis in postgres.query(License).filter(License.account_id == account_id):
			count += 1
			item = self.items.get(lis.good_id)
			if not item:
				good = postgres.query(Good).get(lis.good_id)
				item = LicenseGroups.Item(lis, good)
				self.items[lis.good_id] = item
			else:
				item += lis
		log.debug(f'count = {count}')
		log.debug(f'items = {self.items}')

class Page(BasePage):
	
	def __init__(self, application, request):
		super().__init__(application, request, controls=[Tabs])
		self.postgres = None
		self.license_account_id = self.attribute('license_account_id')
		self._account = None
	
	@property
	def account(self):
		if self._account is None:
			self._account = self.postgres.query(Account).get(self.license_account_id)
		return self._account

	def delete_object(self):
		object_id = self.get('object_id')
		self.postgres.query(LicenseObject).filter(LicenseObject.id == object_id).delete()
		self.postgres.commit()
		Rows(self, 'table').row(object_id)
		self.message(object_id)
   
	def print_object(self, row, obj):
		row.cell(width=2).text(f'{obj.t_id}')
		row.cell(width=2).text(f'{obj.code}')
		row.cell().text(obj.name)
		DeleteIconButton(row.cell(align='right')).onclick('.delete_object', {'object_id':obj.id})

	def print_objects(self):
		table = Table(self, 'table').mt(0.5)
		table.column('Тип')
		table.column('Код')
		table.column('Наименование')
		table.column()
		query = self.postgres.query(LicenseObject)\
			.filter(LicenseObject.account_id == self.account.id)
		
		for obj in query.order_by(LicenseObject.name):
			row = table.row(obj.id)
			self.print_object(row, obj)

	def objects_tab(self):
		toolbar = Toolbar(self, 'toolbar').mt(0.5)
		PrimaryButton(toolbar.item(ml='auto'), 'Регистрировать')\
			.onclick('pages/object_create', {'license_account_id':self.license_account_id})
		self.print_objects()

	def licenses_tab(self):
		toolbar = Toolbar(self, 'toolbar').mt(0.5)  
		self.print_licenses()

	def print_licenses(self):
		table = Table(self, 'table').mt(0.5)
		table.column('Продукт')
		table.column(align='right').text('Количество')
		#table.column('Сроки')

		lisense_grous = LicenseGroups(self.postgres, self.account.id)

		for item in lisense_grous.items.values():
			row = table.row()
			row.cell(wrap=False, width=2).href(item.good.name, 'pages/account_licenses', {'license_account_id':self.account.id, 'good_id':item.good.id})
			row.cell(align='right').text(item.qty)    

	def documents_tab(self):
		toolbar = Toolbar(self, 'toolbar')
		query = self.postgres.query(LicenseDocument, Good).filter(LicenseDocument.account_id == self.account.id)\
			.join(Good, Good.id == LicenseDocument.good_id)

		table = Table(self, 'table').mt(1)
		table.column().text('#')
		table.column().text('Продукт')
		table.column().text('Создание')
		table.column()

		for doc, good in query.order_by(LicenseDocument.id.desc()).limit(100):
			row = table.row(doc.id)
			self.print_document(row, doc, good)

	def print_document(self, row, doc, good):
		#cell = row.cell(wrap=False, width=1).onclick(self.delete_document)
		#Text(cell).glif('check')

		row.cell().text(doc.id)
		row.cell().href(good.name, 'pages/license_document', {'document_id' : doc.id})
		row.cell().text(doc.ctime)

		cell = row.cell(width=1, wrap=False, align='right')
		Text(cell).glif('times', style='-font-size:small; color:red')
		cell.onclick(self.delete_document, {'document_id':doc.id})

	def delete_document(self):
		document_id = self.get('document_id')
		self.postgres.query(LicenseDocument).filter(LicenseDocument.id == document_id).delete()
		Rows(self, 'table').row(document_id)
		#self.message('Удален документ delete') 

	def print_json_sft(self, table):
		sft = Licenses.Sft(self.account.id)
		sft.load()
		table.row().cell(css='h5').text(sft.file)
		table.row().cell().text(sft.js)
		

	def sft_tab(self):
		Text(self, 'toolbar')
		#group_param = self.postgres.query(GoodParam).get('local_group')
		#group_id = None
		#for code, name in group_param_items(self.postgres):

		table = Table(self, 'table').mt(1)
		self.print_json_sft(table)

	def __call__(self):
		Title(self, f'{self.account.id} ({self.account.alias}), {self.account.name}')
		Tabs(self)


