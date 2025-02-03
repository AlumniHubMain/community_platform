# function for searching for a user by a set of optional parameters
search_users: str = """
CREATE OR REPLACE FUNCTION {schema}.search_users(
    p_name VARCHAR DEFAULT NULL,
    p_surname VARCHAR DEFAULT NULL,
    p_location VARCHAR DEFAULT NULL,
    p_expertise_area VARCHAR DEFAULT NULL,
    p_specialisation VARCHAR DEFAULT NULL,
    p_skills VARCHAR DEFAULT NULL,
    p_limit INTEGER DEFAULT 30
)
RETURNS SETOF {schema}.users
AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM {schema}.users u
    WHERE
        (p_name IS NULL OR u.name ILIKE '%' || p_name || '%')
        AND (p_surname IS NULL OR u.surname ILIKE '%' || p_surname || '%')
        AND (p_location IS NULL OR u.location ILIKE '%' || p_location || '%')
        AND (p_expertise_area IS NULL OR p_expertise_area = ANY(u.expertise_area))
        AND (p_specialisation IS NULL OR p_specialisation = ANY(u.specialisation))
        AND (p_skills IS NULL OR p_skills = ANY(u.skills))
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
"""
