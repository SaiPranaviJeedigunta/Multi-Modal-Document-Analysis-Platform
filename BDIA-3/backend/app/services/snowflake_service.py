import snowflake.connector
from app.config.settings import Settings, settings 
from ..models.document import Document
from typing import List

class SnowflakeService:
    def __init__(self):
        self.settings = Settings()
        self.conn = snowflake.connector.connect(
            max_connections=5,
            min_connections=1,
            user=self.settings.SNOWFLAKE_USER,

            password=self.settings.SNOWFLAKE_PASSWORD,
            account=self.settings.SNOWFLAKE_ACCOUNT,
            warehouse=self.settings.SNOWFLAKE_WAREHOUSE,
            database=self.settings.SNOWFLAKE_DATABASE,
            schema=self.settings.SNOWFLAKE_SCHEMA
        )
    

    async def get_all_documents(self) -> List[Document]:
        """Fetch all documents from Snowflake"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM documents")
            rows = cursor.fetchall()
            return [Document(
                id=row[0],
                title=row[1],
                summary=row[2],
                image_link=row[3],
                pdf_link=row[4]
            ) for row in rows]
        finally:
            cursor.close()

    async def get_document(self, document_id: str) -> Document:
        """Fetch a specific document from Snowflake"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM documents WHERE id = %s",
                (document_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Document(
                id=row[0],
                title=row[1],
                summary=row[2],
                image_link=row[3],
                pdf_link=row[4]
            )
        finally:
            cursor.close()

    # Add these methods to the existing SnowflakeService class

async def update_document_summary(self, document_id: str, summary: str):
    """Update document summary in Snowflake"""
    cursor = self.conn.cursor()
    try:
        cursor.execute(
            "UPDATE documents SET summary = %s WHERE id = %s",
            (summary, document_id)
        )
        self.conn.commit()
    finally:
        cursor.close()

async def get_document_qa_interactions(self, document_id: str):
    """Fetch Q&A interactions for a document"""
    cursor = self.conn.cursor()
    try:
        cursor.execute(
            "SELECT question, answer FROM qa_interactions WHERE document_id = %s ORDER BY created_at",
            (document_id,)
        )
        return [{"question": row[0], "answer": row[1]} for row in cursor.fetchall()]
    finally:
        cursor.close()

async def store_research_summary(self, document_id: str, summary: str):
    """Store research summary in Snowflake"""
    cursor = self.conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO research_summaries (document_id, summary, created_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            """,
            (document_id, summary)
        )
        self.conn.commit()
    finally:
        cursor.close()

async def get_connection(self):
        return self.pool.get_connection()