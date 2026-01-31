"""
Unit tests for MongoDB database module.
Tests MongoDB initialization, connection, and MongoRepository operations.

Note: All tests in this file require MongoDB to be enabled (ENABLE_MONGODB=true).
Tests will be automatically skipped if MongoDB is disabled.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.db.mongodb import (
    MongoRepository,
    close_mongo,
    get_mongo,
    init_mongo,
    mongo_client,
    mongo_db,
)


# Mark all tests in this module as requiring MongoDB
pytestmark = pytest.mark.mongodb


@pytest.mark.unit
class TestInitMongo:
    """Test MongoDB initialization."""

    @pytest.mark.asyncio
    async def test_init_mongo_success(self):
        """Test successful MongoDB initialization."""
        from app.db import mongodb as mongodb_module
        
        with patch("app.db.mongodb.AsyncIOMotorClient") as mock_client_class:
            mock_client = AsyncMock(spec=AsyncIOMotorClient)
            mock_db = MagicMock(spec=AsyncIOMotorDatabase)
            mock_client.__getitem__ = MagicMock(return_value=mock_db)
            mock_admin = MagicMock()
            mock_admin.command = AsyncMock(return_value=True)
            mock_client.admin = mock_admin
            mock_client_class.return_value = mock_client

            await init_mongo()

            mock_client_class.assert_called_once()
            mock_admin.command.assert_called_once_with("ping")
            assert mongodb_module.mongo_client == mock_client
            assert mongodb_module.mongo_db == mock_db

    @pytest.mark.asyncio
    async def test_init_mongo_connection_error(self):
        """Test MongoDB initialization with connection error."""
        from app.db import mongodb as mongodb_module
        
        with patch("app.db.mongodb.AsyncIOMotorClient") as mock_client_class:
            mock_client = AsyncMock(spec=AsyncIOMotorClient)
            mock_admin = MagicMock()
            mock_admin.command = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client.admin = mock_admin
            mock_client_class.return_value = mock_client

            # Should not raise exception
            await init_mongo()

            assert mongodb_module.mongo_client is None
            assert mongodb_module.mongo_db is None


@pytest.mark.unit
class TestCloseMongo:
    """Test MongoDB connection closing."""

    @pytest.mark.asyncio
    async def test_close_mongo_success(self):
        """Test successful MongoDB connection closing."""
        from app.db import mongodb as mongodb_module
        
        mock_client_instance = AsyncMock(spec=AsyncIOMotorClient)
        mock_client_instance.close = AsyncMock()
        
        with patch.object(mongodb_module, 'mongo_client', mock_client_instance):
            await close_mongo()
            mock_client_instance.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_mongo_when_client_is_none(self):
        """Test closing MongoDB when client is None."""
        global mongo_client
        mongo_client = None

        # Should not raise exception
        await close_mongo()


@pytest.mark.unit
class TestGetMongo:
    """Test get_mongo dependency function."""

    @pytest.mark.asyncio
    async def test_get_mongo_returns_database(self):
        """Test that get_mongo returns global mongo_db."""
        from app.db import mongodb as mongodb_module
        
        mock_db_instance = MagicMock(spec=AsyncIOMotorDatabase)
        
        with patch.object(mongodb_module, 'mongo_db', mock_db_instance):
            result = await get_mongo()
            assert result == mock_db_instance


@pytest.mark.unit
class TestMongoRepositoryInit:
    """Test MongoRepository initialization."""

    def test_mongo_repository_init(self):
        """Test MongoRepository initialization."""
        from app.db import mongodb as mongodb_module
        
        mock_mongo_db = MagicMock(spec=AsyncIOMotorDatabase)
        mock_collection = MagicMock()
        mock_mongo_db.__getitem__ = MagicMock(return_value=mock_collection)

        with patch.object(mongodb_module, 'mongo_db', mock_mongo_db):
            repo = MongoRepository("test_collection")

            assert repo.collection_name == "test_collection"
            assert repo.collection == mock_collection


@pytest.mark.unit
class TestMongoRepositoryFindOne:
    """Test MongoRepository find_one method."""

    @pytest.mark.asyncio
    async def test_find_one_success(self):
        """Test successful find_one."""
        mock_collection = AsyncMock()
        mock_doc = {"id": "123", "name": "test"}
        mock_collection.find_one = AsyncMock(return_value=mock_doc)

        with patch("app.db.mongodb.mongo_db") as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            repo = MongoRepository("test_collection")

            result = await repo.find_one({"id": "123"})

            assert result == mock_doc
            mock_collection.find_one.assert_called_once_with({"id": "123"})

    @pytest.mark.asyncio
    async def test_find_one_not_found(self):
        """Test find_one when document doesn't exist."""
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)

        with patch("app.db.mongodb.mongo_db") as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            repo = MongoRepository("test_collection")

            result = await repo.find_one({"id": "123"})

            assert result is None


