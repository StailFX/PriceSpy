# API Documentation

This document describes the JSON-based REST API for the PriceSpy application. All endpoints, request parameters, response models, and error codes are listed below.

---

## Authentication

### Obtain JWT Token

**Endpoint:** `POST /token`
**Description:** Authenticate with username and password to obtain an access token.
**Request (form data):**

* `username` (string)
* `password` (string)

**Response (200 OK):**

```json
{
  "access_token": "<token>",
  "token_type": "bearer"
}
```

**Error Codes:**

* `401 Unauthorized` — Invalid credentials.

> **Note:** Include the token in `Authorization: Bearer <token>` header for all protected endpoints.

---

## Products

> Protected endpoints (require valid JWT)

| Method | Endpoint                 | Description                |
| ------ | ------------------------ | -------------------------- |
| GET    | `/products`              | List all products          |
| POST   | `/products`              | Create a new product       |
| DELETE | `/products/{product_id}` | Delete a product by its ID |

### GET /products

* **Query Parameters:** none
* **Response (200):** Array of `Product` objects.

### POST /products

* **Request Body:** `ProductCreate`

  ```json
  {
    "name": "string",
    "sku": "string (optional)"
  }
  ```
* **Response (201):** `Product` object.

### DELETE /products/{product\_id}

* **Path Parameter:** `product_id` (integer)
* **Response (200):** `{ "message": "Product deleted" }`
* **Error Codes:**

  * `404 Not Found` — Product does not exist.

---

## Competitors

| Method | Endpoint            | Description                  |
| ------ | ------------------- | ---------------------------- |
| GET    | `/competitors`      | List competitors (paginated) |
| GET    | `/competitors/{id}` | Retrieve competitor by ID    |
| POST   | `/competitors`      | Create a new competitor      |

### GET /competitors

* **Query Parameters:**

  * `skip` (int, default=0) — Number of items to skip.
  * `limit` (int, default=100) — Max items to return.
* **Response (200):** Array of `Competitor` objects.

### GET /competitors/{id}

* **Path Parameter:** `id` (integer)
* **Response (200):** `Competitor` object.
* **Error Codes:**

  * `404 Not Found` — No competitor with given ID.

### POST /competitors

* **Request Body:** `CompetitorCreate`

  ```json
  {
    "name": "string"
  }
  ```
* **Response (201):** `Competitor` object.

---

## Prices

| Method | Endpoint  | Description                      |
| ------ | --------- | -------------------------------- |
| GET    | `/prices` | List price records for a product |
| POST   | `/prices` | Create a new price record        |

### GET /prices

* **Query Parameters:**

  * `product_id` (int, required) — Filter records by product ID.
* **Response (200):** Array of `PriceRecord` objects.

### POST /prices

* **Request Body:** `PriceRecordCreate`

  ```json
  {
    "product_id": 1,
    "competitor_id": 2,
    "price": 123.45,
    "url": "https://...",
    "date": "YYYY-MM-DD"
  }
  ```
* **Response (201):** `PriceRecord` object.

---

## Ozon Integration

| Method | Endpoint                            | Description                           |
| ------ | ----------------------------------- | ------------------------------------- |
| POST   | `/ozon/products/{product_id}/fetch` | Fetch & store price from Ozon         |
| POST   | `/ozon/products/fetch_all`          | Fetch prices for all products on Ozon |

### POST /ozon/products/{product\_id}/fetch

* **Path Parameter:** `product_id` (int)
* **Response (200):** Single `PriceRecord`.

### POST /ozon/products/fetch\_all

* **Response (200):** Array of `PriceRecord` objects.

---

## Data Models

### ProductCreate

| Field | Type   | Description                   |
| ----- | ------ | ----------------------------- |
| name  | string | Product display name          |
| sku   | string | Stock Keeping Unit (optional) |

### Product

| Field | Type              |
| ----- | ----------------- |
| id    | integer           |
| name  | string            |
| sku   | string (optional) |

### CompetitorCreate

| Field | Type   |
| ----- | ------ |
| name  | string |

### Competitor

| Field | Type    |
| ----- | ------- |
| id    | integer |
| name  | string  |

### PriceRecordBase

| Field          | Type    | Description                           |
| -------------- | ------- | ------------------------------------- |
| product\_id    | integer | ID of the product                     |
| competitor\_id | integer | ID of the competitor                  |
| price          | float   | Price value                           |
| url            | string  | Source URL for the price              |
| date           | date    | Date of the price record (YYYY-MM-DD) |

### PriceRecord

Includes all fields from `PriceRecordBase` plus:

| Field            | Type    | Description                          |
| ---------------- | ------- | ------------------------------------ |
| id               | integer | Unique record ID                     |
| competitor\_name | string  | Name of the competitor (for display) |

---

## Error Responses

| Status Code               | Condition                     |
| ------------------------- | ----------------------------- |
| 400 Bad Request           | Invalid payload or parameters |
| 401 Unauthorized          | Missing or invalid auth token |
| 404 Not Found             | Resource not found            |
| 500 Internal Server Error | Unexpected error              |
