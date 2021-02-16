import sys, os

from domino.core import log, DOMINO_ROOT
from domino.account import Account as AccountFolder, find_account_id

from _system.components.licenses import Licenses
from _system.pages import Title, Text, Toolbar, Select, Table, Rows, Button, Input
from _system.pages import DeleteIconButton, RefreshIconButton
from _system.pages import Page as BasePage
from _system.tables.postgres.account import Account
from _system.tables.postgres.good import Good

from tables.postgres.license import License
from tables.postgres.license_object import LicenseObject

class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)
        self.postgres = None

    def refresh(self):
        try:
            msg = []
            account_id = self.get('license_account_id')
            row = Rows(self, 'table').row(account_id)
            a = AccountFolder(account_id)
            account = self.postgres.query(Account).get(account_id)
            account.name = a.info.description
            if a.info.password:
                account.password = f'{a.info.password}' 
            account.alias =  a.info.alias
            self.postgres.commit()
            # -----------------------------------------
            account_folder = os.path.join(DOMINO_ROOT, 'accounts', a.id)
            account_alias_folder = os.path.join(DOMINO_ROOT, 'accounts.alias')
            alias = a.info.alias
            if alias:
                symlink = os.path.join(account_alias_folder, alias)
            else:
                symlink = os.path.join(account_alias_folder, a.id)
            os.makedirs(account_alias_folder, exist_ok=True)
            if not os.path.exists(symlink):
                os.symlink(account_folder, symlink)
                msg.append(f'Добавлена ссылка "{symlink}"')
            # -----------------------------------------
            sft = Licenses.Sft(account.id)
            query = self.postgres.query(License, Good, LicenseObject)\
                .filter(License.account_id == account.id)\
                .outerjoin(Good, Good.code == License.product_id)\
                .outerjoin(LicenseObject, LicenseObject.id == License.object_id)

            for l, good, obj in query:
                #log.debug(f'{obj}')
                license = Licenses.License(product_id=l.product_id, object_type = obj.t_id, object_id = obj.code, exp_date=l.exp_date)
                sft.add(license)
            sft.save()
            msg.append(f'Создано/обновлен сертификат "{sft.file}"')
            # -----------------------------------------
            self.print_row(row, account)
            self.message(', '.join(msg))
            
        except Exception as ex:
            self.error(ex)

    def print_table(self):
        toolbar = Toolbar(self, 'toolbar') 
        #Input(toolbar.item(), name='filter', placeholder='Поиск...')
        #Button(toolbar.item(ml='auto'), 'Добавить')\
        #    .style('background-color:green; color:white').onclick('pages/account_create')
        #Button(toolbar.item(ml=0.1), 'Удалить')\
        #    .style('background-color:red; color:white').onclick(self.delete, forms=[toolbar])
 
        table = Table(self, 'table').mt(0.1)
        table.column().text('#')
        table.column('Псевдоним')
        table.column().text('Описание')
        table.column().text('Пароль')
        #table.column().text('Сертификат')
        #table.column()
        for account in self.postgres.query(Account).order_by(Account.name):
            row = table.row(account.id)
            self.print_row(row, account)

    def print_row(self, row, account):
        #sft = Licenses.Sft(account.id)
        row.cell(width=1).href(f'{account.id}', 'pages/account', {'license_account_id':account.id})
        cell = row.cell(width=1)
        if account.alias and account.alias != account.id:
            cell.text(f'{account.alias}')
        row.cell().text(f'{account.name}')
        row.cell().text(f'{account.password}')
        #cell = row.cell()
        #if os.path.isfile(sft.file):
        #    cell.href(f'{sft.file}', 'pages/sft', {'license_account_id':account.id})
        #row.cell().href(f'Лицензии', 'pages/active_licenses', {'license_account_id':account.id})
        RefreshIconButton(row.cell(width=2)).onclick(self.refresh, {'license_account_id':account.id})

    def __call__(self):
        Title(self, 'Сертификаты/Учетные записи')
        self.print_table()


