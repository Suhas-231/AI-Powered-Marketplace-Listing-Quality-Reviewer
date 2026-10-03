import logging
from typing import Dict, Any, Optional
from app.database import db
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)

class AuditService:
    @staticmethod
    def log(entity_type: str, entity_id: int, action: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> AuditLog:
        """
        Creates and persists a persistent audit log record in database.
        """
        try:
            entry = AuditLog(
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                details=details or {}
            )
            db.session.add(entry)
            db.session.commit()
            logger.info(f"AUDIT LOG: [{entity_type}:{entity_id}] action='{action}' user_id={user_id}")
            return entry
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to record audit log: {e}")
            return None
