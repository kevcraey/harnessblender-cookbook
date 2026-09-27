"""Validate the exact attachment bytes bound into a report proposal."""
import base64
import binascii
import hashlib
import re


def attachment_bytes(payload):
    allowed = {'filename', 'media_type', 'sha256', 'content_base64', 'page_action'}
    if not isinstance(payload, dict) or set(payload) != allowed:
        raise ValueError('Ongeldige rapportbijlage')
    filename = payload['filename']
    if not isinstance(filename, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,175}\.png', filename) or '..' in filename:
        raise ValueError('Onveilige bestandsnaam voor rapportbijlage')
    if payload['media_type'] != 'image/png' or not isinstance(payload['page_action'], str) or not re.fullmatch(r'[1-9]\d*', payload['page_action']):
        raise ValueError('Bijlage vraagt PNG en een voorafgaande nieuwe pagina-actie')
    encoded = payload['content_base64']
    if not isinstance(encoded, str) or len(encoded) > 14_000_000:
        raise ValueError('Rapportbijlage is ongeldig of te groot')
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError('Bijlage bevat geen geldige base64') from exc
    if not data.startswith(b'\x89PNG\r\n\x1a\n') or hashlib.sha256(data).hexdigest() != payload['sha256']:
        raise ValueError('PNG of bijlagehash klopt niet')
    return data