@pytest.mark.unit
class TestMongoRepositoryFindMany:
    """Test MongoRepository find_many method."""

    @pytest.mark.asyncio
    async def test_find_many_success(self):
        """Test successful find_many."""
        from app.db import mongodb as mongodb_module
        
        mock_db = MagicMock(spec=AsyncIOMotorDatabase)
        mock_collection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_docs = [{"id": "1"}, {"id": "2"}]
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        mock_collection.find = AsyncMock(return_value=mock_cursor)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        with patch.object(mongodb_module, 'mongo_db', mock_db):
            repo = MongoRepository("test_collection")
            result = await repo.find_many()
            assert result == mock_docs

    @pytest.mark.asyncio
    async def test_find_many_with_filter(self):
        """Test find_many with filter."""
        from app.db import mongodb as mongodb_module
        
        mock_db = MagicMock(spec=AsyncIOMotorDatabase)
        mock_collection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_docs = [{"id": "1"}]
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        mock_collection.find = AsyncMock(return_value=mock_cursor)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        with patch.object(mongodb_module, 'mongo_db', mock_db):
            repo = MongoRepository("test_collection")
            result = await repo.find_many(filter_dict={"status": "active"})
            assert result == mock_docs
            mock_collection.find.assert_called_once_with({"status": "active"})

    @pytest.mark.asyncio
    async def test_find_many_with_skip_and_limit(self):
        """Test find_many with skip and limit."""
        from app.db import mongodb as mongodb_module
        
        mock_db = MagicMock(spec=AsyncIOMotorDatabase)
        mock_collection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_docs = [{"id": "2"}]
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        mock_query = MagicMock()
        mock_query.skip = MagicMock(return_value=mock_query)
        mock_query.limit = MagicMock(return_value=mock_cursor)
        mock_collection.find = AsyncMock(return_value=mock_query)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        with patch.object(mongodb_module, 'mongo_db', mock_db):
            repo = MongoRepository("test_collection")
            result = await repo.find_many(skip=10, limit=5)
            assert result == mock_docs
            mock_query.skip.assert_called_once_with(10)
            mock_query.limit.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_find_many_with_sort(self):
        """Test find_many with sort."""
        from app.db import mongodb as mongodb_module
        
        mock_db = MagicMock(spec=AsyncIOMotorDatabase)
        mock_collection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_docs = [{"id": "2"}]
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        mock_query = MagicMock()
        mock_query.sort = MagicMock(return_value=mock_cursor)
        mock_collection.find = AsyncMock(return_value=mock_query)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        with patch.object(mongodb_module, 'mongo_db', mock_db):
            repo = MongoRepository("test_collection")
            result = await repo.find_many(sort=[("created_at", -1)])
            assert result == mock_docs
            mock_query.sort.assert_called_once_with([("created_at", -1)])

    @pytest.mark.asyncio
    async def test_find_many_with_sort_skip_and_limit(self):
        """Test find_many with sort, skip, and limit together."""
        from app.db import mongodb as mongodb_module
        
        mock_db = MagicMock(spec=AsyncIOMotorDatabase)
        mock_collection = MagicMock()
        mock_docs = [{"id": "3"}]
        
        # Create a chain of mocks that supports all operations
        mock_final_cursor = AsyncMock()
        mock_final_cursor.to_list = AsyncMock(return_value=mock_docs)
        
        mock_skip_cursor = MagicMock()
        mock_skip_cursor.limit = MagicMock(return_value=mock_final_cursor)
        
        mock_sort_cursor = MagicMock()
        mock_sort_cursor.skip = MagicMock(return_value=mock_skip_cursor)
        
        mock_query = MagicMock()
        mock_query.sort = MagicMock(return_value=mock_sort_cursor)
        
        mock_collection.find = MagicMock(return_value=mock_query)
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        
        with patch.object(mongodb_module, 'mongo_db', mock_db):
            repo = MongoRepository("test_collection")
            result = await repo.find_many(
                filter_dict={"active": True},
                sort=[("created_at", -1)],
                skip=10,
                limit=20
            )
            assert result == mock_docs
            mock_collection.find.assert_called_once_with({"active": True})
            mock_query.sort.assert_called_once_with([("created_at", -1)])
            mock_sort_cursor.skip.assert_called_once_with(10)
            mock_skip_cursor.limit.assert_called_once_with(20)


