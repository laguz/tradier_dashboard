# Tradier Financial Dashboard API

A Flask-based API for managing user brokerage accounts and viewing financial data by securely integrating with the Tradier developer sandbox.

---

## Features

- 🔐 **JWT Authentication**: Secure user registration and login.
- 🔗 **Account Linking**: Securely store user Tradier API keys.
- 📈 **Portfolio Tracking**: Fetch and view current market positions.
- 📊 **Market Data**: Get real-time stock quotes for multiple symbols.
- 💡 **Performance Analytics**: Calculate high-level portfolio performance metrics like total value and unrealized gains/losses.

---

## Tech Stack

- **Backend**: Flask
- **Database**: MongoDB
- **Containerization**: Docker & Docker Compose
- **Testing**: Pytest

---

## API Endpoints

### Authentication

- `POST /auth/register`
  - **Description**: Creates a new user.
  - **Body**: `{ "username": "string", "email": "string", "password": "string" }`
  - **Response**: `{ "id": "...", "username": "...", "email": "..." }`

- `POST /auth/login`
  - **Description**: Authenticates a user.
  - **Body**: `{ "email": "string", "password": "string" }`
  - **Response**: `{ "access_token": "jwt_token" }`

### Account Management (Requires Authentication)

- `POST /accounts/link`
  - **Description**: Links a user's Tradier API key.
  - **Body**: `{ "tradier_api_key": "string" }`
  - **Response**: `{ "message": "Tradier API key linked successfully" }`

- `GET /accounts/positions`
  - **Description**: Fetches the user's current market positions.
  - **Response**: A list of position objects from Tradier.

### Market Data (Requires Authentication)

- `GET /market/quotes?symbols=AAPL,GOOG`
  - **Description**: Fetches stock quotes.
  - **Response**: A list of quote objects from Tradier.

### Analytics (Requires Authentication)

- `GET /analytics/performance`
  - **Description**: Provides a performance summary of the user's portfolio.
  - **Response**:
    ```json
    {
      "total_portfolio_value": 125430.50,
      "total_cost_basis": 112800.00,
      "unrealized_gain_loss": 12630.50,
      "top_positions_by_value": [
        { "symbol": "AAPL", "market_value": 35000.20 },
        { "symbol": "MSFT", "market_value": 28500.80 }
      ]
    }
    ```

---

## Getting Started

### Prerequisites

- [Docker](https.docs.docker.com/get-docker/)
- [Docker Compose](https.docs.docker.com/compose/install/)

### Setup & Installation

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/laguz/tradier_dashboard.git](https://github.com/laguz/tradier_dashboard.git)
    cd tradier_dashboard
    ```

2.  **Create an environment file:**
    Create a `.env` file in the project root and add the following variables. Use a secure method to generate your keys.
    ```env
    FLASK_ENV=development
    SECRET_KEY=your_strong_encryption_key
    JWT_SECRET_KEY=your_strong_jwt_secret_key
    MONGO_URI=mongodb://mongodb:27017/tradier_dashboard
    TRADIER_API_BASE_URL=[https://sandbox.tradier.com](https://sandbox.tradier.com)
    ```

3.  **Build and run the containers:**
    ```sh
    docker-compose up --build
    ```
    The API will be available at `http://localhost:5000`.

---

## Running the Tests

To run the tests, execute the following command in the project root:

```sh
docker-compose exec web pytest