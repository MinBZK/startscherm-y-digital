
def get_source_query_output_schema():
    """
    Returns the output schema for the source query.
    This schema defines the structure of the response that includes relevant legal sources.
    """
    return {
        "title": "RelevantSources",
        "description": "Schema for extracting relevant legal sources from the model output.",
        "type": "object",
        "properties": {
        "relevant_sources": {
            "type": "array",
            "description": "A list of laws and legal sources that should be consulted to answer the user's question.",
            "items": {
            "type": "object",
            "properties": {
                "source_id": {
                "type": "string",
                "enum": ["WOO", "AVG", "AWB", "Archiefwet", "WOO-Werkinstructie", "Jurisprudentie", "Selectielijsten"],
                "description": "The unique identifier or name of the legal source."
                },
            },
            "required": ["source_id"]
            },
            },
        },
        # "required": ["relevant_sources"],
        "additionalProperties": False
    }

def get_main_query_output_schema():
    """
    Returns the output schema for the main query.
    """
    return {
        "title": "MainQueryResponse",
        "description": "Schema for the main query response including legal sources and their details.",
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": "Answer to the user's question based on the relevant legal sources.",
            }
        },
        "required": ["answer"],
        "additionalProperties": False
    }


def get_paragraphwise_source_schema(allowed_sources):
    return {
        "title": "ParagraphSourceAttribution",
        "description": "Schema for assigning relevant legal sources per paragraph in a legal reasoning answer.",
        "type": "object",
        "properties": {
            "paragraphs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "paragraph_index": {"type": "integer"},
                        "relevant_sources": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source_names": {
                                        "type": "string",
                                        "enum": allowed_sources,
                                        "description": "One of the provided sources that this paragraph relies on."
                                    },
                                },
                                "required": ["source_names"]
                            }
                        },
                        "unlisted_sources": {
                            "type": "array",
                            "description": "Any legal sources used that were not in the provided list (e.g. other laws).",
                            "items": {
                                "type": "string"
                            }
                        },
                    },
                    "required": ["paragraph_index", "relevant_sources"]
                }
            }
        },
        "required": ["paragraphs"],
        "additionalProperties": False
    }

def get_taxonomy_extraction_schema():
    return {
        "title": "TaxonomyExtraction",
        "description": "Schema for extracting taxonomy from the model output.",
        "type": "object",
        "properties": {
            "paragraphs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "paragraph_index": {"type": "integer"},
                        "taxonomie_term_index": {
                                "type": "object",
                                "properties": {
                                    "term_index": {
                                        "type": "array",
                                        "items" : {
                                            "type": "integer",},
                                            "description": "An array of the term indices of the taxonomy terms in the paragraph."
                                    },
                                    "context_index": {
                                        "type": "array",
                                        "items": {
                                            "type": "integer",
                                        },
                                        "description": "An array of the context indices of the taxonomy terms."
                                    },
                                },
                                "required": ["term_index", "context_index"]
                            },
                        "updated_paragraph": {
                            "type": "string",
                            "description": "The updated paragraph with taxonomy term indices placed in the paragraph.",
                        },
                    },
                    "required": ["paragraph_index"]
                }
            }
        },
        "required": ["paragraphs"],
        "additionalProperties": False
    }

def get_source_extraction_schema():
    return {
        "title": "SourceExtraction",
        "description": "Schema for extracting sources from the model output.",
        "type": "object",
        "properties": {
            "paragraphs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "paragraph_index": {"type": "integer"},
                        "sources": {
                            "type": "array",
                            "items": {
                                "type": "integer",
                                "description": "Integer of the source index in the provided list of sources."
                            }
                        },
                    },
                    "required": ["paragraph_index", "sources"]
                }
            }
        },
        "required": ["paragraphs"],
        "additionalProperties": False
    }