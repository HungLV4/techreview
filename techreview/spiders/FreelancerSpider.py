from scrapy import Spider
from scrapy.selector import Selector
from scrapy.http import HtmlResponse, Request
from techreview.items import ZorgkaartrItem, EtsyItem, TripAdRevItem
from dateutil import parser

class TripAdRevSpider(Spider):
	name = "tripad"
	allowed_domains = ["www.tripadvisor.com/", "www.tripadvisor.com", "tripadvisor.com"]

	def callnext(self, response):
		meta = response.request.meta

		if len(meta["callstack"]) > 0:
			target = meta["callstack"].pop()
			yield Request(target['url'], meta = meta, callback=target['callback'])
		else:
			yield meta["item"]

	def start_requests(self):
		data = json.loads('{"attractions" : [{"name": "Cadillac Mountain", "url": "http://www.tripadvisor.com/Attraction_Review-g143010-d108269-Reviews-Cadillac_Mountain-Acadia_National_Park_Mount_Desert_Island_Maine.html#REVIEWS"}]}')

		for attraction in data['attractions']:
			item = TripAdRevItem()
			item["attractionName"] = attraction["name"]
			item["attractionUrl"] = attraction["url"]
			item["reviews"] = []

			yield Request(attraction["url"], meta={'item': item}, callback=self.parse)

	def parse(self, response):
		selector = Selector(response=response)

		meta = response.meta
		item = meta['item']

		# find all reviews
		reviews_list = selector.xpath('//div[@id="REVIEWS"]/div[contains(@class, "reviewSelector")]')
		for review_node in reviews_list:
			review = {}

			quote = review_node.xpath('.//div[@class="quote"]/a/span/text()').extract()
			if len(quote) > 0:
				review["quote"] = quote[0].strip()

			rate = review_node.xpath('.//div[contains(@class, "rating")]/span[contains(@class, "rate")]/img/@alt').extract()
			if len(rate) > 0:
				review["rate"] = rate[0].strip()

			ratingDate = review_node.xpath('.//div[contains(@class, "rating")]/span[contains(@class, "ratingDate")]/@title').extract()
			if len(ratingDate) > 0:
				review["ratingDate"] = ratingDate[0].strip()

			entry = review_node.xpath('.//div[@class="entry"]/p/text()').extract()
			if len(entry) > 0:
				review["entry"] = entry[0].strip()

			recommend = review_node.xpath('.//div[@class="rating-list"]/div[@class="recommend"]/span/text()').extract()
			if len(recommend) > 0:
				review["recommend"] = recommend[0].strip()


			(item["reviews"]).append(review)


		#find next page
		next_page = selector.xpath('//div[@class="pageNumbers"]/span[contains(@class, "pageNum current")]/following-sibling::a[1]/@href').extract()
		if len(next_page) > 0:
			yield Request(next_page[0], meta=meta, callback=self.parse)
		else:
			yield item


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

