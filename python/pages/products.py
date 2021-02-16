#import sys, os, enum
from enum import Enum as EnumBase

from domino.core import log
from domino.page_controls import TabControl

from _system.pages import Page as BasePage, Input, Title, Text, Toolbar, Select, Table, Rows, Button, EditIconButton, RefreshIconButton, CheckIconButton, CloseIconButton

from components import Licenses
from tables.postgres import Good

class Enum(EnumBase):
    __elements_by_id__ = {}

    def __str__(self):
        return self.value[1]
    
    @property
    def id(self):
        return self.value[0]
    
    @property
    def short_name(self):
        return self.value[1]
    
    @staticmethod
    def get(id, default = None):
        e = ShowMode.__elements_by_id__.get(id)
        return e if e else default

    @classmethod
    def items(cls):
        return cls.__elements_by_id__.items()
    
    @classmethod
    def init(cls):
        for e in cls:
            cls.__elements_by_id__[e.id] = e

class ShowMode(Enum):

    ALL_GOODS = ['all', 'Все товары']
    ONLY_PRODUCTS = ['only_products', 'Только лиценизируемые']

ShowMode.init()

#for e in ShowMode:
#    ShowMode.__elements_by_id__[e.id] = e

Tabs = TabControl('ProductTabs')
Tabs.item('only_product_tab', 'Товары, зарегистрированные ка продукты')
Tabs.item('all_goods_tab', 'Все товары')

class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)
        self.postgres = None

    @property
    def show_mode(self):
        return ShowMode.get(self.STORE.show_mode, ShowMode.ONLY_PRODUCTS)
    
    def change_show_mode(self):
        self.STORE.set(show_mode = self.get('show_mode'))
        self.print_tab()
        #self.message(self.show_mode)

    def refresh_row(self):
        good_id = self.get('good_id')
        good = self.postgres.query(Good).get(good_id)
        good.license_product_id = None
        good.object_type_id = None
        row = Rows(self, 'table').row(good_id)
        self.print_row(row, good)

    def close_row(self):
        good_id = self.get('good_id')
        good = self.postgres.query(Good).get(good_id)
        row = Rows(self, 'table').row(good_id)
        self.print_row(row, good)
    
    def save_row(self):
        good_id = self.get('good_id')
        license_product_id = self.get('license_product_id')
        object_type_id = self.get('object_type_id')
        if not object_type_id:
            self.error('Метрику следует определить')
            return
        good = self.postgres.query(Good).get(good_id)
        good.license_product_id = license_product_id
        good.object_type_id = object_type_id
        row = Rows(self, 'table').row(good_id)
        self.print_row(row, good)

    def edit_row(self):
        good_id = self.get('good_id')
        good = self.postgres.query(Good).get(good_id)
        row = Rows(self, 'table').row(good_id)
        self.print_row(row, good, edit=True)

    def print_row(self, row, good, edit = False):
        if edit:
            row.css('table-warning')

        row.cell(wrap=False, width=2).text(good.code)
        row.cell().href(good.name, '')
        
        cell = row.cell(width=20)
        if edit:
            Input(cell, name='license_product_id', value=good.license_product_id)
        else:
            cell.text(good.license_product_id)

        cell = row.cell(width=20)
        if edit:
            select = Select(cell, name='object_type_id', value=good.object_type_id)
            for t in Licenses.ObjectType:
                select.option(t.id, f'{t}')
        else:
            cell.text(good.object_type)

        cell = row.cell(width=4, wrap=None, align='right')
        if edit:
            CheckIconButton(cell, True).onclick(self.save_row, {'good_id':good.id}, forms=[row])
            CloseIconButton(cell).onclick(self.close_row, {'good_id':good.id})
        else:
            EditIconButton(cell).onclick(self.edit_row, {'good_id':good.id})
            RefreshIconButton(cell).onclick(self.refresh_row, {'good_id':good.id})

    def print_table(self):
        table = Table(self, 'table').mt(1)
        table.column('Код')
        table.column('Наименование')
        table.column('Продукт')
        table.column('Метрика')
        query = self.postgres.query(Good)
        if self.show_mode == ShowMode.ONLY_PRODUCTS:
            query = query.filter(Good.object_type_id != None)
        for good in query:
            row = table.row(good.id)
            self.print_row(row, good)
    
    def print_tab(self):
        toolbar = Toolbar(self, 'toolbar')
        Text(toolbar.item(ml='auto'))
        for e in ShowMode:
            button = Button(toolbar.item(), f'{e}')
            if e.id == self.show_mode.id:
                button.style('background-color:black; color:white')
            button.onclick(self.change_show_mode, {'show_mode':e.id})
        self.print_table()

    def __call__(self):
        self.STORE.var('show_mode', ShowMode.ALL_GOODS)
        Title(self, 'Продукты')
        self.print_tab()

