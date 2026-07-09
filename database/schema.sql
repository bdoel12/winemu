-- ============================================
-- WINEMU DATABASE SCHEMA (MySQL 8.0+)
-- Updated: 2026-07-08 — includes all migrations
-- ============================================

CREATE DATABASE IF NOT EXISTS winemu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE winemu;

CREATE TABLE categories (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	slug VARCHAR(100) NOT NULL, 
	icon VARCHAR(100), 
	description TEXT, 
	is_active BOOL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	full_name VARCHAR(100), 
	bio TEXT, 
	avatar_url VARCHAR(500), 
	phone VARCHAR(20), 
	location VARCHAR(100), 
	latitude FLOAT, 
	longitude FLOAT, 
	`role` VARCHAR(20), 
	is_active BOOL, 
	is_verified BOOL, 
	response_rate FLOAT, 
	rating FLOAT, 
	total_reports INTEGER, 
	total_found INTEGER, 
	reset_token VARCHAR(255), 
	reset_token_expires DATETIME, 
	last_login DATETIME, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE activity_logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER, 
	action VARCHAR(100) NOT NULL, 
	resource_type VARCHAR(50), 
	resource_id INTEGER, 
	ip_address VARCHAR(45), 
	user_agent VARCHAR(500), 
	data JSON, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE notifications (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	actor_id INTEGER, 
	type VARCHAR(50) NOT NULL, 
	title VARCHAR(200), 
	message TEXT, 
	data JSON, 
	is_read BOOL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(actor_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE reports (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	type ENUM('hilang','ditemukan') NOT NULL, 
	status ENUM('aktif','proses','selesai','ditutup'), 
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	category_id INTEGER, 
	verification_question VARCHAR(300),
	verification_answer VARCHAR(500),
	location_name VARCHAR(200), 
	latitude FLOAT, 
	longitude FLOAT, 
	date_occurred DATETIME, 
	reward VARCHAR(200), 
	contact_info VARCHAR(200), 
	like_count INTEGER, 
	comment_count INTEGER, 
	share_count INTEGER, 
	view_count INTEGER, 
	is_verified BOOL, 
	is_active BOOL, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(category_id) REFERENCES categories (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bookmarks (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	report_id INTEGER NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, report_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(report_id) REFERENCES reports (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE claims (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	report_id INTEGER NOT NULL, 
	claimant_id INTEGER NOT NULL, 
	answer TEXT, 
	status ENUM('pending','approved','rejected','disputed'), 
	priority ENUM('rendah','sedang','tinggi'), 
	admin_notes TEXT, 
	resolved_by INTEGER, 
	resolved_at DATETIME, 
	deadline DATETIME,
	handover_method ENUM('cod','titik_aman','kurir'),
	handover_location VARCHAR(300),
	handover_tracking VARCHAR(200),
	handover_status ENUM('menunggu_metode','dalam_proses','selesai'),
	handover_completed_at DATETIME,
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(report_id) REFERENCES reports (id) ON DELETE CASCADE, 
	FOREIGN KEY(claimant_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(resolved_by) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE comments (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	report_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	parent_id INTEGER, 
	content TEXT NOT NULL, 
	is_active BOOL, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(report_id) REFERENCES reports (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(parent_id) REFERENCES comments (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE conversations (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	report_id INTEGER, 
	user1_id INTEGER NOT NULL, 
	user2_id INTEGER NOT NULL, 
	status ENUM('pending','active','closed'), 
	last_message_at DATETIME, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(report_id) REFERENCES reports (id) ON DELETE CASCADE, 
	FOREIGN KEY(user1_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(user2_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE report_likes (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	report_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (report_id, user_id), 
	FOREIGN KEY(report_id) REFERENCES reports (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE report_media (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	report_id INTEGER NOT NULL, 
	url VARCHAR(500) NOT NULL, 
	type ENUM('image','video'), 
	filename VARCHAR(255), 
	size INTEGER, 
	`order` INTEGER, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(report_id) REFERENCES reports (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Messages table — fully updated with pin & reply columns (migration e5f2a1b3c4d0)
CREATE TABLE messages (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	conversation_id INTEGER NOT NULL, 
	sender_id INTEGER NOT NULL, 
	content TEXT NOT NULL, 
	type VARCHAR(20), 
	is_read BOOL DEFAULT 0,
	is_pinned BOOL DEFAULT 0,
	reply_to_id INTEGER,
	reply_to_content TEXT,
	reply_to_sender VARCHAR(100),
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id) ON DELETE CASCADE, 
	FOREIGN KEY(sender_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(reply_to_id) REFERENCES messages (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE user_ratings (
	id INTEGER NOT NULL AUTO_INCREMENT,
	rater_id INTEGER NOT NULL,
	rated_id INTEGER NOT NULL,
	report_id INTEGER,
	rating FLOAT NOT NULL,
	review TEXT,
	created_at DATETIME,
	PRIMARY KEY (id),
	FOREIGN KEY(rater_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(rated_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(report_id) REFERENCES reports (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
