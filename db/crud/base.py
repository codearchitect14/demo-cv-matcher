# File: db/crud/base.py
from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """Get single record by ID"""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records with pagination"""
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        """Create new record with optimized performance"""
        import time
        start_time = time.time()
        
        try:
            obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else (obj_in.dict() if hasattr(obj_in, 'dict') else obj_in)
            
            # Handle enum conversion for status field if it exists
            if 'status' in obj_data and hasattr(obj_data['status'], 'value'):
                obj_data['status'] = obj_data['status'].value
            
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            # Flush to assign primary key without issuing a SELECT
            await db.flush()
            await db.commit()
            
            elapsed = time.time() - start_time
            if elapsed > 0.5:  # Log slow creates
                logger.warning(f"Slow database create operation: {elapsed:.3f}s for {self.model.__name__}")
            
            # Do NOT refresh to avoid prepared SELECT; caller can re-query if needed
            return db_obj
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Database create failed after {elapsed:.3f}s: {e}")
            await db.rollback()
            raise

    async def update(
        self, db: AsyncSession, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update existing record without refresh"""
        update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await db.commit()
        # Avoid refresh to prevent prepared statements
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """Delete record by ID"""
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
