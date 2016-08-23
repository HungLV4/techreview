# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class EtsyItem(scrapy.Item):
    shopOwner = scrapy.Field()
    etsyUrl = scrapy.Field()
    shopName = scrapy.Field()
    joinDate = scrapy.Field()
    ratingCount = scrapy.Field()
    ratingScore = scrapy.Field()
    sales = scrapy.Field()
    location = scrapy.Field()
    categories = scrapy.Field()
    links = scrapy.Field()

class ZorgkaartrItem(scrapy.Item):
    name = scrapy.Field()
    beroep = scrapy.Field()
    specialisme = scrapy.Field()
    zorginstelling = scrapy.Field()
    location = scrapy.Field()


class CoopItem(scrapy.Item):
    id = scrapy.Field()
    name = scrapy.Field()
    category = scrapy.Field()
    des = scrapy.Field()
    source = scrapy.Field()
    ingre = scrapy.Field()
    info = scrapy.Field()
    images = scrapy.Field()
    allergy = scrapy.Field()
    madein = scrapy.Field()
    url = scrapy.Field()

class TecSpecsItem(scrapy.Item):
    product = scrapy.Field()
    name = scrapy.Field()
    brand = scrapy.Field()
    specs = scrapy.Field()
    pros = scrapy.Field()
    cons = scrapy.Field()
    benchmarks = scrapy.Field()
    size_images = scrapy.Field()
    yt_videos = scrapy.Field()
    images = scrapy.Field()
    thumbnail = scrapy.Field()
    stats = scrapy.Field()
    source = scrapy.Field()

class TechreviewItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field() # product name
    brand = scrapy.Field() # producer company name
    product = scrapy.Field() # type of product: computer, smartphone, etc
    released = scrapy.Field() # released date
    images = scrapy.Field() # product image url
    thumbnail = scrapy.Field()
    headline = scrapy.Field() # overall review headline
    score = scrapy.Field() # overall score by engadget
    criticScores = scrapy.Field()
    userScores = scrapy.Field()
    criticReviews = scrapy.Field()
    userReviews = scrapy.Field()
    stats = scrapy.Field()
    source = scrapy.Field()