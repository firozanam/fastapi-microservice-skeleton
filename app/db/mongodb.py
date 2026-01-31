"""
MongoDB database client for document storage.
"""
from typing import Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global MongoDB client
mongo_client: Optional[AsyncIOMotorClient] = None
mongo_db: Optional[AsyncIOMotorDatabase] = None


async def get_mongo() -> AsyncIOMotorDatabase:
    """
    Get MongoDB database instance.

    Returns:
        AsyncIOMotorDatabase: MongoDB database

    Raises:
        RuntimeError: If MongoDB is not enabled in configuration

    Example:
        ```python
        @app.get("/content/{content_id}")
        async def get_content(content_id: str, db: AsyncIOMotorDatabase = Depends(get_mongo)):
            content = await db.content.find_one({"_id": content_id})
            return content
        ```
    """
    if not settings.ENABLE_MONGODB:
        raise RuntimeError(
            "MongoDB is not enabled. Set ENABLE_MONGODB=true in your configuration "
            "to use MongoDB database features."
        )
    
    if mongo_db is None:
        raise RuntimeError(
            "MongoDB client is not initialized. Ensure init_mongo() was called during startup."
        )
    
    return mongo_db


async def init_mongo() -> None:
    """
    Initialize MongoDB connection.
    
    This function checks if MongoDB is enabled before attempting initialization.
    If disabled, it logs an info message and returns early.
    """
    global mongo_client, mongo_db

    if not settings.ENABLE_MONGODB:
        logger.info("MongoDB is disabled - skipping initialization")
        return

    try:
        logger.info("Initializing MongoDB connection...")
        
        mongo_client = AsyncIOMotorClient(
            settings.MONGODB_URL, serverSelectionTimeoutMS=5000
        )
        mongo_db = mongo_client[settings.MONGODB_DB]

        # Test connection
        await mongo_client.admin.command("ping")
        logger.info("MongoDB connection established successfully")

    except Exception as e:
        logger.warning(
            "Failed to connect to MongoDB - continuing without MongoDB", error=str(e)
        )
        # Ensure globals remain None
        mongo_client = None
        mongo_db = None
        # Don't raise - allow app to start without MongoDB for development


async def close_mongo() -> None:
    """Close MongoDB connection."""
    global mongo_client

    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")


class MongoRepository:
    """Base repository for MongoDB operations."""

    def __init__(self, collection_name: str):
        """
        Initialize repository with collection name.

        Args:
            collection_name: Name of the MongoDB collection
        """
        self.collection_name = collection_name

    @property
    def collection(self):
        """Get MongoDB collection."""
        return mongo_db[self.collection_name]

    async def find_one(self, filter_dict: dict) -> Optional[dict]:
        """
        Find a single document.

        Args:
            filter_dict: Query filter

        Returns:
            Document or None
        """
        return await self.collection.find_one(filter_dict)

    async def find_many(
        self,
        filter_dict: dict = None,
        skip: int = 0,
        limit: int = 100,
        sort: list = None,
    ) -> list:
        """
        Find multiple documents.

        Args:
            filter_dict: Query filter
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort: Sort specification (e.g., [("created_at", -1)])

        Returns:
            List of documents
        """
        query = self.collection.find(filter_dict or {})

        if sort:
            query = query.sort(sort)

        if skip:
            query = query.skip(skip)

        if limit:
            query = query.limit(limit)

        return await query.to_list(length=limit)

    async def insert_one(self, document: dict) -> str:
        """
        Insert a single document.

        Args:
            document: Document to insert

        Returns:
            Inserted document ID
        """
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def update_one(
        self,
        filter_dict: dict,
        update_dict: dict,
    ) -> bool:
        """
        Update a single document.

        Args:
            filter_dict: Query filter
            update_dict: Update operations

        Returns:
            True if document was modified, False otherwise
        """
        result = await self.collection.update_one(
            filter_dict,
            {"$set": update_dict},
        )
        return result.modified_count > 0

    async def delete_one(self, filter_dict: dict) -> bool:
        """
        Delete a single document.

        Args:
            filter_dict: Query filter

        Returns:
            True if document was deleted, False otherwise
        """
        result = await self.collection.delete_one(filter_dict)
        return result.deleted_count > 0

    async def count_documents(self, filter_dict: dict = None) -> int:
        """
        Count documents matching filter.

        Args:
            filter_dict: Query filter

        Returns:
            Number of documents
        """
        return await self.collection.count_documents(filter_dict or {})

    async def aggregate(self, pipeline: list) -> list:
        """
        Execute aggregation pipeline.

        Args:
            pipeline: Aggregation pipeline

        Returns:
            List of results
        """
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)
