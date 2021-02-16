from _system.pages import Text, Toolbar, Select, Table, FlatTable, Input, Button

class Form:
    class Column:
        def __init__(self, id, name, options = None):
            self.id = id
            self.name = name
            self.options = options

        def print(self, page, table):
            row = table.row(self.id)
            row.cell().text(self.name)
            cell = row.cell()
            if self.options:
                select = Select(cell, name=self.id)
                if isinstance(self.options, str):
                    for key, name in getattr(page, self.options)():
                        select.option(key, f'{name}')
                else:
                    for key, name in self.options:
                        select.option(key, f'{name}')
            else:
                Input(cell, name=self.id)

    def __init__(self, id = 'form'):
        self.id = id
        self.columns = []
    
    @property
    def ID(self):
        return self.id
    
    def column(self, id, name, options=None):
        self.columns.append(Form.Column(id, name, options=options))

    def __call__(self, page, create=None):
        table = FlatTable(page, self.id)
        for column in self.columns:
            column.print(page, table)
        if create:
            toolbar = Toolbar(page, f'{self.id}_toolbar')
            Button(toolbar.item(ml='auto'),'Создать').onclick(create, forms=[table]).style('background-color:green;color:white')


    def values(self, page):
        values = {}
        for column in self.columns:
            values[column.id] = page.get(column.id)
        return values
