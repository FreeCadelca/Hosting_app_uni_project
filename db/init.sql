-- Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tariff plans (pre-populated)
CREATE TABLE IF NOT EXISTS plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    cpu INT NOT NULL,
    ram_mb INT NOT NULL,
    disk_gb INT NOT NULL,
    price_monthly DECIMAL(10,2) NOT NULL
);

-- User servers
CREATE TABLE IF NOT EXISTS servers (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    plan_id INT REFERENCES plans(id),
    hostname VARCHAR(255),
    ip_address VARCHAR(45),
    root_password VARCHAR(255),
    os VARCHAR(100) DEFAULT 'Ubuntu 22.04',
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Orders / payments
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    plan_id INT REFERENCES plans(id),
    server_id INT REFERENCES servers(id),
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pre-populate plans
INSERT INTO plans (name, cpu, ram_mb, disk_gb, price_monthly) VALUES
('VPS Basic', 1, 1024, 20, 5.00),
('VPS Standard', 2, 2048, 40, 10.00),
('VPS Pro', 4, 4096, 80, 20.00);
