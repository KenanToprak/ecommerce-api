from core.security import create_access_token
from models.order import Order
from models.product import Product
from models.user import User


def test_create_order_unauthenticated_rejected(client, sample_products):
    response = client.post(
        "/orders/",
        json={"items": [{"product_id": sample_products[0].id, "quantity": 1}]},
    )
    assert response.status_code == 401


def test_create_order_success_and_stock_deduction(client, db_session, user_headers, sample_products):
    p1, p2 = sample_products
    response = client.post(
        "/orders/",
        json={
            "items": [
                {"product_id": p1.id, "quantity": 2},
                {"product_id": p2.id, "quantity": 1},
            ]
        },
        headers=user_headers,
    )
    assert response.status_code == 201
    data = response.json()
    # 2 * 99.99 + 1 * 25.50 = 225.48
    assert data["total_price"] == 225.48
    assert len(data["items"]) == 2

    db_session.expire_all()
    assert db_session.get(Product, p1.id).stock_quantity == 8
    assert db_session.get(Product, p2.id).stock_quantity == 2


def test_create_order_aggregates_duplicate_product_ids(client, db_session, user_headers, sample_products):
    p1, p2 = sample_products
    # p2 has stock 3; ordering 2 + 1 in separate lines aggregates to 3
    response = client.post(
        "/orders/",
        json={
            "items": [
                {"product_id": p2.id, "quantity": 2},
                {"product_id": p2.id, "quantity": 1},
            ]
        },
        headers=user_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 3
    assert data["total_price"] == 76.5

    db_session.expire_all()
    assert db_session.get(Product, p2.id).stock_quantity == 0

    # Exceeding stock across duplicate lines (e.g. 2 + 2 for stock 10 -> ok, vs 6 + 5 > 10 -> 400)
    fail_resp = client.post(
        "/orders/",
        json={
            "items": [
                {"product_id": p1.id, "quantity": 6},
                {"product_id": p1.id, "quantity": 5},
            ]
        },
        headers=user_headers,
    )
    assert fail_resp.status_code == 400
    db_session.expire_all()
    assert db_session.get(Product, p1.id).stock_quantity == 10


def test_create_order_rejects_negative_zero_quantity_and_empty_items(client, user_headers, sample_products):
    p1 = sample_products[0]
    for bad_qty in (0, -5):
        r_qty = client.post(
            "/orders/",
            json={"items": [{"product_id": p1.id, "quantity": bad_qty}]},
            headers=user_headers,
        )
        assert r_qty.status_code == 422

    r_empty = client.post("/orders/", json={"items": []}, headers=user_headers)
    assert r_empty.status_code == 422


def test_partial_order_failure_leaves_zero_orphan_orders_and_unchanged_stock(
    client, db_session, user_headers, sample_products
):
    p1, p2 = sample_products

    # Item 1 valid, Item 2 nonexistent product -> 404, 0 orders, stock unchanged
    r_missing = client.post(
        "/orders/",
        json={
            "items": [
                {"product_id": p1.id, "quantity": 2},
                {"product_id": 99999, "quantity": 1},
            ]
        },
        headers=user_headers,
    )
    assert r_missing.status_code == 404
    assert db_session.query(Order).count() == 0
    db_session.expire_all()
    assert db_session.get(Product, p1.id).stock_quantity == 10

    # Item 1 valid, Item 2 insufficient stock -> 400, 0 orders, stock unchanged
    r_stock = client.post(
        "/orders/",
        json={
            "items": [
                {"product_id": p1.id, "quantity": 2},
                {"product_id": p2.id, "quantity": 99},
            ]
        },
        headers=user_headers,
    )
    assert r_stock.status_code == 400
    assert db_session.query(Order).count() == 0
    db_session.expire_all()
    assert db_session.get(Product, p1.id).stock_quantity == 10
    assert db_session.get(Product, p2.id).stock_quantity == 3


def test_my_orders_isolation_and_pagination(client, db_session, user_headers, admin_user, sample_products):
    p1 = sample_products[0]
    # Place two orders as regular_user
    r1 = client.post(
        "/orders/",
        json={"items": [{"product_id": p1.id, "quantity": 1}]},
        headers=user_headers,
    )
    r2 = client.post(
        "/orders/",
        json={"items": [{"product_id": p1.id, "quantity": 2}]},
        headers=user_headers,
    )
    assert r1.status_code == 201 and r2.status_code == 201

    # Place one order as admin_user
    admin_token = create_access_token(data={"sub": str(admin_user.id)})
    r_admin = client.post(
        "/orders/",
        json={"items": [{"product_id": p1.id, "quantity": 1}]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_admin.status_code == 201

    # Regular user sees only their 2 orders, newest first
    my_resp = client.get("/orders/my-orders?skip=0&limit=10", headers=user_headers)
    assert my_resp.status_code == 200
    my_orders = my_resp.json()
    assert len(my_orders) == 2
    assert my_orders[0]["id"] > my_orders[1]["id"]
    assert all(o["user_id"] != admin_user.id for o in my_orders)

    # Pagination bounds
    assert client.get("/orders/my-orders?skip=-1", headers=user_headers).status_code == 422
    assert client.get("/orders/my-orders?limit=0", headers=user_headers).status_code == 422
    assert client.get("/orders/my-orders?limit=101", headers=user_headers).status_code == 422
