import sys, os

from domino.core import log

from _system.pages import Title, Text
from _system.pages.start_page import Page as BasePage

class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)
    
    def create_menu(self, menu):
        menu.item('Сертификаты/Учетные записи', 'pages/accounts')
        menu.item('Создать учетную запись/сертификат', 'pages/account_create')
        menu.item('Товары, являющиеся Лицензируемыыми продуктами', 'pages/products')
        menu.item('Зачвки на изменения', 'pages/license_documents')
        menu.item('Процедуры', 'domino/pages/procs')

