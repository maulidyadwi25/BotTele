from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
import uuid


db = SQLAlchemy()


def generate_uuid():
    return str(uuid.uuid4())


class GUID(db.TypeDecorator):
    impl = db.String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if not isinstance(value, str):
                value = str(value)
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value).bytes
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(bytes=value)
        return value


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    if 'sqlite' in str(type(dbapi_conn)):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


from .project import Project, ProjectMilestone
from .wbs import WbsItem
from .progress import WeeklyProgress
from .recovery import RecoveryPlan
from .action import ActionTracker
from .budget import BudgetControl, BudgetDetailLine
from .cashflow import CashflowIn, CashflowOut
from .vendor import Vendor
from .procurement import ProcurementItem, ProcurementPayment
from .proc_ops import ProcOpsStatus
from .proc_pol import ProcPolStatus
from .photo import ProjectPhoto
from .exchange import ExchangeRate
from .access import AdminUser, TelegramUser, FilePermission, UserGlobalAccess, SpreadsheetIndex

__all__ = [
    'db',
    'GUID',
    'generate_uuid',
    'Project',
    'ProjectMilestone',
    'WbsItem',
    'WeeklyProgress',
    'RecoveryPlan',
    'ActionTracker',
    'BudgetControl',
    'BudgetDetailLine',
    'CashflowIn',
    'CashflowOut',
    'Vendor',
    'ProcurementItem',
    'ProcurementPayment',
    'ProcOpsStatus',
    'ProcPolStatus',
    'ProjectPhoto',
    'ExchangeRate',
    # Access management models (migrated from access_manager)
    'AdminUser',
    'TelegramUser',
    'FilePermission',
    'UserGlobalAccess',
    'SpreadsheetIndex',
]
