from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db import Base


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    service = Column(String(128), nullable=True)
    function = Column(String(256), nullable=True)
    exception_type = Column(String(128), nullable=False)
    message = Column(Text, nullable=True)      # short message (str(exc))
    traceback = Column(Text, nullable=True)    # full stack trace
    severity = Column(String(32), nullable=True)
    request_path = Column(String(512), nullable=True)
    http_method = Column(String(16), nullable=True)

    def __repr__(self) -> str:
        return f"<ErrorLog id={self.id} type={self.exception_type} service={self.service}>"
