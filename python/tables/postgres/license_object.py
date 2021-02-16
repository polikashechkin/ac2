from sqlalchemy import Column, Index, BigInteger, String, Date, DateTime, func as F

from domino.core import log 

from _system.components.licenses import LicenseObjectType
from _system.databases import Postgres

class LicenseObject(Postgres.Base):

    Type = LicenseObjectType

    __tablename__ = 'license_object'

    id          = Column(BigInteger, nullable=False, primary_key = True, autoincrement=True)
    ctime       = Column(DateTime, default=F.current_timestamp())
    mtime       = Column(DateTime, default=F.current_timestamp(), onupdate=F.current_timestamp())
    account_id  = Column(String, nullable=False)
    object_type_id  = Column('type', String, nullable=False)
    code        = Column(String, nullable=False)
    name        = Column(String)
    description = Column(String)
    address     = Column(String)
    guid        = Column(String)
    serial_no   = Column(String)
    mark_no     = Column(String)
    hasp_party  = Column(String)
    hasp_type   = Column(String)
    pwd1        = Column(String)
    pwd2        = Column(String)
    #info        = Column(Postgres.JSON)

    Index('', account_id, object_type_id, code, unique=True)

    
    #@property
    #def get(postgres, object_type, object_id):
    #    return postgres.query(LicenseObject).filter(LicenseObject.t_id == object_type.id, LicenseObject.code)

    @property
    def t_id(self):
        return self.object_type_id

    @property
    def object_type(self):
        return LicenseObjectType.get(self.object_type_id)

#    @property
#    def t(self):
#        return LicenseObjectType.get(self.t_id)
    
    def __repr__(self):
        return f'<LicenseObject account_id={self.account_id}, object_type={self.object_type}, code={self.code}, name={self.name}>'


LicenseObjectTable = LicenseObject.__table__
Postgres.Table(LicenseObjectTable)
