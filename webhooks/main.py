import base64
import hashlib
import hmac
import json
import requests
import uuid
import os


def check_signature(request_data, key):
    local_digest = hmac.new(bytes(key, 'utf-8'), request_data.data, digestmod=hashlib.sha256).digest()
    received_digest = base64.b64decode(bytes(request_data.headers['X-Todoist-Hmac-Sha256'], 'utf-8'))

    return hmac.compare_digest(local_digest, received_digest)


def check_label(request_data, label):
    return label in request_data.json['event_data']['labels']


def duplicate_task(request_data):
    old_task = request_data.json['event_data']
    requests.post(
        "https://api.todoist.com/rest/v1/tasks",
        data=json.dumps({
            "content": old_task['content'],
            "project_id": old_task['project_id'],
            "section_id": old_task['section_id'],
            "parent": old_task['parent_id'],
            "order": old_task['child_order'],
            "label_ids": old_task['labels'],
            "priority": old_task['priority']
        }),
        headers={
            "Content-Type": "application/json",
            "X-Request-Id": str(uuid.uuid4()),
            "Authorization": "Bearer %s" % os.environ.get('USER_TOKEN')
        }).json()


def webhooks(request):
    if not check_signature(request, os.environ.get('TODOIST_CLIENT_SECRET')):
        return '', 403

    # get user's token based on the payload user; otherwise return 403
    # TODO

    # check if the label is 'timeless-habit'; otherwise ignore
    if check_label(request, os.environ.get('TIMELESS_LABEL')):
        # try to recreate / duplicate the item
        duplicate_task(request)

    return '', 204
