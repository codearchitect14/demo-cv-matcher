import json
import os
from typing import Any, Dict

INPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema_report.txt')
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema_tables.txt')


def _load_json_with_flexible_encoding(path: str) -> Dict[str, Any]:
    # Try common encodings used by PowerShell redirection
    encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be']
    last_err = None
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                return json.load(f)
        except Exception as e:
            last_err = e
            continue
    raise last_err if last_err else RuntimeError('Failed to read JSON file')


def main() -> None:
    data = _load_json_with_flexible_encoding(INPUT_PATH)

    tables = data.get('tables', {})
    recruiter_roles = data.get('recruiters_role_columns', [])

    lines = []

    # Header summary
    lines.append('Schema Summary (condensed)')
    lines.append('')
    lines.append(f"Total tables: {len(tables)}")
    lines.append('')

    # Per-table condensed view
    for table_name in sorted(tables.keys()):
        t = tables[table_name]
        cols = t.get('columns', [])
        cons = t.get('constraints', [])

        # Basic section header
        lines.append(f"Table: {table_name}")
        lines.append('Columns:')
        lines.append('  - Column | Type | Null | Default')

        for c in cols:
            col = c.get('column_name')
            typ = c.get('data_type')
            nul = c.get('is_nullable')
            dfl = c.get('column_default')
            # Keep it short; trim long defaults
            if isinstance(dfl, str) and len(dfl) > 60:
                dfl = dfl[:57] + '...'
            lines.append(f"  - {col} | {typ} | {nul} | {dfl}")

        # Constraints summary
        if cons:
            pk = [c for c in cons if c.get('constraint_type') == 'PRIMARY KEY']
            fks = [c for c in cons if c.get('constraint_type') == 'FOREIGN KEY']
            uq = [c for c in cons if c.get('constraint_type') == 'UNIQUE']
            checks = [c for c in cons if c.get('constraint_type') == 'CHECK']
            lines.append('Constraints:')
            if pk:
                for c in pk:
                    lines.append(f"  - PK: {c.get('columns')}")
            if fks:
                for c in fks:
                    lines.append(f"  - FK: {c.get('columns')}")
            if uq:
                for c in uq:
                    lines.append(f"  - UNIQUE: {c.get('columns')}")
            if checks:
                for c in checks:
                    # keep check concise
                    definition = c.get('definition')
                    if isinstance(definition, str) and len(definition) > 60:
                        definition = definition[:57] + '...'
                    lines.append(f"  - CHECK: {definition}")

        lines.append('')

    # Recruiter roles/permissions
    lines.append('Recruiters table: role/permission-related columns')
    if recruiter_roles:
        for rc in recruiter_roles:
            lines.append(f"  - {rc.get('column_name')} ({rc.get('data_type')})")
    else:
        lines.append('  - None detected')

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Wrote condensed tables to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()


