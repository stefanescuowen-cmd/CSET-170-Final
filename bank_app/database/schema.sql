CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    ssn TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT NOT NULL,
    password TEXT NOT NULL,

    approved BOOLEAN DEFAULT 0,
    is_admin BOOLEAN DEFAULT 0,

    account_number TEXT UNIQUE,
    balance REAL DEFAULT 0.0
);

INSERT INTO users (username, first_name, last_name, ssn, address, phone, password, approved, is_admin)
VALUES ('admin', 'Admin', 'User', '000-00-0000', 'Bank HQ', '1234567890', '<hashed_password>', 1, 1);