#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract supplies.rfp chatter data from PostgreSQL backup SQL file.

Usage:
    python extract_rfp_chatter.py path/to/backup_20260227_025907.sql -o rfp_chatter.json

Output: JSON file with chatter data keyed by rfp_number for import into current database.
"""

import re
import json
import argparse
from pathlib import Path


# mail_message columns from pg_dump (order matters)
MAIL_MESSAGE_COLUMNS = [
    'id', 'parent_id', 'res_id', 'record_alias_domain_id', 'record_company_id',
    'subtype_id', 'mail_activity_type_id', 'author_id', 'author_guest_id', 'mail_server_id',
    'create_uid', 'write_uid', 'subject', 'model', 'record_name', 'message_type',
    'email_from', 'message_id', 'reply_to', 'email_layout_xmlid', 'body',
    'is_internal', 'reply_to_force_new', 'email_add_signature', 'date', 'pinned_at',
    'create_date', 'write_date'
]

# supplies_rfp columns (from backup)
SUPPLIES_RFP_COLUMNS = [
    'id', 'currency_id', 'product_category_id', 'submitted_by', 'store_request_id',
    'create_uid', 'write_uid', 'state', 'rfp_number', 'purchase_origin', 'purchase_type',
    'purpose', 'required_date', 'date_approve', 'date_ordered', 'total_amount',
    'requested_date', 'create_date', 'write_date', 'department_id', 'company_id',
    'approved_by', 'internal_notes', 'agreement_id', 'is_from_sale', 'f_approved_by',
    'f_approved_date', 'source_rfp_id', 'merged_from_references', 'verified_by',
    'direct_purchase_id', 'decision'
]


def parse_pg_copy_value(val):
    """Parse PostgreSQL COPY format value (\\N = NULL)."""
    if val == '\\N' or val == '':
        return None
    return val


def parse_pg_copy_line(line):
    """Parse a tab-separated PostgreSQL COPY line, handling escaped chars."""
    result = []
    current = []
    i = 0
    while i < len(line):
        if line[i] == '\\' and i + 1 < len(line):
            if line[i + 1] == 'N':
                current.append('\\N')
                i += 2
            elif line[i + 1] == 't':
                current.append('\t')
                i += 2
            elif line[i + 1] == 'n':
                current.append('\n')
                i += 2
            elif line[i + 1] == '\\':
                current.append('\\')
                i += 2
            else:
                current.append(line[i])
                i += 1
        elif line[i] == '\t':
            result.append(''.join(current))
            current = []
            i += 1
        else:
            current.append(line[i])
            i += 1
    result.append(''.join(current))
    return result


def extract_supplies_rfp_map(lines):
    """Extract old_res_id -> rfp_number mapping from supplies_rfp COPY block."""
    rfp_map = {}
    for i, line in enumerate(lines):
        if 'COPY public.supplies_rfp' in line and 'FROM stdin' in line:
            for j in range(i + 1, len(lines)):
                data_line = lines[j].strip()
                if data_line == '\\.':
                    break
                parts = data_line.split('\t')
                if len(parts) >= 9:
                    try:
                        old_id = int(parse_pg_copy_value(parts[0]) or 0)
                        rfp_number = parse_pg_copy_value(parts[8]) or ''
                        if old_id and rfp_number:
                            rfp_map[old_id] = rfp_number
                    except (ValueError, IndexError):
                        continue
            break
    return rfp_map


def extract_mail_messages_supplies_rfp(lines):
    """Extract mail_message rows where model='supplies.rfp'."""
    messages = []
    for i, line in enumerate(lines):
        if 'COPY public.mail_message' in line and 'FROM stdin' in line:
            for j in range(i + 1, len(lines)):
                data_line = lines[j]
                if data_line.strip() == '\\.':
                    break
                parts = parse_pg_copy_line(data_line.rstrip('\n'))
                if len(parts) >= 15:
                    model = parse_pg_copy_value(parts[13])
                    if model == 'supplies.rfp':
                        res_id_raw = parse_pg_copy_value(parts[2])
                        try:
                            res_id = int(res_id_raw) if res_id_raw else None
                        except (ValueError, TypeError):
                            res_id = None
                        if res_id:
                            msg = {col: parse_pg_copy_value(parts[k]) for k, col in enumerate(MAIL_MESSAGE_COLUMNS) if k < len(parts)}
                            msg['_backup_res_id'] = res_id
                            messages.append(msg)
            break
    return messages


def build_chatter_by_rfp_number(rfp_map, messages):
    """Build {rfp_number: [messages]} structure for restore."""
    by_rfp = {}
    for msg in messages:
        old_res_id = msg.get('_backup_res_id')
        rfp_number = rfp_map.get(old_res_id) if old_res_id else None
        if rfp_number:
            m = {k: v for k, v in msg.items() if k != '_backup_res_id'}
            by_rfp.setdefault(rfp_number, []).append(m)
    for rfp in by_rfp:
        by_rfp[rfp].sort(key=lambda x: (x.get('date') or x.get('create_date') or ''))
    return by_rfp


def main():
    parser = argparse.ArgumentParser(description='Extract supplies.rfp chatter from PostgreSQL backup')
    parser.add_argument('sql_file', help='Path to backup SQL file (e.g. backup_20260227_025907.sql)')
    parser.add_argument('-o', '--output', default='rfp_chatter.json', help='Output JSON file')
    args = parser.parse_args()

    sql_path = Path(args.sql_file)
    if not sql_path.exists():
        print("Error: File not found:", sql_path)
        return 1

    print("Reading", sql_path, "...")
    with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    print("Extracting supplies_rfp id -> rfp_number mapping...")
    rfp_map = extract_supplies_rfp_map(lines)
    print("  Found", len(rfp_map), "RFP records")

    print("Extracting mail_message for supplies.rfp...")
    messages = extract_mail_messages_supplies_rfp(lines)
    print("  Found", len(messages), "chatter messages")

    chatter_by_rfp = build_chatter_by_rfp_number(rfp_map, messages)
    print("  Chatter for", len(chatter_by_rfp), "unique RFP numbers")

    out_path = Path(args.output)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(chatter_by_rfp, f, indent=2, ensure_ascii=False)

    print("Written to", out_path)
    return 0


if __name__ == '__main__':
    exit(main())
