

def get_user_info(kc_user_info, db):
    """
    Retrieve user information based on user_id.
    This is a placeholder function and should be replaced with actual implementation.
    """
    # Example user info, replace with actual database retrieval logic
    return {
        "user_id": kc_user_info.get("user_id"),
        "name": kc_user_info.get("name", "Marieke Jansen"),
        "email": kc_user_info.get("email", ""),
        "department": "Afdeling Milieu en Duurzaamheid",
        "role": "Beleidsmedewerker informatiebeheer",
        "preferences": {
            "language": "nl",
            "notifications": True,
        },
        "knowledge_base": "Expertise in milieuwetgeving, bestuursrecht en informatieverzoeken. Ervaring met het behandelen van Woo-verzoeken en het toepassen van de Wet open overheid, Archiefwet en Algemene wet bestuursrecht binnen de gemeentelijke context."
    }
