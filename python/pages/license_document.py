import sys, os, datetime
from sqlalchemy import insert
from lxml import etree as ET

from domino.core import log, DOMINO_ROOT
from domino.page_controls import TabControl

from _system.pages import Input, Title, Text, Toolbar, Select, Table, Button, Rows, DeleteIconButton, TextWithComments
from _system.pages import Page as BasePage


from _system.components.licenses import Licenses
from _system.enums.unit import Unit

#from _system.tables.postgres.good_param import GoodParam
from components.metrics import Metric
from components.ls import from_domino_date, to_domino_date, Product

from tables.postgres import Account, License, LicenseObject, Good, LicenseDocument, LicenseDocumentLine


class Page(BasePage):
	
	def __init__(self, application, request):
		super().__init__(application, request)
		self.postgres = None
		self.document_id = self.attribute('document_id')
		self._document = None
		self._license_account = None
		self._good = None

	@property
	def document(self):
		if self._document is None:
			self._document = self.postgres.query(LicenseDocument).get(self.document_id)
		return self._document

	@property
	def license_account(self):
		if self._license_account is None:
			self._license_account = self.postgres.query(Account).get(self.document.account_id)
		return self._license_account
	
	@property
	def good(self):
		if self._good is None:
			self._good = self.postgres.query(Good).get(self.document.good_id)
		return self._good

	@property
	def object_type(self):
		return self.good.object_type

	def print_tab(self):
		toolbar = Toolbar(self, 'toolbar').mt(0.5)
		Input(toolbar.item(), name = 'finder', placeholder='Поиск ...').onkeypress(13, self.print_table, forms=[toolbar])
		self.print_table()

	def print_table(self):

		table = Table(self, 'table').mt(0.5)
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

		#if self.object_type in [Licenses.ObjectType.Hasp]:
		table.column(align='right').text('Количество')

		table.column('Срок')

		query = self.postgres.query(LicenseDocumentLine, LicenseObject)\
			.filter(LicenseDocumentLine.document_id == self.document.id)\
			.outerjoin(LicenseObject, LicenseObject.id == LicenseDocumentLine.object_id)

		#finder = self.get('finder')
		#if finder:
		#query = query.filter(License.name.ikile(f'%{finder}%'))

		for line, obj in query:
			row = table.row(line.id)
			self.print_row(row, line, obj)

	def print_row(self, row, line, obj):

		#row.cell(wrap=False, width=2).text(line.id)

		row.cell(wrap=False, width=2).text(obj.code if obj else '')

		if self.object_type in [Licenses.ObjectType.Подразделение, Licenses.ObjectType.Компьютер, Licenses.ObjectType.ФСРАР]:
			row.cell(wrap=False, width=2).text(obj.name if obj else '')
		#row.cell().text(obj.info)

		if self.object_type in [Licenses.ObjectType.Hasp, Licenses.ObjectType.MemoHasp]:
			row.cell().text(obj.hasp_type if obj else '')
			row.cell().text(obj.hasp_party if obj else '')
			row.cell().text(obj.serial_no if obj else '')

		if self.object_type in [Licenses.ObjectType.Hasp, Licenses.ObjectType.MemoHasp]:
			row.cell().text(obj.mark_no if obj else '')

		#if self.object_type in [Licenses.ObjectType.Hasp]:
		row.cell(align='right').text(line.qty)

		cell = row.cell(align='right')
		cell.text(line.exp_date)

	def __call__(self):
		account_name = self.license_account.name if self.license_account.name else self.license_account.id
		Title(self, f'{account_name}, {self.good.name}, {self.document.id}')
		self.print_tab()


