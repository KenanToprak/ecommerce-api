def test_create_product_requires_admin(client, user_headers, admin_headers):
    payload = {
        "name": "Monitor 4K",
        "description": "27-inch IPS",
        "price": 349.99,
        "stock_quantity": 5,
    }

    # Unauthenticated
    r_unauth = client.post("/products/", json=payload)
    assert r_unauth.status_code == 401

    # Regular authenticated non-admin user
    r_user = client.post("/products/", json=payload, headers=user_headers)
    assert r_user.status_code == 403

    # Admin user
    r_admin = client.post("/products/", json=payload, headers=admin_headers)
    assert r_admin.status_code == 201
    data = r_admin.json()
    assert data["name"] == "Monitor 4K"
    assert data["price"] == 349.99
    assert data["stock_quantity"] == 5


def test_create_product_validation_rejects_invalid_fields(client, admin_headers):
    # Blank / whitespace-only name
    r_blank = client.post(
        "/products/",
        json={"name": "   ", "price": 10.0, "stock_quantity": 1},
        headers=admin_headers,
    )
    assert r_blank.status_code == 422

    # Zero, negative, or non-finite price
    for bad_price in (0, -12.5, "NaN", "inf"):
        r_price = client.post(
            "/products/",
            json={"name": "Item", "price": bad_price, "stock_quantity": 1},
            headers=admin_headers,
        )
        assert r_price.status_code == 422

    # Negative stock
    r_stock = client.post(
        "/products/",
        json={"name": "Item", "price": 10.0, "stock_quantity": -1},
        headers=admin_headers,
    )
    assert r_stock.status_code == 422


def test_list_and_get_products_with_pagination(client, sample_products):
    r_list = client.get("/products/?skip=0&limit=1")
    assert r_list.status_code == 200
    items = r_list.json()
    assert len(items) == 1
    assert items[0]["id"] == sample_products[0].id

    r_second = client.get("/products/?skip=1&limit=1")
    assert r_second.status_code == 200
    assert r_second.json()[0]["id"] == sample_products[1].id

    r_one = client.get(f"/products/{sample_products[0].id}")
    assert r_one.status_code == 200
    assert r_one.json()["name"] == "Mechanical Keyboard"

    r_missing = client.get("/products/99999")
    assert r_missing.status_code == 404


def test_products_pagination_bounds_rejected(client):
    assert client.get("/products/?skip=-1").status_code == 422
    assert client.get("/products/?limit=0").status_code == 422
    assert client.get("/products/?limit=101").status_code == 422
