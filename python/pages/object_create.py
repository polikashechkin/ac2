import sys, os, datetime
from sqlalchemy import insert

from domino.core import log

from _system.components.licenses import LicenseObjectType
from _system.pages import Title, Text, Toolbar, Select, Table, FlatTable, Input, Button
from _system.pages import Page as BasePage
from _system.tables.postgres.account import Account
from _system.tables.postgres.good import Good

from components.controls import Form as BaseForm
from tables.postgres.license_object import LicenseObject

Form = BaseForm()
Form.column('type', 'Тип', options = LicenseObjectType.items())
Form.column('code', 'Код')
Form.column('name', 'Наименование')

class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)
        self.postgres = None
        self.license_account_id = self.attribute('license_account_id')
        self._account = None
    
    @property
    def account(self):
        if self._account is None:
            self._account = self.postgres.query(Account).get(self.license_account_id)
        return self._account

    def create(self):
        values = Form.values(self)
        values['account_id'] = self.license_account_id
        ins = insert(LicenseObject, values)
        self.postgres.execute(ins)
        self.message(f'{values}')

    def __call__(self):
        Title(self, f'Создать объект для {self.account.id} {self.account.name}')
        Form(self, create = self.create)


