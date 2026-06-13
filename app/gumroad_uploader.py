"""
Yeshua Architect Platform — Gumroad Integration

Generates agent packages as .zip files and attaches them to Gumroad products.
Each Gumroad product = one tier = one pre-built agent package.
"""

import json
import urllib.request
from app.package_generator import create_agent_zip_package
from app.models import AgentIntake


def upload_zip_to_gumroad(product_id: str, zip_bytes: bytes, filename: str, gumroad_token: str) -> dict:
    """
    Upload a .zip file as a product variant/file to Gumroad.

    Gumroad API endpoint: POST /v2/products/:id/files
    """
    url = f"https://api.gumroad.com/v2/products/{product_id}/files?access_token={gumroad_token}"

    # Multipart upload
    boundary = "----GumroadBoundary7MA4YWxkTrZu0gW"
    body = []
    body.append(f"--{boundary}")
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"')
    body.append("Content-Type: application/zip")
    body.append("")
    body.append(zip_bytes.decode("latin-1"))  # Binary-safe encoding
    body.append(f"--{boundary}--")

    payload = "\r\n".join(body).encode("latin-1")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": e.code, "body": body[:500]}


GUMROAD_PRODUCTS = {
    "quick_audit": {
        "id": "ki5CJT63TngDwlkdWiEQ==",
        "name": "Quick Audit",
        "price": 11,
    },
    "starter_build": {
        "id": "A7xaqWzdZpwwHu2esJ2-Bg==",
        "name": "Starter Build",
        "price": 20,
    },
    "full_audit": {
        "id": "bZOxWHo0iyg9tGlIzjlFFg==",
        "name": "Full Audit",
        "price": 49,
    },
    "cognitive_solvency": {
        "id": "-ZK70byAEvjh-Ert0Zsw0g==",
        "name": "Cognitive Solvency Audit",
        "price": 99,
    },
    "pro_build": {
        "id": "vw7OrLskPa9IcCxflrLQrg==",
        "name": "Pro Build",
        "price": 149,
    },
    "full_system": {
        "id": "wtlb0_tM80qiTN-_1L7fbQ==",
        "name": "Full System",
        "price": 299,
    },
}


def generate_and_attach_package(
    product_key: str,
    intake: AgentIntake,
    verdict: dict,
    poa_receipt_id: str,
    gumroad_token: str,
) -> dict:
    """
    Generate a .zip package and attach it to the matching Gumroad product.

    Returns the Gumroad API response.
    """
    product = GUMROAD_PRODUCTS.get(product_key)
    if not product:
        return {"error": f"Unknown product key: {product_key}"}

    # Generate the zip
    zip_bytes = create_agent_zip_package(
        intake=intake,
        verdict=verdict,
        poa_receipt_id=poa_receipt_id,
        tier=product_key,
    )

    # Create filename
    safe_name = intake.agent_name.lower().replace(" ", "-")
    filename = f"{safe_name}-{product_key}.zip"

    # Upload to Gumroad
    result = upload_zip_to_gumroad(
        product_id=product["id"],
        zip_bytes=zip_bytes,
        filename=filename,
        gumroad_token=gumroad_token,
    )

    return result
