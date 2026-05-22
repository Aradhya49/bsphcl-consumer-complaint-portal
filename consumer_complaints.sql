-- ================================================================
-- BSPHCL Consumer Complaint Portal – MySQL Database Schema
-- ================================================================
-- Run this file in MySQL Workbench or via:
--   mysql -u root -p < consumer_complaints.sql
-- ================================================================

CREATE DATABASE IF NOT EXISTS consumer_portal
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE consumer_portal;

-- ── Users Table ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INT          AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) NOT NULL UNIQUE,
    mobile      VARCHAR(15)  NOT NULL UNIQUE,
    password    VARCHAR(256) NOT NULL,
    consumer_id VARCHAR(20)  NOT NULL UNIQUE,
    role        VARCHAR(20)  NOT NULL DEFAULT 'user',  -- user | staff | admin
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Complaints Table ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaints (
    id             INT          AUTO_INCREMENT PRIMARY KEY,
    user_id        INT          NOT NULL,
    complaint_type VARCHAR(100),
    subcategory    VARCHAR(100),
    description    TEXT,
    status         VARCHAR(50)  NOT NULL DEFAULT 'Pending',   -- Pending | Under Review | Resolved
    priority       VARCHAR(20)  NOT NULL DEFAULT 'Medium',    -- Low | Medium | High
    attachment     VARCHAR(255),                               -- stored filename
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_complaints_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- ── Replies Table ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS replies (
    id           INT      AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT      NOT NULL,
    user_id      INT      NOT NULL,
    message      TEXT     NOT NULL,
    role         VARCHAR(20),          -- admin | staff | user
    timestamp    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_replies_complaint
        FOREIGN KEY (complaint_id) REFERENCES complaints(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_replies_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- ── OTP Table ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS otp (
    id         INT          AUTO_INCREMENT PRIMARY KEY,
    email      VARCHAR(150) NOT NULL,
    otp        VARCHAR(6)   NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_otp_email (email)
);

-- ── Indexes for performance ───────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_complaints_user_id ON complaints(user_id);
CREATE INDEX IF NOT EXISTS idx_complaints_status  ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_replies_complaint  ON replies(complaint_id);

-- ================================================================
-- Sample Data (optional – remove before production deployment)
-- ================================================================

-- Default admin (password: Admin@123)
INSERT IGNORE INTO users (name, email, mobile, password, consumer_id, role)
VALUES (
    'BSPHCL Admin',
    'admin@bsphcl.co.in',
    '9000000000',
    'scrypt:32768:8:1$placeholder$hashed',   -- replaced by init_db.py
    'ADMIN000001',
    'admin'
);

-- ================================================================
-- END OF SCHEMA
-- ================================================================
