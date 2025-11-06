keywords_schema = {
    "name": "KeywordsSchema",
    "description": "A schema for generating keywords from a given text.",
    "parameters": {
        "type": "object",
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of keywords generated from the text.",
            },
        },
        "required": ["keywords"],
    },
}