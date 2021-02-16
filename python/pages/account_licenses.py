import sys, os, datetime
from sqlalchemy import insert
from lxml import etree as ET

from domino.core import log, DOMINO_ROOT
from domino.page_controls import TabControl

from _system.pages import Input, Title, Text, Toolbar, Select, Table, Button, Rows, DeleteIconButton, TextWithComments
from _system.pages import Page as BasePage
from _system.components.licenses import Licenses
from _system.enums.unit import Unit

from _system.tables.postgres.good_param import GoodParam

from _system.tables.postgres.account import Account
from tables.postgres import License, LicenseObject, Good

from components.metrics import Metric
from components.ls import from_domino_date, to_domino_date, Product

class Page(BasePage):
	
	def __init__(self, application, request):
		super().__init__(application, request)
		self.postgres = None
		self.license_account_id = self.attribute('license_account_id')
		self.good_id = self.attribute('good_id')
		self._account = None
		self._good = None

	@property
	def account(self):
		if self._account is None:
			self._account = self.postgres.query(Account).get(self.license_account_id)
		return self._account

	@property
	def object_type(self):
		return self.good.object_type

	@property
	def good(self):
		if self._good is None:
			self._good = self.postgres.query(Good).get(self.good_id)
		return self._good

	def print_tab(self):
		toolbar = Toolbar(self, 'toolbar').mt(0.5)
		Input(toolbar.item(), name = 'finder', placeholder='Поиск ...').onkeypress(13, '.print_licenses')
		self.print_table()
		
	def print_table(self):
		table = Table(self, 'table').mt(0.5)
		#table.column().text('#')
		table.column(self.object_type)
	
		if self.object_type in [Licenses.ObjectType.Подразделение]:
			table.column().text('Guid')

		if self.object_type in [Licenses.ObjectType.Подразделение, Licenses.ObjectType.Компьютер, Licenses.ObjectType.ФСРАР]:
			table.column().text('Описание')

		if self.object_type in [Licenses.ObjectType.Hasp, Licenses.ObjectType.MemoHasp]:
			table.column().text('Тип')
			table.column().text('Партия')
			table.column('Cерийный номер')

		if self.object_type in [Licenses.ObjectType.Hasp, Licenses.ObjectType.MemoHasp]:
			table.column('Марк. номер')
 
		table.column('Примечание')

		if self.object_type in [Licenses.ObjectType.Hasp]:
			table.column(align='right').text('Количество')

		table.column('Срок')

		query = self.postgres.query(License, LicenseObject)\
			.filter(License.account_id == self.account.id)\
			.filter(License.good_id == self.good_id)\
			.outerjoin(LicenseObject, LicenseObject.id == License.object_id)

		finder = self.get('finder')
		if finder:
			query = query.filter(License.name.ikile(f'%{finder}%'))

		for lis, obj in query:
			row = table.row(lis.id)
			self.print_row(row, lis, obj)

	def print_row(self, row, lis, obj):
		#row.cell().text(lis.id)
		if not obj:
			row.cell().text(f'?{lis.object_id}?').style('color:red')
			return
		try:
			row.cell(wrap=False, width=2).text(obj.code)

			if self.object_type in [Licenses.ObjectType.Подразделение]:
				row.cell().text(obj.guid)
			
			if self.object_type in [Licenses.ObjectType.Подразделение, Licenses.ObjectType.Компьютер, Licenses.ObjectType.ФСРАР]:
				row.cell(wrap=False, width=2).text(obj.name)
			#row.cell().text(obj.info)

			if self.object_type in [Licenses.ObjectType.Hasp, Licenses.ObjectType.MemoHasp]:
				row.cell().text(obj.hasp_type)
				row.cell().text(obj.hasp_party)
				row.cell().text(obj.serial_no)

			if self.object_type in [Licenses.ObjectType.Hasp, Licenses.ObjectType.MemoHasp]:
				row.cell().text(obj.mark_no)

			row.cell().text(lis.name)

			if self.object_type in [Licenses.ObjectType.Hasp]:
				row.cell(align='right').text(lis.qty)

			cell = row.cell()
			cell.text(lis.exp_date)
			if lis.exp_date:
				if lis.exp_date < datetime.date.today():
					cell.style('color:red')
					
		except Exception as ex:
			log.exception(__file__)
			row.cell().text(ex).style('color:red')

	def __call__(self):
		account_name = self.account.name if self.account.name else self.account.id
		Title(self, f'{account_name}, {self.good.name}')
		self.print_tab()


