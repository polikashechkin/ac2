import sys, os

from domino.core import log

from _system.components.licenses import Licenses
from _system.pages import Title, Text, Toolbar, Select, Table, Button, Rows, DeleteIconButton
from _system.pages import Page as BasePage
from _system.tables.postgres.account import Account
from _system.tables.postgres.good import Good
 
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

    def __call__(self):
        Title(self, f'Активные лицензии')
        store = Licenses.Store(self.account.id)
        table = Table(self, 'table')
        for license in store.getall():
            row = table.row()
            row.cell().text(license.js)




