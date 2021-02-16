import sys, os

from domino.core import log, DOMINO_ROOT
from domino.page_controls import TabControl
from domino.account import Account as AccountFolder, find_account_id

from _system.pages import Title, Text, Input, Toolbar, Select, FlatTable, Button, Rows, DeleteIconButton
from _system.pages import Page as BasePage
from _system.tables.postgres.account import Account, AccountTable

#from domino.tables.accountdb.license import License

from components.controls import Form as BaseForm

Form = BaseForm()
Form.column('account_id', 'Идентификатор учетной запиcи (account_id)')

class Page(BasePage):
    
    def __init__(self, application, request):
        super().__init__(application, request)
        self.postgres = None
    
    def create(self):
        try:
            account_id = self.get('account_id')
            id = find_account_id(account_id)
            if id is None:
                self.error(f'Не обнаружено учетной записи "{account_id}"')
                return
            a = AccountFolder(id)
            account = self.postgres.query(Account).get(a.id)
            if account:
                self.error(f'Учетная запись "{a.id} уже существует')
                return
            values = {
                Account.id          : a.id,
                Account.alias       : a.info.alias if a.info.alias else a.id,
                Account.name        : a.info.description,
                Account.password    : a.info.password
            }
            Account.insert(self.postgres, values)
            #account = Account(id=a.id, alias=a.info.alias, name=a.info.description)
            #account.password = a.info.password
            #self.postgres.add(account)
            #self.postgres.commit()
            self.message(f'{a.id}, {a.info.name}')

        except Exception as ex:
            self.error(ex)

    def __call__(self):
        Title(self, f'Создание/Добавление учетной записи.')
        Form(self, self.create)
        #table = FlatTable(self, 'table')
        #row = table.row('account_id')
        #row.cell().text('Идентификатор учетной запиаи (account_id)')
        #Input(row.cell(), name='account_id')
        #toolbar = Toolbar(self, 'toolbar').mt(1)
        #Button(toolbar.item(mr=0.5), 'Создать').css('btn-info').onclick(self.create, forms=[table])


