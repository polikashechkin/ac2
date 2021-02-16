import sys, os, datetime
from sqlalchemy import insert

from domino.core import log

from _system.pages import Title, Text, Toolbar, Select, Table, Input, Button
from _system.pages import Page as BasePage
from _system.tables.postgres.account import Account
from _system.tables.postgres.good import Good

from components.controls import Form as BaseForm
from tables.postgres.license import License
from tables.postgres.license_object import LicenseObject

Form = BaseForm()
Form.column('product_id', 'Продукт', options='good_options')
Form.column('object_id', 'Объект лицензирования', options='object_options')

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
        self.postgres.execute(insert(License, values))
        self.message(f'{values}')
    
    def good_options(self):
        options = []
        for good in self.postgres.query(Good):
            options.append((good.code, good.name))
        return options

    def object_options(self):
        options = []
        for obj in self.postgres.query(LicenseObject).filter(LicenseObject.account_id == self.account.id).order_by(LicenseObject.name):
            options.append((obj.id, f'{obj.code}, {obj.name}'))
        return options

    def __call__(self):
        Title(self, f'Создать лицензию для {self.account.id} {self.account.name}')
        Form(self, self.create)
