from sqlalchemy import Index, Column, Index, BigInteger, String, Date, Integer, DateTime, func, Boolean, DateTime
 
from databases import Postgres

class LicenseDocument(Postgres.Base):
 
    __tablename__ = 'license_document'

    id          = Column(BigInteger, nullable=False, primary_key = True, autoincrement=True)
    ctime       = Column(DateTime, default=func.current_timestamp())
    mtime       = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    account_id  = Column(String, nullable=False)
    good_id     = Column(BigInteger, nullable=False)
    accepted    = Column(DateTime)

    Index('', account_id)

    def __repr__(self):
        return f'<LicenseDocument {self.id}, account_id={self.account_id}, good_id={self.good_id}, accepted={self.accepted}>'

LicenseDocumentTable = LicenseDocument.__table__
table= Postgres.Table(LicenseDocumentTable)
table.column('good_id').references('good')
table.column('account_id').references('account')


   