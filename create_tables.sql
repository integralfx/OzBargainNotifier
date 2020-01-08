CREATE TABLE IF NOT EXISTS Sales (
	id	INTEGER PRIMARY KEY,
	last_update	TEXT,
	title	TEXT,
	link	TEXT,
	expiry	TEXT,
	date_published	TEXT,
	creator	TEXT
);

CREATE TABLE IF NOT EXISTS Category (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    link TEXT UNIQUE,
);

CREATE TABLE IF NOT EXISTS SalesCategory (
    sales_id INTEGER,
    category_id INTEGER,
    PRIMARY KEY(sales_id, category_id),
    FOREIGN KEY(sales_id) REFERENCES Sale(id),
    FOREIGN KEY(category_id) REFERENCES Category(id)
);