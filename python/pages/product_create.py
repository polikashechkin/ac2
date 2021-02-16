import sys, os
from domino.core import log

from _system.pages import Page as BasePage, Title, Text, Toolbar, Select, Table, Button, Input
from _system.tables.postgres.good import Good

class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)
        self.postgres = None

    def create(self):
        code = self.get('code')
        name = self.get('name')
        good = Good(code=code, name=name, state=0)
        self.postgres.add(good)
        self.message(f'{code}, {name}')

    def __call__(self):
        Title(self, 'Новый продукт')
        toolbar = Toolbar(self, 'toolbar')
        Input(toolbar.item(), label='Код', name='code')
        Input(toolbar.item(), label='Наименование', name='name')
        Button(toolbar.item(ml='auto'), 'Создать').onclick('.create', forms=[toolbar])


