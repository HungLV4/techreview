from scrapy import Spider
from scrapy.selector import Selector
from scrapy.http import HtmlResponse, Request

from extruct.w3cmicrodata import MicrodataExtractor

import json
from techreview.items import TechreviewItem

abre_list = [u"released", u"announced", u"discontinued"]

class EngadgetSpider(Spider):
	name = "engadget"
	allowed_domains = ["http://www.engadget.com/", "www.engadget.com", "engadget.com"]

	def start_requests(self):
		# data = json.loads('{"cat":[{"name":"Computers","products":[{"title":"Desktops","url":"desktops"},{"title":"Laptops/Portables","url":"laptops"},{"title":"Operating Systems","url":"os-platforms"}]},{"name":"Mobile","products":[{"title":"Cellphones","url":"cellphones"},{"title":"Tablets","url":"tablets"},{"title":"Bluetooth Headsets","url":"bluetooth-headsets"},{"title":"GPS","url":"gps"}]},{"name":"Photography","products":[{"title":"Cameras","url":"cameras"},{"title":"Camera Lens","url":"camera-lenses"},{"title":"camcorders","url":"camcorders"},{"title":"Digital Picture Frames","url":"digital-photo-frames"}]},{"name":"Gaming","products":[{"title":"Consoles (home)","url":"gaming-consoles-home"},{"title":"Consoles (portable)","url":"gaming-consoles-portable"},{"title":"Controllers / Gamepads","url":"controllers/"},{"title":"Joysticks /Flight / Racing","url":"joysticks-flight-racing/"}]},{"name":"Peripherals","products":[{"title":"Keyboards","url":"keyboards"},{"title":"Mice","url":"mice"},{"title":"Monitors","url":"monitors"},{"title":"Computer Speakers","url":"computer-speakers"},{"title":"Headsets","url":"headsets"},{"title":"Printers","url":"printers"},{"title":"Scanners","url":"scanners"},{"title":"Pen Tablets","url":"pen-tablets"},{"title":"USB/Firewire Hubs","url":"usb-firewire-hubs/"},{"title":"Webcams","url":"webcams"}]},{"name":"Personal Tech","products":[{"title":"Headphones","url":"headphones"},{"title":"Portable Media Players","url":"portable-media-players"},{"title":"E-book Readers","url":"e-book-readers"},{"title":"Fitness","url":"fitness"},{"title":"Misc devices","url":"misc"}]},{"name":"Networking","products":[{"title":"Routers","url":"routers"},{"title":"Switches/Hubs","url":"switches-hubs"}]},{"name":"Storage","products":[{"title":"External Hard Drives","url":"external-drives"},{"title":"Flash Drives","url":"flash-drives"},{"title":"Memory Cards","url":"memory-cards"},{"title":"Network Storage","url":"network-storage"},{"title":"RAID/Drive Arrays","url":"raid-arrays"}]},{"name":"Home Theater","products":[{"title":"HDTVs/Televisions","url":"hdtvs-televisions"},{"title":"Speaker Docks","url":"speaker-docks"},{"title":"Digital Media Players","url":"digital-media-players"},{"title":"Remotes/Controllers","url":"remotes"},{"title":"A/V Receivers","url":"av-receivers"},{"title":"DVRs","url":"dvrs"},{"title":"Speakers","url":"speakers"},{"title":"Video Disc Players","url":"video-disc-players"}]}]}')
		data = json.loads('{"cat":[{"name":"Mobile","products":[{"title":"Cellphones","url":"cellphones"},{"title":"Tablets","url":"tablets"}]}]}')

		for cat in data['cat']:
			for product in cat['products']:
				yield Request("http://www.engadget.com/reviews/" + product['url'], meta={'product': product['title']}, callback=self.parse)

	def parse(self, response):	
		selector = Selector(response=response)
		extractor = MicrodataExtractor()
		items = extractor.extract(response.body_as_unicode(), response.url)
		print items

		# extract items on current page
		# nodes = selector.xpath('//ul[@class="product-grid"]/li')
		# for node in nodes:
		# 	brand = node.xpath('.//span[@class="company"]/text()').extract()
		# 	name = node.xpath('.//span[@class="model"]/text()').extract()
		# 	product = response.meta['product']
		# 	score = node.xpath('.//span[contains(@class, "engadget-score")]//text()').extract()
		# 	released = node.xpath('.//span[@class="product-released"]//text()').extract()
		# 	link = node.xpath('.//a[@class="product-name"]/@href').extract()
		# 	thumbnail = node.xpath('.//a[contains(@class, "product-image")]/img/@data-src').extract()

		# 	item = TechreviewItem()
		# 	if len(brand) > 0:
		# 		item["brand"] = brand[0].strip()
		# 	if len(name) > 0:
		# 		item["name"] = name[0].strip() 
		# 	item["product"] = response.meta['product']
			
		# 	if len(score) > 0:
		# 		item["score"] = score[0].strip()
		# 	item["source"] = 2
			
		# 	if len(thumbnail) > 0:
		# 		item["thumbnail"] = thumbnail[0].strip()

		# 	if len(released) > 0:
		# 		item["released"] = released[0].strip()
		# 		for abre in abre_list:
		# 			item["released"] = item["released"].replace(abre, "")
				
		# 		item["released"] = item["released"].strip()
			

		# 	yield Request(link[0], meta = {'item' : item}, callback=self.parseItem)

		# finding nextpage
		# nextPage = selector.xpath('//a[@class="next"]/@href').extract()
		# if len(nextPage) > 0:
		# 	yield Request(nextPage[0], meta={'product': response.meta['product']}, \
		# 					callback=self.parse)
		
	def parseItem(self, response):
		item = response.meta["item"]

		selector = Selector(response=response)

		# get image
		imgUrl = selector.xpath('//div[@data-swiftype-name="image"]//text()').extract()
		if len(imgUrl) > 0:
			item["images"] = imgUrl[0].strip()

		# get headline
		headline = selector.xpath('//div[contains(@class,"headline")]/*[self::h1 or self::h2]//text()').extract()
		if len(headline) > 0:
			item["headline"] = headline[0].strip()


		# get popularity
		item["stats"] = selector.xpath('//ul[@class="ownership"]/li[@class="list"]/span/p[@class="number"]//text()').extract()

		# get critical scores
		criticScores = {}
		crit_score_element = selector.xpath('//section[@id="critic-reviews-graph"]')
		
		crit_rev_overall_score = ""
		crit_rev_overall_score_element = crit_score_element.xpath\
			('.//div[@class="product-overall-rating"]/div[contains(@class, "rating")]//text()').extract()
		if len(crit_rev_overall_score_element) > 0:
			crit_rev_overall_score = crit_rev_overall_score_element[0].strip()

		crit_rev_criteria_scores = []
		crit_rev_criteria_elements = crit_score_element.xpath('.//ul[@class="product-criteria-bars"]/li')
		for crit_rev_criteria_element in crit_rev_criteria_elements:
			label = crit_rev_criteria_element.xpath('.//div[@class="product-criteria-label"]/text()').extract()
			score = crit_rev_criteria_element.xpath('.//div[contains(@class, "rating")]/text()').extract()
			if len(label) > 0 and len(score) > 0:
				crit_rev_criteria_scores.append({"label" : label[0].strip(), "score" :score[0].strip()})

		criticScores["overall_score"] = crit_rev_overall_score
		criticScores['criteria_scores'] = crit_rev_criteria_scores

		item["criticScores"] = criticScores

		# get user scores
		usrScores = {}
		usr_rev_element = selector.xpath('//section[@id="user-reviews-graph"]')
		
		usr_rev_overall_score = ""
		usr_rev_overall_score_element = usr_rev_element.xpath\
			('.//div[@class="product-overall-rating"]/div[contains(@class, "rating")]//text()').extract()
		if len(usr_rev_overall_score_element) > 0:
			usr_rev_overall_score = usr_rev_overall_score_element[0].strip()

		usr_rev_criteria_scores = []
		usr_rev_criteria_elements = usr_rev_element.xpath('.//ul[@class="product-criteria-bars"]/li')
		for usr_rev_criteria_element in usr_rev_criteria_elements:
			label = usr_rev_criteria_element.xpath('.//div[@class="product-criteria-label"]/text()').extract()
			score = usr_rev_criteria_element.xpath('.//div[contains(@class, "rating")]/text()').extract()
			if len(label) > 0 and len(score) > 0:
				usr_rev_criteria_scores.append({"label" : label[0].strip(), "score" :score[0].strip()})

		usrScores["overall_score"] = usr_rev_overall_score
		usrScores['criteria_scores'] = usr_rev_criteria_scores

		item["userScores"] = usrScores

		# get critical reviews
		criticReviews = []
		crit_rev_elements = selector.xpath('//section[@id="critic-reviews-stream"]/article')
		for crit_rev_element in crit_rev_elements:
			score = crit_rev_element.xpath('.//div[contains(@class, "rating")]//text()').extract()
			source = crit_rev_element.xpath('.//div[@class="product-review-content"]/header/a//text()').extract()
			details = crit_rev_element.xpath('.//div[@class="product-review-content"]/p[@class="product-review-details"]//text()').extract()
			sourceUrl = crit_rev_element.xpath('.//div[@class="product-review-content"]/a/@href').extract()

			if len(score) > 0 and len(source) > 0 and len(details) > 0 and len(sourceUrl) > 0:
				criticReviews.append({"score": score[0].strip(),\
										"source": source[0].strip(), \
										"details" : details[0].strip(), \
										"sourceUrl": sourceUrl[0].strip()})

		item["criticReviews"] = criticReviews

		# get user reviews
		usrReviews = []
		usr_rev_elements = selector.xpath('//section[@id="user-reviews-stream"]/article')
		for usr_rev_element in usr_rev_elements:
			score = usr_rev_element.xpath('.//div[contains(@class, "rating")]//text()').extract()
			name = usr_rev_element.xpath('.//div[@class="product-review-content"]/header/a//text()').extract()
			details = usr_rev_element.xpath('.//div[@class="product-review-content"]/p[@class="product-review-details"]//text()').extract()

			if len(score) > 0 and len(name) > 0 and len(details) > 0 > 0:
				usrReviews.append({"score": score[0].strip(),\
									"name": name[0].strip(), \
									"details" : details[0].strip()})

		item["userReviews"] = usrReviews


		# return item
		yield item