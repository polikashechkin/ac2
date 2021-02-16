from sqlalchemy import Index, Column, Index, BigInteger, String, Date, Integer, DateTime, func

from domino.core import log 

from _system.databases import Postgres
from _system.tables.postgres.good import GoodTable

from .license_object import LicenseObjectTable

class License(Postgres.Base):
 
    __tablename__ = 'license'

    id          = Column(BigInteger, nullable=False, primary_key = True, autoincrement=True)
    ctime       = Column(DateTime, default=func.current_timestamp())
    mtime       = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    account_id  = Column(String, nullable=False)
    good_id     = Column(BigInteger, nullable=False)
    object_id   = Column(BigInteger)
    exp_date    = Column(Date)
    name        = Column(String)
    qty         = Column(Integer, default = 0)
    info        = Column(Postgres.JSON)

    Index('', account_id, good_id, object_id, unique=True)

LicenseTable = License.__table__
table = Postgres.Table(LicenseTable)
table.column(License.good_id.name).references(GoodTable.name)
table.column(License.object_id.name).references(LicenseObjectTable.name)
