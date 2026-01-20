# database/queries.py
COMPETITIONS_QUERY = """
SELECT * FROM competition 
ORDER BY date_of_the_event DESC
"""

USERS_QUERY = "SELECT * FROM users"

TASKS_QUERY = "SELECT * FROM programming_tasks"

DECISIONS_QUERY = """
SELECT d.*, u.FCs AS user_name, pt.points, pt.complexity 
FROM decisions d
JOIN users u ON d.id_users = u.id
JOIN programming_tasks pt ON d.id_programminng_tasks = pt.id
"""

PARTICIPATION_QUERY = """
SELECT p.*, u.FCs, c.title 
FROM participation p 
LEFT JOIN users u ON p.id_users = u.id 
LEFT JOIN competition c ON p.id_competition = c.id
"""
