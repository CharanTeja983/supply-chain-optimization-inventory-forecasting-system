-- Reference schema. The SQLAlchemy models create these tables automatically at startup.
CREATE DATABASE IF NOT EXISTS supply_chain;
USE supply_chain;
CREATE TABLE IF NOT EXISTS suppliers (
  supplier_id INT AUTO_INCREMENT PRIMARY KEY,
  supplier_name VARCHAR(150) NOT NULL UNIQUE,
  email VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS products (
  product_id INT AUTO_INCREMENT PRIMARY KEY,
  sku VARCHAR(80) NOT NULL UNIQUE,
  product_name VARCHAR(200) NOT NULL,
  unit_cost FLOAT NOT NULL DEFAULT 0,
  lead_time_days INT NOT NULL DEFAULT 7,
  reorder_point INT NOT NULL DEFAULT 0,
  INDEX idx_products_sku (sku)
);
CREATE TABLE IF NOT EXISTS purchase_orders (
  po_id INT AUTO_INCREMENT PRIMARY KEY,
  supplier_id INT NOT NULL,
  order_date DATE NOT NULL,
  expected_date DATE NULL,
  received_date DATE NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'ordered',
  FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);
CREATE TABLE IF NOT EXISTS stock_transactions (
  transaction_id INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL,
  transaction_date DATE NOT NULL,
  transaction_type VARCHAR(30) NOT NULL,
  quantity INT NOT NULL,
  FOREIGN KEY (product_id) REFERENCES products(product_id),
  INDEX idx_stock_product_date (product_id, transaction_date)
);
CREATE TABLE IF NOT EXISTS demand_records (
  demand_id INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL,
  demand_date DATE NOT NULL,
  quantity INT NOT NULL,
  FOREIGN KEY (product_id) REFERENCES products(product_id),
  INDEX idx_demand_product_date (product_id, demand_date)
);