@pytest.mark.unit
class TestMongoRepositoryInsertOne:
    """Test MongoRepository insert_one method."""

    @pytest.mark.asyncio
    async def test_insert_one_success(self):
        """Test successful insert_one."""
        mock_collection = AsyncMock()
        mock_result = MagicMock()
        mock_result.inserted_id = "123456"
        mock_collection.insert_one = AsyncMock(return_value=mock_result)

        with patch("app.db.mongodb.mongo_db") as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            repo = MongoRepository("test_collection")

            result = await repo.insert_one({"name": "test"})

            assert result == "123456"
            mock_collection.insert_one.assert_called_once_with({"name": "test"})


@pytest.mark.unit
class TestMongoRepositoryUpdateOne:
    """Test MongoRepository update_one method."""

    @pytest.mark.asyncio
    async def test_update_one_success(self):
        """Test successful update_one."""
        mock_collection = AsyncMock()
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_collection.update_one = AsyncMock(return_value=mock_result)

        with patch("app.db.mongodb.mongo_db") as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            repo = MongoRepository("test_collection")

            result = await repo.update_one({"id": "123"}, {"name": "updated"})

            assert result is True
            mock_collection.update_one.assert_called_once_with({"id": "123"}, {"$set": {"name": "updated"}})

    @pytest.mark.asyncio
    async def test_update_one_no_match(self):
        """Test update_one when no document matches."""
        mock_collection = AsyncMock()
        mock_result = MagicMock()
        mock_result.modified_count = 0
        mock_collection.update_one = AsyncMock(return_value=mock_result)

        with patch("app.db.mongodb.mongo_db") as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            repo = MongoRepository("test_collection")

            result = await repo.update_one({"id": "123"}, {"name": "updated"})

            assert result is False


@pytest.mark.unit
class TestMongoRepositoryDeleteOne:
    """Test MongoRepository delete_one method."""

    @pytest.mark.asyncio
    async def test_delete_one_success(self):
        """Test successful delete_one."""
        mock_collection = AsyncMock()
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mock_collection.delete_one = AsyncMock(return_value=mock_result)

        with patch("app.db.mongodb.mongo_db") as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            repo = MongoRepository("test_collection")

            result = await repo.delete_one({"id": "123"})

            assert result is True
            mock_collection.delete_one.assert_called_once_with({"id": "123"})

    @pytest.mark.asyncio
    async def test_delete_one_no_match(self):
        """Test delete_one when no document matches."""
        mock_collection = AsyncMock()
        mock_result = MagicMock()
        mock_result.deleted_count = 0
        mock_collection.delete_one = AsyncMock(return_value=mock_result)

        with patch("app.db.mongodb.mongo_db") as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            repo = MongoRepository("test_collection")

            result = await repo.delete_one({"id": "123"})

            assert result is False


@pytest.mark.unit
class TestMongoRepositoryCountDocuments:
    """Test MongoRepository count_documents method."""

    @pytest.mark.asyncio
    async def test_count_documents_success(self):
        """Test successful count_documents."""
        mock_collection = AsyncMock()
        mock_collection.count_documents = AsyncMock(return_value=5)

        with patch("app.db.mongodb.mongo_db") as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            repo = MongoRepository("test_collection")

            result = await repo.count_documents()

            assert result == 5
            mock_collection.count_documents.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_count_documents_with_filter(self):
        """Test count_documents with filter."""
        mock_collection = AsyncMock()
        mock_collection.count_documents = AsyncMock(return_value=3)

        with patch("app.db.mongodb.mongo_db") as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            repo = MongoRepository("test_collection")

            result = await repo.count_documents({"status": "active"})

            assert result == 3
            mock_collection.count_documents.assert_called_once_with({"status": "active"})


@pytest.mark.unit
class TestMongoRepositoryAggregate:
    """Test MongoRepository aggregate method."""

    @pytest.mark.asyncio
    async def test_aggregate_success(self):
        """Test successful aggregate."""
        mock_collection = AsyncMock()
        mock_cursor = AsyncMock()
        mock_results = [{"total": 100}]
        mock_cursor.to_list = AsyncMock(return_value=mock_results)
        mock_collection.aggregate = AsyncMock(return_value=mock_cursor)

        with patch("app.db.mongodb.mongo_db") as mock_db:
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            repo = MongoRepository("test_collection")

            pipeline = [{"$group": {"_id": None, "count": {"$sum": 1}}}]
            result = await repo.aggregate(pipeline)

            assert result == mock_results
            mock_collection.aggregate.assert_called_once_with(pipeline)
