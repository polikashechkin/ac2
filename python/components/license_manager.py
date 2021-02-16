from datetime import datetime
from sqlalchemy import or_, and_

from domino.core import log
from tables.postgres import LicenseDocument, LicenseDocumentLine, Good, License, LicenseObject

class LicenseManager:

	def __init__(self, postgres):
		self.postgres = postgres

	def acccept(self, license_dcoument):
		assert not license_dcoument.accepted, 'Документ уже утвержден'
		good = self.postgres.quey(Good).get(LicenseDocument.good_id)
		object_type = good.object_type
		assert object_type, 'Не определена метрика лицензируемого продукта'
		query = self.postgres.query(LicenseDocumentLine)\
			.filter(LicenseDocumentLine.document_id == license_dcoument.id)

		for line in query:
			assert line.qty, 'Не задано количество в строке'
			assert line.exp_date, 'Не задан срок действия лицензии в строке'
			assert line.object_id, 'Не задан объект лицензирования в строке'
			lis = self.postgres.query(License).filter(License.product_id == good.id, License.object_id == line.object_id).one()
			if lis:
				if lis.exp_date < line.exp_date:
					lis.exp_date = line.exp_date
				else:
					lis = License(account_id = license_dcoument.account_id, product_id =  good.id, object_id = line.object_id,  qty = line.qty, exp_date = line.exp_date)
					self.postgres.add(lis)
		license_dcoument.accepted = datetime.now()


