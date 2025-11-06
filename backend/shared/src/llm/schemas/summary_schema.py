# Placeholder for summary schema - to be implemented if needed
summary_schema = {
    "name": "SummarySchema", 
    "description": "A schema for generating summaries from a given text.",
    "parameters": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "A concise summary of the text.",
            },
        },
        "required": ["summary"],
    },
}