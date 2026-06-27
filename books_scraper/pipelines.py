import re
import sqlite3


class CleanBookDataPipeline:
    def process_item(self, item, spider):
        item["title"] = item["title"].strip()
        item["price"] = float(re.sub(r"[^\d.]", "", item["price"]))
        item["availability"] = "In stock" in item["availability"]
        item["category"] = item["category"].strip()

        return item

class SQLitePipeline:
    def open_spider(self, spider):
        database_name = spider.settings.get("DATABASE_NAME")
        self.connection = sqlite3.connect(database_name)
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                price REAL,
                availability BOOLEAN,
                product_url TEXT,
                image_url TEXT,
                category TEXT
            )
        """)

        self.connection.commit()

    def process_item(self, item, spider):
        self.cursor.execute("""
            INSERT INTO books (
                title,
                price,
                availability,
                product_url,
                image_url,
                category
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            item["title"],
            item["price"],
            item["availability"],
            item["product_url"],
            item["image_url"],
            item["category"],
        ))

        self.connection.commit()

        return item

    def close_spider(self, spider):
        self.connection.close()
