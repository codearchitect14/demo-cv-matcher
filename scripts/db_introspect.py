import asyncio
import json
import os
import sys
from typing import Dict, List, Any

# Ensure project root is on sys.path so `config` can be imported when running as a script
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.connection_pool import global_pool


async def fetch_tables() -> List[Dict[str, Any]]:
    query = """
        select table_name
        from information_schema.tables
        where table_schema = 'public'
          and table_type = 'BASE TABLE'
        order by table_name
    """
    rows = await global_pool.fetch(query)
    return [dict(r) for r in rows]


async def fetch_columns() -> List[Dict[str, Any]]:
    query = """
        select
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        from information_schema.columns
        where table_schema = 'public'
        order by table_name, ordinal_position
    """
    rows = await global_pool.fetch(query)
    return [dict(r) for r in rows]


async def fetch_constraints() -> List[Dict[str, Any]]:
    # Collect PK, FK, UNIQUE, CHECK with involved columns
    query = """
        with key_cols as (
            select
                tc.table_name,
                tc.constraint_name,
                tc.constraint_type,
                string_agg(kcu.column_name, ', ' order by kcu.ordinal_position) as columns
            from information_schema.table_constraints tc
            left join information_schema.key_column_usage kcu
              on tc.constraint_name = kcu.constraint_name
             and tc.table_schema = kcu.table_schema
            where tc.table_schema = 'public'
            group by tc.table_name, tc.constraint_name, tc.constraint_type
        ), checks as (
            select
                tc.table_name,
                tc.constraint_name,
                'CHECK'::text as constraint_type,
                cc.check_clause as definition
            from information_schema.table_constraints tc
            join information_schema.check_constraints cc
              on tc.constraint_name = cc.constraint_name
             and tc.table_schema = cc.constraint_schema
            where tc.table_schema = 'public'
              and tc.constraint_type = 'CHECK'
        )
        select table_name, constraint_name, constraint_type,
               coalesce(columns, '') as columns,
               null::text as definition
        from key_cols
        union all
        select table_name, constraint_name, constraint_type, '' as columns, definition
        from checks
        order by table_name, constraint_name
    """
    rows = await global_pool.fetch(query)
    return [dict(r) for r in rows]


async def fetch_recruiter_role_columns() -> List[Dict[str, Any]]:
    # Inspect recruiters table for role/permission related columns
    query = """
        select column_name, data_type
        from information_schema.columns
        where table_schema = 'public'
          and table_name = 'recruiters'
          and column_name ~* '(role|permission|is_admin|is_superuser|privilege|access|group)'
        order by column_name
    """
    rows = await global_pool.fetch(query)
    return [dict(r) for r in rows]


async def main() -> None:
    await global_pool.initialize()
    try:
        tables, columns, constraints, role_cols = await asyncio.gather(
            fetch_tables(), fetch_columns(), fetch_constraints(), fetch_recruiter_role_columns()
        )

        # Organize per table
        by_table: Dict[str, Dict[str, Any]] = {}
        for t in tables:
            by_table[t['table_name']] = {"columns": [], "constraints": []}

        for c in columns:
            table_name = c['table_name']
            if table_name not in by_table:
                by_table[table_name] = {"columns": [], "constraints": []}
            by_table[table_name]["columns"].append({
                "column_name": c['column_name'],
                "data_type": c['data_type'],
                "is_nullable": c['is_nullable'],
                "column_default": c['column_default'],
                "character_maximum_length": c['character_maximum_length'],
                "numeric_precision": c['numeric_precision'],
                "numeric_scale": c['numeric_scale'],
            })

        for k in constraints:
            table_name = k['table_name']
            if table_name not in by_table:
                by_table[table_name] = {"columns": [], "constraints": []}
            by_table[table_name]["constraints"].append({
                "constraint_name": k['constraint_name'],
                "constraint_type": k['constraint_type'],
                "columns": k.get('columns') or '',
                "definition": k.get('definition'),
            })

        output = {
            "tables": by_table,
            "recruiters_role_columns": role_cols,
        }

        print(json.dumps(output, default=str, indent=2))
    finally:
        await global_pool.close()


if __name__ == "__main__":
    asyncio.run(main())


