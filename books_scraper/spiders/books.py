import random

import scrapy

from books_scraper.items import BookItem


class BooksSpider(scrapy.Spider):
    name = "books"
    start_urls = ["https://books.toscrape.com/index.html"]

    def parse(self, response):
        categories = response.css(".nav>li>ul>li>a")

        selected_categories = random.sample(
            list(categories),
            min(5, len(categories))
        )

        for category in selected_categories:
            category_name = category.xpath('./text()').get()
            category_url = category.css("::attr(href)").get()

            yield response.follow(
                category_url,
                callback=self.parse_category,
                meta={
                    "category": category_name,
                    "books": [],
                },
            )

    def parse_category(self, response):
        category = response.meta["category"]
        books = response.meta["books"]
        current_page_books = response.xpath("//article[@class='product_pod']")
        books.extend(current_page_books)

        next_page_url = response.css(".next>a::attr(href)").get()

        if next_page_url:
            yield response.follow(
                next_page_url,
                callback=self.parse_category,
                meta={
                    "category": category,
                    "books": books,
                },
            )
        else:
            selected_books = random.sample(
                books,
                min(5, len(books))
            )

            for book in selected_books:
                yield BookItem(
                    title=book.css("h3>a::attr(title)").get(),
                    price=book.xpath(".//p[@class='price_color']/text()").get(),
                    availability=book.css(".availability::text").getall()[1],
                    product_url=book.xpath(".//h3/a/@href").get(),
                    image_url=book.css("img::attr(src)").get(),
                    category=category,
                )
