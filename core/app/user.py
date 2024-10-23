import dataclasses
import logging

from datetime import datetime
from requests.status_codes import codes

import psycopg2 as pg

from flask import Blueprint, request
from flask.json import jsonify

from app import consts
from app.db import with_cursor

logger = logging.getLogger(__name__)

bp = Blueprint("user", __name__, url_prefix="/user")


# TODO: consider ORM (?)
@dataclasses.dataclass
class User:
    uid: str = ''
    name: str = ''
    surname: str = ''

    email: str = ''
    td_id: int = 0
    tg_login: str = ''
    linkedin_id: str = ''
    bio: str = ''
    avatars: list[str] = None

    created_at: datetime = None
    modified_at: datetime = None
    last_accessed_at: datetime = None


def _is_valid(user_data):
    if user_data is None:
        return False
    try:
        User(**user_data)
        return True
    except Exception as e:
        logger.debug("failed to init user from json: %s", e)
        return False


def _extract_user_fieilds(req_data):
    fields = []
    values = []
    for f in dataclasses.fields(User):
        field = f.name
        if field == "uid" or field not in req_data:
            continue
        fields.append(field)
        values.append(req_data[field])
    return fields, values


@bp.route("/<uuid:uid>/get", methods=("GET",))
@with_cursor
def get(curs, uid):
    curs.execute(f"""
        SELECT *
        FROM {consts.USERS_TABLE}
        WHERE uid = %s
    """, (uid.hex,))

    user_row = curs.fetchone()
    if user_row:
        user = User(*user_row)
        return jsonify(dataclasses.asdict(user)), codes.ok
    else:
        return jsonify(err="user not found"), codes.not_found


@bp.route("/<uuid:uid>/update", methods=("PUT",))
@with_cursor
def update(curs, uid):
    data = request.get_json(force=True, silent=True)
    if not _is_valid(data):
        return jsonify(err="failed to parse user data"), codes.bad_request
    try:
        uid = data.get("uuid")
        fields, values = _extract_user_fieilds(data)
        if uid is None:
            return jsonify(err="uuid not provided"), codes.bad_request

        curs.execute(f"""
            UPDATE {consts.USERS_TABLE}
            SET = {"= %s, ".join(fields)} = %s
            WHERE uid = %s;
        """, (*values, uid))

        return "", codes.ok
    except pg.Error as e:
        return jsonify(err=str(e)), codes.bad_request


@bp.route("/create", methods=("POST",))
@with_cursor
def create(curs):
    data = request.get_json(force=True, silent=True)
    if not _is_valid(data):
        print(data)
        return jsonify(err="failed to parse user data"), codes.not_found
    try:
        fields, values = _extract_user_fieilds(data)
        n = len(fields)

        curs.execute(f"""
            INSERT INTO {consts.USERS_TABLE} ({", ".join(fields)})
            VALUES ({", ".join(n * ["%s"])})
            RETURNING uid;
        """, tuple(values))

        uid = curs.fetchone()[0]
        return jsonify(uuid=uid), codes.ok
    except pg.Error as e:
        return jsonify(err=str(e)), codes.bad_request
