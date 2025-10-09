"""
MongoDB Storage Utility for Stock Time Series Data

This module handles storing and retrieving stock time series data
from a local MongoDB instance.
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from pymongo import MongoClient, ASCENDING, DESCENDING, UpdateOne
from pymongo.errors import ConnectionFailure, DuplicateKeyError


class MongoDBStorage:
    """
    Class to handle MongoDB storage for stock time series data
    """
    
    def __init__(self, connection_string: str = 'mongodb://localhost:27017/', database_name: str = 'stock_data'):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string (str): MongoDB connection string
            database_name (str): Name of the database to use
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connection_string = connection_string
        self.database_name = database_name
        
        try:
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[database_name]
            self.logger.info(f"Successfully connected to MongoDB at {connection_string}")
            
            # Initialize collections
            self._initialize_collections()
            
        except ConnectionFailure as e:
            self.logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.logger.warning("Time series data will not be stored in MongoDB")
            self.client = None
            self.db = None
    
    def _initialize_collections(self):
        """
        Initialize MongoDB collections with appropriate indexes
        """
        if self.db is None:
            return
        
        try:
            # Time series collection for stock prices
            if 'timeseries' not in self.db.list_collection_names():
                self.logger.info("Creating 'timeseries' collection")
            
            timeseries_collection = self.db['timeseries']
            
            # Create compound index on ticker and date (unique)
            timeseries_collection.create_index(
                [('ticker', ASCENDING), ('date', DESCENDING)],
                unique=True,
                name='ticker_date_idx'
            )
            
            # Create index on date for querying
            timeseries_collection.create_index(
                [('date', DESCENDING)],
                name='date_idx'
            )
            
            # Create index on ticker for querying
            timeseries_collection.create_index(
                [('ticker', ASCENDING)],
                name='ticker_idx'
            )
            
            # Collection for run metadata
            if 'run_metadata' not in self.db.list_collection_names():
                self.logger.info("Creating 'run_metadata' collection")
            
            metadata_collection = self.db['run_metadata']
            
            # Create index on run_timestamp
            metadata_collection.create_index(
                [('run_timestamp', DESCENDING)],
                name='run_timestamp_idx'
            )
            
            self.logger.info("MongoDB collections and indexes initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing MongoDB collections: {str(e)}")
    
    def store_timeseries_data(self, ticker: str, df: pd.DataFrame, run_id: str = None) -> bool:
        """
        Store time series data for a ticker
        
        Args:
            ticker (str): Stock ticker symbol
            df (pandas.DataFrame): DataFrame with OHLCV data (index must be datetime)
            run_id (str, optional): Unique identifier for this run
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.db is None or df.empty:
            return False
        
        try:
            collection = self.db['timeseries']
            
            # Prepare documents for insertion
            documents = []
            for date_index, row in df.iterrows():
                # Convert date to datetime if it isn't already
                if isinstance(date_index, pd.Timestamp):
                    date = date_index.to_pydatetime()
                else:
                    date = pd.to_datetime(date_index).to_pydatetime()
                
                doc = {
                    'ticker': ticker.upper(),
                    'date': date,
                    'open': float(row['open']) if 'open' in row and pd.notna(row['open']) else None,
                    'high': float(row['high']) if 'high' in row and pd.notna(row['high']) else None,
                    'low': float(row['low']) if 'low' in row and pd.notna(row['low']) else None,
                    'close': float(row['close']) if 'close' in row and pd.notna(row['close']) else None,
                    'volume': int(row['volume']) if 'volume' in row and pd.notna(row['volume']) else None,
                    'last_updated': datetime.now(),
                    'run_id': run_id
                }
                documents.append(doc)
            
            # Bulk upsert (update if exists, insert if not)
            if documents:
                bulk_operations = []
                for doc in documents:
                    bulk_operations.append(
                        UpdateOne(
                            {'ticker': doc['ticker'], 'date': doc['date']},
                            {'$set': doc},
                            upsert=True
                        )
                    )
                
                result = collection.bulk_write(bulk_operations)
                
                self.logger.info(
                    f"Stored {len(documents)} time series records for {ticker} "
                    f"(inserted: {result.upserted_count}, modified: {result.modified_count})"
                )
                return True
            
        except Exception as e:
            self.logger.error(f"Error storing time series data for {ticker}: {str(e)}")
            return False
    
    def store_run_metadata(self, tickers: List[str], run_config: Dict = None) -> str:
        """
        Store metadata about a scraper run
        
        Args:
            tickers (list): List of ticker symbols processed
            run_config (dict, optional): Configuration used for this run
            
        Returns:
            str: Unique run ID
        """
        if self.db is None:
            return None
        
        try:
            collection = self.db['run_metadata']
            
            run_timestamp = datetime.now()
            run_id = f"run_{run_timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            doc = {
                'run_id': run_id,
                'run_timestamp': run_timestamp,
                'tickers': [t.upper() for t in tickers],
                'ticker_count': len(tickers),
                'config': run_config or {},
                'status': 'started'
            }
            
            collection.insert_one(doc)
            self.logger.info(f"Created run metadata with ID: {run_id}")
            
            return run_id
            
        except Exception as e:
            self.logger.error(f"Error storing run metadata: {str(e)}")
            return None
    
    def update_run_status(self, run_id: str, status: str, error_message: str = None):
        """
        Update the status of a run
        
        Args:
            run_id (str): Run identifier
            status (str): Status ('started', 'completed', 'failed')
            error_message (str, optional): Error message if status is 'failed'
        """
        if self.db is None or not run_id:
            return
        
        try:
            collection = self.db['run_metadata']
            
            update_doc = {
                'status': status,
                'last_updated': datetime.now()
            }
            
            if error_message:
                update_doc['error_message'] = error_message
            
            if status == 'completed':
                update_doc['completed_at'] = datetime.now()
            
            collection.update_one(
                {'run_id': run_id},
                {'$set': update_doc}
            )
            
            self.logger.info(f"Updated run {run_id} status to: {status}")
            
        except Exception as e:
            self.logger.error(f"Error updating run status: {str(e)}")
    
    def get_timeseries_data(self, ticker: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """
        Retrieve time series data for a ticker
        
        Args:
            ticker (str): Stock ticker symbol
            start_date (datetime, optional): Start date for data retrieval
            end_date (datetime, optional): End date for data retrieval
            
        Returns:
            pandas.DataFrame: DataFrame with historical data
        """
        if self.db is None:
            return pd.DataFrame()
        
        try:
            collection = self.db['timeseries']
            
            # Build query
            query = {'ticker': ticker.upper()}
            if start_date or end_date:
                query['date'] = {}
                if start_date:
                    query['date']['$gte'] = start_date
                if end_date:
                    query['date']['$lte'] = end_date
            
            # Fetch data
            cursor = collection.find(query).sort('date', DESCENDING)
            
            # Convert to DataFrame
            data = list(cursor)
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
            df.set_index('date', inplace=True)
            df.sort_index(ascending=False, inplace=True)
            
            self.logger.info(f"Retrieved {len(df)} time series records for {ticker} from MongoDB")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error retrieving time series data for {ticker}: {str(e)}")
            return pd.DataFrame()
    
    def get_latest_date(self, ticker: str) -> Optional[datetime]:
        """
        Get the latest date for which data is available for a ticker
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            datetime: Latest date, or None if no data
        """
        if self.db is None:
            return None
        
        try:
            collection = self.db['timeseries']
            
            result = collection.find_one(
                {'ticker': ticker.upper()},
                sort=[('date', DESCENDING)]
            )
            
            if result:
                return result['date']
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting latest date for {ticker}: {str(e)}")
            return None
    
    def get_run_history(self, limit: int = 10) -> List[Dict]:
        """
        Get history of recent runs
        
        Args:
            limit (int): Number of recent runs to retrieve
            
        Returns:
            list: List of run metadata dictionaries
        """
        if self.db is None:
            return []
        
        try:
            collection = self.db['run_metadata']
            
            cursor = collection.find().sort('run_timestamp', DESCENDING).limit(limit)
            
            runs = []
            for doc in cursor:
                doc.pop('_id', None)  # Remove MongoDB ObjectId
                runs.append(doc)
            
            return runs
            
        except Exception as e:
            self.logger.error(f"Error retrieving run history: {str(e)}")
            return []
    
    def close(self):
        """
        Close MongoDB connection
        """
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")
