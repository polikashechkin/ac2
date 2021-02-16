import sys, os, datetime
from sqlalchemy import insert
from lxml import etree as ET

from domino.core import log, DOMINO_ROOT
from domino.page_controls import TabControl

from _system.pages import Title, Text, Toolbar, Select, Table, Button, Rows, DeleteIconButton, TextWithComments, FlatButton, DangerButton, PrimaryButton
from _system.pages import IconButton, DeleteIconButton
from _system.pages import Page as BasePage


from enums import Unit
from components import LicenseManager, Licenses

from tables.postgres import License, Good, LicenseObject, LicenseDocument, Account


LICNSE_ACCOUNT_ID = 'license_account_id'
GOOD_ID = 'good_id'

class Page(BasePage):

	ID = 'pages/license_documents'
	
	def __init__(self, application, request):
		super().__init__(application, request)
		self.postgres = None
	
	@property
	def license_account_id(self):
		return self.STORE.get(LICNSE_ACCOUNT_ID)
	
	@license_account_id.setter
	def license_account_id(self, value):
		self.STORE[LICNSE_ACCOUNT_ID] = value
	
	@property
	def good_id(self):
		return self.STORE.get(GOOD_ID)

	@good_id.setter
	def good_id(self, value):
		self.STORE[GOOD_ID] = value

	def delete_not_accepted_documents(self):
		query = self.postgres.query(LicenseDocument).filter(LicenseDocument.accepted == False)
		
		self.licence_account_id = self.get(LICNSE_ACCOUNT_ID)
		if self.licence_account_id:
			query = query.filter(LicenseDocument.account_id == self.licence_account_id)
		
		self.good_id = self.get(GOOD_ID)
		if self.good_id:
			query = query.filter(LicenseDocument.good_id == self.good_id)

		query.delete()
		self.print_tab()

	def change_query(self):
		self.license_account_id = self.get(LICNSE_ACCOUNT_ID)
		self.good_id = self.get(GOOD_ID)
		self.print_tab()

	def print_tab(self):
		toolbar = Toolbar(self, 'toolbar')
		
		select = Select(toolbar.item(mr=0.5), name = LICNSE_ACCOUNT_ID, value=self.license_account_id)\
			.onchange(self.change_query, forms=[toolbar])
		select.option('','<Все учетные записи>')
		for account in self.postgres.query(Account):
			select.option(account.id, account.name if account.name else account.id)

		select = Select(toolbar.item(), name = GOOD_ID, value=self.good_id)\
			.onchange(self.change_query, forms=[toolbar])
		select.option('','<Все продукты>')
		for good in self.postgres.query(Good).filter(Good.object_type_id != None).order_by(Good.name):
			select.option(good.id, good.name)
		
		btn = Button(toolbar.item(ml='auto'), 'Удалить')
		btn.item(f'Удалить все не утвержденные заявки').onclick(self.delete_not_accepted_documents, forms=[toolbar])
		
		self.print_table()
		
	def print_table(self, license_account_id = None):

		query = self.postgres.query(LicenseDocument, Good, Account)\
			.join(Account, Account.id == LicenseDocument.account_id)\
			.join(Good, Good.id == LicenseDocument.good_id)

		#license_account_id = self.get('license_account_id')
		if self.license_account_id:
			query = query.filter(LicenseDocument.account_id == self.license_account_id)

		#good_id = self.get('good_id')
		if self.good_id:
			query = query.filter(LicenseDocument.good_id == self.good_id)

		table = Table(self, 'table').mt(1)
		table.column()
		table.column().text('#')
		table.column().text('Учетная запись')
		table.column().text('Продукт')
		#table.column().text('Создание')
		table.column()
			
		for doc, good, account in query.order_by(LicenseDocument.id.desc()).limit(100):
			row = table.row(doc.id)
			self.print_row(row, doc, good, account)

	def print_row(self, row, doc, good, account):
		#cell = row.cell(wrap=False, width=1).onclick(self.delete_document)
		#Text(cell).glif('check')

		text = Text(row.cell(width=2))
		text.glif('check ', style = 'color:green' if doc.accepted else 'color:lightgray' )

		row.cell(width=2).text(doc.id).tooltip(f'{doc.ctime}')

		row.cell(width=2, wrap=False).text(account.name  if account.name else account.id)

		row.cell().href(good.name, 'pages/license_document', {'document_id' : doc.id})
		#row.cell().text(doc.ctime)

		cell = row.cell(width=1, wrap=False, align='right')
		PrimaryButton(cell, 'Утвердить').onclick(self.accept_document, {'document_id':doc.id})
		DeleteIconButton(cell).onclick(self.delete_document, {'document_id':doc.id})
		#Text(cell).glif('times', style='-font-size:small; color:red')
		#cell.onclick(self.delete_document, {'document_id':doc.id})

	def accept_document(self):
		document_id = self.get('document_id')
		assert document_id
		document = self.postgres.query(LicenseDocument).get(document_id)
		try:
			manager = LicenseManager(self.postgres)
			manager.accept(document)
		except Exception as ex:
			log.exception(__file__)
			self.error(ex)
			return
		account = self.postgres.query(Account).get(document.account_id)
		good = self.postgres.query(Good).get(document.good_id)
		row = Rows(self, 'table').row(document_id)
		self.print_row(row, document, good, account)

	def delete_document(self):
		document_id = self.get('document_id')
		assert document_id
		self.postgres.query(LicenseDocument).filter(LicenseDocument.id == document_id).delete()
		Rows(self, 'table').row(document_id)
		#self.message('Удален документ delete') 

	def __call__(self):
		Title(self, f'Заявки на изменения')
		self.print_tab()
