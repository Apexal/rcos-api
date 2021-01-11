from api.db import ARRAY_ANY
from typing import Any, List, Dict, Optional
from asyncpg import Connection
from pypika import PostgreSQLQuery as Query, Table
from pypika.terms import Parameter

proj_t = Table("projects")


async def fetch_projects(conn: Connection, filter: Dict[str, Any]) -> List[Dict]:
    query = Query.from_(proj_t) \
        .select("*") \
        .orderby(proj_t.created_at)

    params = []
    for key, value in filter.items():
        if value is None:
            continue

        # Big brain move here.
        # 'value' = ANY("array_col") is not supported directly in PyPika.
        # We can use a custom function, here named ARRAY_ANY but then
        # the order comes out as ANY("array_col") = 'value' which Postgres doesn't like.
        # To get around this, we use a parameterized query and pass in the languages and stacks
        if key == "languages" or key == "stack":
            for item in value:
                query = query.where(Parameter("$" + str(len(params)+1))
                                    == ARRAY_ANY(proj_t[key]))
                params.append(item)
        else:
            query = query.where(value == proj_t[key])

    return await conn.fetch(str(query), *params)