from typing import Union
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from stopwordsiso import stopwords
import re

from ir.db.models.models import ChatMessage, Law
from api.models import ChatQuery
from utils.logging.logger import logger

SELECTIELIJSTEN_ROW_LIMIT = 15

def chat_postgresql(chat_query: ChatQuery, db_postgresql: Session):
    # Log message to database
    message = ChatMessage(message=chat_query.message)
    db_postgresql.add(message)
    db_postgresql.commit()
    # Get laws
    laws = db_postgresql.query(Law).all()
    laws_str = "\n".join([f"{law.name}: {law.url}" for law in laws])
    return {"message": f"Ik baseer mijn antwoorden op de volgende wetten:\n{laws_str}"}


def clean_word(word):
    """Remove special characters from a word, keeping only alphanumeric characters."""
    return re.sub(r"\W+", "", word)


async def search_selectielijsten(
    input: str, db: Session
) -> Union[list[dict[str, str]], str]:
    try:
        logger.info("Searching for matching words from input in selectielijsten")
        # Load Dutch stopwords
        stop_words = list(stopwords("nl")) + ["of", "ik", "is"]

        # Tokenize, filter stopwords, and remove special characters
        filtered_words = [
            clean_word(word).lower()
            for word in set(input.split())
            if clean_word(word).lower() not in stop_words
        ]
        # Filter out words that contain any numeric values
        filtered_words = [
            word for word in filtered_words if not any(char.isdigit() for char in word)
        ]

        if not filtered_words:
            return "No relevant search terms found"

        # Define the columns to search (matching the SelectieLijsten model)
        columns_to_search = [
            "selectielijsten",
            "procescategorie",
            "process_number",
            "process_description",
            "waardering",
            "proces_komt_voor_bij",
            "toelichting",
            "voorbeelden",
            "voorbeelden_werkdoc_bsd",
            "persoonsgegevens_aanwezig",
        ]

        # Construct a SQL query that searches for any of the words in the specified columns
        search_conditions = []
        params = {}
        for i, word in enumerate(filtered_words):
            word_param = f"word_{i}"
            params[word_param] = f"%{word}%"
            search_conditions.append(
                " OR ".join(
                    [f"{column} ILIKE :{word_param}" for column in columns_to_search]
                )
            )
        sql_query = text(
            f"SELECT * FROM selectielijsten WHERE {' OR '.join(search_conditions)}"
        )

        # Execute the query
        result = db.execute(sql_query, params=params)
        rows = result.fetchall()

        if not rows:
            logger.warning("No matching records found in selectielijsten")
            return False

        logger.info(f"Found {len(rows)} matching records in selectielijsten")

        result_dicts = [
            {key: value for key, value in row._asdict().items() if key != "id"}
            for row in rows
        ]
        return result_dicts #[:SELECTIELIJSTEN_ROW_LIMIT]
    except Exception as e:
        logger.error(f"Error during selectielijsten db-search: {e}")
        return False
