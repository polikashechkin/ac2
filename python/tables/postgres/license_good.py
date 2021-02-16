from sqlalchemy import Column, Index, String, Integer

from _system.components.licenses import Licenses
from _system.tables.postgres.good import Good

from databases import Postgres

class LicenseGood(Good):

	__tablename__ = Good.__tablename__
	__table_args__ = {'extend_existing': True}

	license_product_id = Column(String)
	object_type_id = Column(String)

	@property
	def object_type(self):
		return Licenses.ObjectType.get(self.object_type_id)

	def __repr__(self):
		#good = super().__repr__()
		return f'<Good id={self.id}, code={self.code}, name={self.name}, product={self.license_product_id}, object_type={self.object_type_id}>'

LicenseGoodTable = LicenseGood.__table__
Postgres.Table(LicenseGoodTable)
