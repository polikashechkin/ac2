from sqlalchemy import Index, Column, Index, BigInteger, String, Date, Integer, DateTime, func

from databases import Postgres

class LicenseDocumentLine(Postgres.Base):
 
    __tablename__ = 'license_document_line'
   
    id          = Column(BigInteger, nullable=False, primary_key = True, autoincrement=True)
    ctime       = Column(DateTime, nullable=False, default=func.current_timestamp())
    mtime       = Column(DateTime, nullable=False, default=func.current_timestamp(), onupdate=func.current_timestamp())
    document_id = Column(BigInteger, nullable=False)
    object_id   = Column(BigInteger)
    qty         = Column(Integer, nullable=False, default=1)
    exp_date    = Column(Date, nullable=False)

    Index('', document_id)

    def __repr_(self):
        return f'<LicenseDocumentLine {self.id}, document_id={self.document_id}, object_id={self.object_id}, qty={self.qty}, exp_date={exp_date}>'

LicenseDocumentLineTable = LicenseDocumentLine.__table__
table = Postgres.Table(LicenseDocumentLineTable)
table.column('document_id').references('license_document', on_delete='cascade')
table.column('object_id').references('license_object')


 







