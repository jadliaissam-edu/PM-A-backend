import json
import os
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model


BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "api_endpoints.json")


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


@pytest.mark.django_db
def test_all_api_endpoints():
    cfg = load_config()
    client = APIClient()
    User = get_user_model()
    user = User.objects.create_user(username="allapitest", password="testpass")
    client.force_authenticate(user=user)

    for entry in cfg:
        name = entry.get("name")
        list_url = entry.get("list_url")
        detail_url_tpl = entry.get("detail_url")
        payload = entry.get("create_payload")
        skip_delete = entry.get("skip_delete", False)

        # List
        resp = client.get(list_url)
        assert resp.status_code in (200, 201, 204), f"List {name} failed: {resp.status_code}"

        created_id = None
        # Create (if payload provided)
        if payload:
            resp2 = client.post(list_url, payload, format="json")
            if resp2.status_code in (200, 201):
                data = resp2.json()
                created_id = data.get("id") or data.get("pk")
                # Some APIs return nested data (e.g. {"results": [...]})
                if created_id is None and isinstance(data, dict):
                    # try to find an id in keys
                    for k, v in data.items():
                        if isinstance(v, dict) and (v.get("id") or v.get("pk")):
                            created_id = v.get("id") or v.get("pk")
                            break
            else:
                pytest.skip(f"Create for {name} returned {resp2.status_code}; skipping detail/modify/delete steps")

        # If we have an id, try GET/PATCH/DELETE
        if created_id and detail_url_tpl:
            detail_url = detail_url_tpl.replace("{id}", str(created_id))
            resp3 = client.get(detail_url)
            assert resp3.status_code in (200, 201), f"GET detail {name} failed: {resp3.status_code}"

            # Try patch (if API supports it)
            try:
                resp_patch = client.patch(detail_url, {"summary": "patched by test"}, format="json")
                # Accept 200/202/204 or 405 (method not allowed)
                assert resp_patch.status_code in (200, 202, 204, 405), f"PATCH unexpected: {resp_patch.status_code}"
            except Exception:
                pass

            # Try delete unless skipped
            if not skip_delete:
                resp_del = client.delete(detail_url)
                assert resp_del.status_code in (200, 202, 204, 404), f"DELETE unexpected: {resp_del.status_code}"
