"""
Unit tests for Demo E-Commerce Flask application
================================================
Validates route behaviors, normal traffic rendering, and honeypot triggers.
"""

import pytest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, DEMO_PRODUCTS

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_route(client):
    """Test that the home route renders successfully"""
    res = client.get("/")
    assert res.status_code == 200
    assert b"Welcome to TechStore" in res.data

def test_products_route(client):
    """Test that the products page displays the catalogs with descriptions"""
    res = client.get("/products")
    assert res.status_code == 200
    for product in DEMO_PRODUCTS:
        assert product["name"].encode() in res.data
        assert product["description"].encode() in res.data

def test_login_route_get(client):
    """Test that the login page loads with credentials helper info"""
    res = client.get("/login")
    assert res.status_code == 200
    assert b"demo@example.com" in res.data

def test_login_route_post_success(client):
    """Test login with correct credentials redirects to products"""
    res = client.post("/login", data={
        "email": "demo@example.com",
        "password": "password123"
    })
    assert res.status_code == 302
    assert "/products" in res.headers["Location"]

def test_login_route_post_failure(client):
    """Test login with wrong credentials renders error message"""
    res = client.post("/login", data={
        "email": "demo@example.com",
        "password": "wrongpassword"
    })
    assert res.status_code == 200
    assert b"Invalid credentials" in res.data

@patch('app.honeycloud.send_honeypot_hit')
def test_honeypot_admin_route(mock_hit, client):
    """Test that accessing /admin returns a 404 and calls HoneyCloudClient"""
    mock_hit.return_value = True
    res = client.get("/admin")
    assert res.status_code == 404
    mock_hit.assert_called_once()
    args, kwargs = mock_hit.call_args
    assert kwargs["endpoint"] == "/admin"
    assert kwargs["severity"] == "CRITICAL"

@patch('app.honeycloud.send_honeypot_hit')
def test_honeypot_env_route(mock_hit, client):
    """Test that accessing /.env returns a 404 and alerts HoneyCloud"""
    mock_hit.return_value = True
    res = client.get("/.env")
    assert res.status_code == 404
    mock_hit.assert_called_once()
    args, kwargs = mock_hit.call_args
    assert kwargs["endpoint"] == "/.env"
    assert kwargs["severity"] == "CRITICAL"

@patch('app.honeycloud.send_honeypot_hit')
def test_honeypot_wp_route(mock_hit, client):
    """Test that accessing /wp-login.php returns a 404 and alerts HoneyCloud"""
    mock_hit.return_value = True
    res = client.get("/wp-login.php")
    assert res.status_code == 404
    mock_hit.assert_called_once()
    args, kwargs = mock_hit.call_args
    assert kwargs["endpoint"] == "/wp-login.php"
    assert kwargs["severity"] == "HIGH"
