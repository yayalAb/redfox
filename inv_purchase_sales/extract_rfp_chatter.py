#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract supplies.rfp chatter data from PostgreSQL backup SQL file.
Includes: messages, attachments, tracking values.

Usage:
    python extract_rfp_chatter.py backup_20260227_025907.sql -o rfp_chatter.json
"""

import json
import argparse
import base64
from pathlib import Path


MAIL_MESSAGE_COLUMNS = [
    'id', 'parent_id', 'res_id', 'record_alias_domain_id', 'record_company_id',
    'subtype_id', 'mail_activity_type_id', 'author_id', 'author_guest_id', 'mail_server_id',
    'create_uid', 'write_uid', 'subject', 'model', 'record_name', 'message_type',
    'email_from', 'message_id', 'reply_to', 'email_layout_xmlid', 'body',
    'is_internal', 'reply_to_force_new', 'email_add_signature', 'date', 'pinned_at',
    'create_date', 'write_date'
]

IR_ATTACHMENT_COLUMNS = [
    'id', 'res_id', 'company_id', 'file_size', 'create_uid', 'write_uid', 'name',
    'res_model', 'res_field', 'type', 'url', 'access_token', 'store_fname', 'checksum',
    'mimetype', 'description', 'index_content', 'public', 'create_date', 'write_date',
    'db_datas', 'original_id', 'website_id', 'theme_template_id', 'key'
]

MAIL_TRACKING_COLUMNS = [
    'id', 'field_id', 'old_value_integer', 'new_value_integer', 'currency_id',
    'mail_message_id', 'create_uid', 'write_uid', 'old_value_char', 'new_value_char',
    'field_info', 'old_value_text', 'new_value_text', 'old_value_datetime',
    'new_value_datetime', 'create_date', 'write_date', 'old_value_float', 'new_value_float'
]


def parse_pg_copy_value(val):
    if val == '\\N' or val == '':
        return None
    return val


def parse_pg_copy_line(line):
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


def decode_bytea(val):
    """Decode PostgreSQL bytea from COPY text format. Returns base64 string or None."""
    if not val or val == '\\N':
        return None
    try:
        if val.startswith('\\x'):
            raw = bytes.fromhex(val[2:])
        else:
            raw = val.encode('latin-1')
        return base64.b64encode(raw).decode('ascii') if raw else None
    except Exception:
        return None


def extract_supplies_rfp_map(lines):
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


def extract_field_id_to_name(lines):
    """Build field_id -> name for supplies.rfp model. ir_model: id=0, model=3. ir_model_fields: id=0, model_id=2, name=7."""
    model_id = None
    for i, line in enumerate(lines):
        if 'COPY public.ir_model ' in line and 'FROM stdin' in line:
            for j in range(i + 1, len(lines)):
                data_line = lines[j]
                if data_line.strip() == '\\.':
                    break
                parts = data_line.split('\t')
                if len(parts) >= 4 and parse_pg_copy_value(parts[3]) == 'supplies.rfp':
                    try:
                        model_id = int(parse_pg_copy_value(parts[0]) or 0)
                        break
                    except (ValueError, TypeError):
                        pass
            if model_id:
                break

    field_map = {}
    if not model_id:
        return field_map

    for i, line in enumerate(lines):
        if 'COPY public.ir_model_fields' in line and 'FROM stdin' in line:
            for j in range(i + 1, len(lines)):
                data_line = lines[j]
                if data_line.strip() == '\\.':
                    break
                parts = data_line.split('\t')
                if len(parts) >= 8:
                    try:
                        fid = int(parse_pg_copy_value(parts[0]) or 0)
                        mid = int(parse_pg_copy_value(parts[2]) or 0)
                        name = parse_pg_copy_value(parts[7]) or ''
                        if mid == model_id and fid:
                            field_map[fid] = name
                    except (ValueError, TypeError):
                        continue
            break
    return field_map


def extract_mail_messages_supplies_rfp(lines):
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
                        msg_id_raw = parse_pg_copy_value(parts[0])
                        try:
                            res_id = int(res_id_raw) if res_id_raw else None
                            msg_id = int(msg_id_raw) if msg_id_raw else None
                        except (ValueError, TypeError):
                            res_id = msg_id = None
                        if res_id and msg_id:
                            msg = {col: parse_pg_copy_value(parts[k]) for k, col in enumerate(MAIL_MESSAGE_COLUMNS) if k < len(parts)}
                            msg['_backup_res_id'] = res_id
                            msg['_backup_message_id'] = msg_id
                            messages.append(msg)
            break
    return messages


def extract_message_attachments(lines, message_ids):
    """Get message_id -> [attachment_id] from message_attachment_rel."""
    msg_attachments = {}
    for i, line in enumerate(lines):
        if 'COPY public.message_attachment_rel' in line and 'FROM stdin' in line:
            for j in range(i + 1, len(lines)):
                data_line = lines[j].strip()
                if data_line == '\\.':
                    break
                parts = data_line.split('\t')
                if len(parts) >= 2:
                    try:
                        mid = int(parse_pg_copy_value(parts[0]) or 0)
                        aid = int(parse_pg_copy_value(parts[1]) or 0)
                        if mid in message_ids and aid:
                            msg_attachments.setdefault(mid, []).append(aid)
                    except (ValueError, TypeError):
                        continue
            break
    return msg_attachments


def extract_attachments_by_ids(lines, attachment_ids):
    """Extract ir_attachment rows by ids."""
    attachments = {}
    for i, line in enumerate(lines):
        if 'COPY public.ir_attachment' in line and 'FROM stdin' in line:
            for j in range(i + 1, len(lines)):
                data_line = lines[j]
                if data_line.strip() == '\\.':
                    break
                parts = parse_pg_copy_line(data_line.rstrip('\n'))
                if len(parts) >= 21:
                    try:
                        aid = int(parse_pg_copy_value(parts[0]) or 0)
                        if aid not in attachment_ids:
                            continue
                        att = {col: parse_pg_copy_value(parts[k]) for k, col in enumerate(IR_ATTACHMENT_COLUMNS) if k < len(parts)}
                        db_datas = parse_pg_copy_value(parts[20]) if len(parts) > 20 else None
                        if db_datas:
                            att['db_datas_b64'] = decode_bytea(db_datas)
                        attachments[aid] = att
                    except (ValueError, TypeError):
                        continue
            break
    return attachments


def extract_tracking_by_message_ids(lines, message_ids, field_map):
    """Extract mail_tracking_value for given message_ids."""
    tracking = []
    for i, line in enumerate(lines):
        if 'COPY public.mail_tracking_value' in line and 'FROM stdin' in line:
            for j in range(i + 1, len(lines)):
                data_line = lines[j]
                if data_line.strip() == '\\.':
                    break
                parts = parse_pg_copy_line(data_line.rstrip('\n'))
                if len(parts) >= 6:
                    try:
                        mid = int(parse_pg_copy_value(parts[5]) or 0)
                        if mid not in message_ids:
                            continue
                        tv = {col: parse_pg_copy_value(parts[k]) for k, col in enumerate(MAIL_TRACKING_COLUMNS) if k < len(parts)}
                        fid = tv.get('field_id') and int(tv['field_id'])
                        tv['field_name'] = field_map.get(fid) if fid else None
                        tv['_backup_message_id'] = mid
                        tracking.append(tv)
                    except (ValueError, TypeError, KeyError):
                        continue
            break
    return tracking


def build_chatter_by_rfp_number(rfp_map, messages, msg_attachments, attachments, tracking_list):
    by_rfp = {}
    for msg in messages:
        old_res_id = msg.get('_backup_res_id')
        old_msg_id = msg.get('_backup_message_id')
        rfp_number = rfp_map.get(old_res_id) if old_res_id else None
        if rfp_number:
            m = {k: v for k, v in msg.items() if k not in ('_backup_res_id', '_backup_message_id')}
            att_ids = msg_attachments.get(old_msg_id, [])
            m['_attachments'] = [attachments.get(aid) for aid in att_ids if attachments.get(aid)]
            m['_tracking'] = [{k: v for k, v in t.items() if k != '_backup_message_id'}
                             for t in tracking_list if t.get('_backup_message_id') == old_msg_id]
            by_rfp.setdefault(rfp_number, []).append(m)
    for rfp in by_rfp:
        by_rfp[rfp].sort(key=lambda x: (x.get('date') or x.get('create_date') or ''))
    return by_rfp


def main():
    parser = argparse.ArgumentParser(description='Extract supplies.rfp chatter from PostgreSQL backup')
    parser.add_argument('sql_file', help='Path to backup SQL file')
    parser.add_argument('-o', '--output', default='rfp_chatter.json', help='Output JSON file')
    args = parser.parse_args()

    sql_path = Path(args.sql_file)
    if not sql_path.exists():
        print("Error: File not found:", sql_path)
        return 1

    print("Reading", sql_path, "...")
    with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    print("Extracting supplies_rfp id -> rfp_number...")
    rfp_map = extract_supplies_rfp_map(lines)
    print("  Found", len(rfp_map), "RFP records")

    print("Extracting mail_message for supplies.rfp...")
    messages = extract_mail_messages_supplies_rfp(lines)
    print("  Found", len(messages), "messages")

    message_ids = {m['_backup_message_id'] for m in messages}
    attachment_ids = set()

    print("Extracting message_attachment_rel...")
    msg_attachments = extract_message_attachments(lines, message_ids)
    for aids in msg_attachments.values():
        attachment_ids.update(aids)
    print("  Found", len(attachment_ids), "attachments linked to messages")

    print("Extracting ir_attachment data...")
    attachments = extract_attachments_by_ids(lines, attachment_ids)
    print("  Loaded", len(attachments), "attachments")

    print("Extracting field_id -> name for supplies.rfp...")
    field_map = extract_field_id_to_name(lines)
    print("  Found", len(field_map), "fields")

    print("Extracting mail_tracking_value...")
    tracking_list = extract_tracking_by_message_ids(lines, message_ids, field_map)
    print("  Found", len(tracking_list), "tracking values")

    chatter_by_rfp = build_chatter_by_rfp_number(rfp_map, messages, msg_attachments, attachments, tracking_list)
    print("  Chatter for", len(chatter_by_rfp), "unique RFP numbers")

    out_path = Path(args.output)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(chatter_by_rfp, f, indent=2, ensure_ascii=False)

    print("Written to", out_path)
    return 0


if __name__ == '__main__':
    exit(main())
