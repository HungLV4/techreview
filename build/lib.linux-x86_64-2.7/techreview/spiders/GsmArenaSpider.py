from scrapy import Spider
from scrapy.selector import Selector
from scrapy.http import HtmlResponse, Request
import json
from techreview.items import TecSpecsItem

class GsmArenaSpider(Spider):
	name = "gsmarena"
	allowed_domains = ["http://www.gsmarena.com/", "www.gsmarena.com", "gsmarena.com"]
	start_urls = ["http://www.gsmarena.com/makers.php3"]

	def parse(self, response):		
		selector = Selector(response=response)

		# extract brand on current page
		brands = selector.xpath('//div[@class="st-text"]/table/tr/td[descendant::img]')
		for brand in brands:
			brandLink = (brand.xpath('.//a/@href').extract())[0]
			brandName = (brand.xpath('.//img/@alt').extract())[0]

			yield Request("http://www.gsmarena.com/" + brandLink, meta={'brand': brandName}, callback=self.parseBrandItems)
		
	def parseBrandItems(self, response):
		phoneBrand = response.meta['brand']

		selector = Selector(response=response)

		phones = selector.xpath('//div[@id="review-body"]/div[@class="makers"]/ul/li')
		for phone in phones:
			phoneLink = (phone.xpath('.//a/@href').extract())[0]
			phoneName = (phone.xpath('.//span//text()').extract())[0]

			yield Request("http://www.gsmarena.com/" + phoneLink, meta={'brand': phoneBrand, 'name': phoneName}, callback=self.parseItem)


		nextPageLink = selector.xpath('//a[@class="pages-next"]/@href').extract()
		if len(nextPageLink) > 0:
			yield Request("http://www.gsmarena.com/" + nextPageLink[0], meta={'brand': phoneBrand}, callback=self.parseBrandItems)


	def parseItem(self, response):
		item = TecSpecsItem()

		item["brand"] = response.meta['brand']
		item["name"] = response.meta['name']
		item["source"] = 1
		
		selector = Selector(response=response)

		# get stats
		item["stats"] = selector.xpath('//a[@class="specs-fans"]/strong/text()').extract()

		# get specs
		specs = []

		specs_group_nodes = selector.xpath('//div[@id="specs-list"]/table')
		for group in specs_group_nodes:
			group_name = ""
			group_specs = []
			
			specs_nodes = group.xpath('.//tr')
			for i in range(len(specs_nodes)):
				node = specs_nodes[i]
				
				if i == 0:
					group_name =  (node.xpath('.//th//text()').extract())[0]

				ttl = (node.xpath('.//td[@class="ttl"]//text()').extract())
				nfo = (node.xpath('.//td[@class="nfo"]//text()').extract())

				if len(ttl) > 0 and len(nfo) > 0:
					group_specs.append({"title": ttl[0], "info": nfo[0]})

			specs.append({"group_name": group_name, "group_specs": group_specs})

		item["specs"] = specs

		# return item
		yield item