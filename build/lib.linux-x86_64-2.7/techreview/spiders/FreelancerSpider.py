from scrapy import Spider
from scrapy.selector import Selector
from scrapy.http import HtmlResponse, Request
from techreview.items import ZorgkaartrItem, EtsyItem
from dateutil import parser

class ZorgkaartrSpider(Spider):
	name = "zorgkaart"
	allowed_domains = ["www.zorgkaartnederland.nl/", "www.zorgkaartnederland.nl", "zorgkaartnederland.nl"]
	start_urls = ["https://www.zorgkaartnederland.nl/overzicht/beroepen"]

	def parse(self, response):
		selector = Selector(response=response)

		list_groups = selector.xpath('//ul[contains(@class, "list-group")]')
		for group in list_groups:
			group_items = group.xpath('.//li[@class="list-group-item"]')
			for group_item in group_items:
				link = group_item.xpath('.//a/@href').extract()

				yield Request("https://www.zorgkaartnederland.nl" + link[0], callback=self.parseItem)
				
	def parseItem(self, response):
		selector = Selector(response=response)

		medias = selector.xpath('//ul[@id="results"]/li[@class="media"]')
		for media in medias:
			item = ZorgkaartrItem()

			media_body = media.xpath('.//div[@class="media-body"]')

			item["name"] = (media_body.xpath('.//h4/a/text()').extract())[0]
			
			title = media_body.xpath('.//ul/li/span[contains(@class, "title")]//text()').extract()
			contexts = media_body.xpath('.//ul/li/span[@class="context"]//text()').extract()

			if "Beroep" in title:
				item["beroep"] = contexts[title.index("Beroep")]
			if "Specialisme" in title:
				item["specialisme"] = contexts[title.index("Specialisme")]
			if "Zorginstelling" in title:				
				item["zorginstelling"]  = contexts[title.index("Zorginstelling")]

			yield item


		# find next page
		next_page = selector.xpath('//ul[@class="pagination"]/li[@class="active"]/following-sibling::li[1]/a/@href').extract()
		if len(next_page) > 0:
			yield Request("https://www.zorgkaartnederland.nl" + next_page[0], callback=self.parseItem)


class EtsySpider(Spider):
	name = "etsy"
	allowed_domains = ["www.etsy.com/", "www.etsy.com", "etsy.com"]
	start_urls = ["https://www.etsy.com/search/shops"]

	def callnext(self, response):
		meta = response.request.meta

		if len(meta["callstack"]) > 0:
			target = meta["callstack"].pop()
			yield Request(target['url'], meta = meta, callback=target['callback'])
		else:
			yield meta["item"]

	def parse(self, response):
		selector = Selector(response=response)

		list_shops = selector.xpath('//div[@id="shop-search"]/div[@class="shop"]/div[contains(@class, "shop-info")]')
		for shop in list_shops:
			item = EtsyItem()

			item["etsyUrl"] = (shop.xpath('.//div[@class="shop-details"]/span/a/@href').extract())[0]
			item["shopOwner"] = (shop.xpath('.//div[@class="shop-owner"]/div[@class="real-name"]/a/text()').extract())[0].strip()
			
			yield Request(item["etsyUrl"], meta={"item": item}, callback=self.parseItem)

		# find next page
		next_page = selector.xpath('//ul[@class="pages"]/li[contains(@class, "active")]/following-sibling::li[1]/a/@href').extract()
		if len(next_page) > 0:
			yield Request(next_page[0], callback=self.parse)
				
	def parseItem(self, response):
		item = response.meta["item"]

		selector = Selector(response=response)

		# scraping shop info
		shop_info = selector.xpath('//div[@id="shop-info"]')
		
		shopName = shop_info.xpath('.//li[@class="shopname"]/a/text()').extract()
		if len(shopName) > 0:
			item["shopName"] = shopName[0].strip()
		joinDate = shop_info.xpath('.//li[@class="shopname"]/div[@class="join-date"]/text()').extract()
		if len(joinDate) > 0:
			item["joinDate"] = parser.parse(joinDate[0], fuzzy=True)

		review_rating = shop_info.xpath('.//li[@class="reviews"]/a/span[@class="review-rating"]')
		ratingScore = review_rating.xpath('.//meta[@itemprop="rating"]/@content').extract()
		if len(ratingScore) > 0:
			item["ratingScore"] = ratingScore[0].strip()
		ratingCount = review_rating.xpath('.//meta[@itemprop="count"]/@content').extract()
		if len(ratingCount) > 0:
			item["ratingCount"] = ratingCount[0].strip()

		sales = shop_info.xpath('.//li[contains(@class, "sales")]/a/text()').extract()
		if len(sales) > 0:
			# a little bit lazy code
			item["sales"] = sales[0].replace("sales", "").strip()


		# scraping shop location
		location = selector.xpath('//div[@class="location"]//text()').extract()
		if len(location) > 0:
			item["location"] = location[0].strip()


		# scraping categories
		item["categories"] = []
		categories = selector.xpath('//div[@id="shop-sections"]/ul/li[position()>1]/a/text()').extract()
		for cat in categories:
			if cat.strip() != "":
				item["categories"].append(cat.strip())

		# 
		callstack = []

		# scraping about page
		aboutUrl = shop_info.xpath('.//li[@class="about"]/a/@href').extract()
		if len(aboutUrl) > 0:
			callstack.append({'url': "https://www.etsy.com" + aboutUrl[0], 'callback': self.parseAboutPage})

		
		response.request.meta["item"] = item
		response.request.meta["callstack"] = callstack
		return self.callnext(response)

	def parseAboutPage(self, response):
		item = response.meta['item']

		selector = Selector(response=response)

		item["links"] = []
		related_links = selector.xpath('//div[@class="related-links"]/ul/li/a')
		for link in related_links:
			url = (link.xpath('.//@href').extract())[0]
			title = (link.xpath('.//text()').extract())[0].strip()

			item["links"].append({"url":url, "title":title})

		return self.callnext(response)

