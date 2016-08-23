from scrapy import Spider
from scrapy.selector import Selector
from scrapy.http import HtmlResponse, Request
import json
from techreview.items import TecSpecsItem

class GsmArenaSpider(Spider):
	name = "phonearena"
	allowed_domains = ["http://www.phonearena.com/", "www.phonearena.com", "phonearena.com"]
	start_urls = ["http://www.phonearena.com/phones/manufacturers"]

	def parse(self, response):		
		selector = Selector(response=response)

		# extract brand on current page
		brands = selector.xpath('//div[@id="brands"]/div[@class="s_listing"]/div[contains(@class, "s_block_4")]/div[@class="s_hover"]')
		for brand in brands:
			brandLink = (brand.xpath('.//a[@class="s_thumb"]/@href').extract())[0]
			brandName = (brand.xpath('(.//a)[2]//text()').extract())[0]

			yield Request("http://www.phonearena.com" + brandLink + "/?filter_class[]=1223", meta={'product': 'Cellphones', 'brand': brandName}, callback=self.parseBrandItems)
			yield Request("http://www.phonearena.com" + brandLink + "/?filter_class[]=1612", meta={'product': 'Tablets','brand': brandName}, callback=self.parseBrandItems)
		
	def parseBrandItems(self, response):
		product = response.meta['product']
		brand = response.meta['brand']

		selector = Selector(response=response)

		phones = selector.xpath('//div[@id="phones"]/div[@class="s_listing"]/div[contains(@class, "s_block_4")]/h3')
		for phone in phones:
			phoneLink = (phone.xpath('.//a[not(*)]/@href').extract())[0]
			phoneName = (phone.xpath('.//a[not(*)]//text()').extract())[0]

			item = TecSpecsItem()
			item["product"] = product
			item["brand"] = brand
			item["name"] = phoneName
			item["source"] = 0

			yield Request("http://www.phonearena.com" + phoneLink, meta={'item': item}, callback=self.parseItemSpecs)


		nextPageLink = selector.xpath('//li[@class="s_next"]/a/@href').extract()
		if len(nextPageLink) > 0:
			yield Request("http://www.phonearena.com" + nextPageLink[0], meta={'product': product, 'brand': brand}, callback=self.parseBrandItems)

	def callnext(self, response):
		meta = response.request.meta

		if len(meta["callstack"]) > 0:
			target = meta["callstack"].pop()
			yield Request("http://www.phonearena.com" + target['url'], meta = meta, callback=target['callback'])
		else:
			yield meta["item"]

	def parseItemSpecs(self, response):
		item = response.meta["item"]
		
		selector = Selector(response=response)


		# get pros and cons
		pros = []
		cons = []

		proscons_node = selector.xpath('//div[@class="proscons"]')
		pros_nodes = proscons_node.xpath('.//ul[@class="s_pros_list"]/li')
		for node in pros_nodes:
			pros.append((node.xpath('.//text()').extract())[0])

		cons_nodes = proscons_node.xpath('.//ul[@class="s_cons_list"]/li')
		for node in cons_nodes:
			cons.append((node.xpath('.//text()').extract())[0])		

		item["pros"] = pros
		item["cons"] = cons

		# get images
		item["images"] = selector.xpath('//div[@class="lcimg"]/a[@class="pics"]/@href').extract()
		item["thumbnail"] = selector.xpath('//div[@class="lcimg"]/a[@class="pics"]/img/@src').extract()

		# get stats
		item["stats"] = selector.xpath('//div[@id="have_it"]/div/a[contains(@class, "number")]//text()').extract()

		# getting urls to parse other information
		phonetabs = selector.xpath('//div[@class="phonetabs"]/div[contains(@class, "s_tabs")]/ul')
		
		sizeUrl = phonetabs.xpath('.//li/a[text()[contains(.,"Size")]]/@href').extract()
		benchmarksUrl = phonetabs.xpath('.//li/a[text()[contains(.,"Benchmarks")]]/@href').extract()
		videosUrl = phonetabs.xpath('.//li/a[text()[contains(.,"Video")]]/@href').extract()

		# building up callstack
		callstack = []
		if len(sizeUrl) > 0 and sizeUrl[0] != "javascript:;":
			callstack.append({'url': sizeUrl[0], 'callback': self.parseItemSize})
		
		if len(benchmarksUrl) > 0 and benchmarksUrl[0] != "javascript:;":
			callstack.append({'url': benchmarksUrl[0], 'callback': self.parseItemBenchmarks})
		
		if len(videosUrl) > 0 and videosUrl[0] != "javascript:;":
			callstack.append({'url': videosUrl[0], 'callback': self.parseItemVideos})

		response.request.meta["item"] = item
		response.request.meta["callstack"] = callstack
		return self.callnext(response)

	def parseItemSize(self, response):
		item = response.meta['item']

		selector = Selector(response=response)

		sz_phone = selector.xpath('//div[@class="standart_view"]/ul[contains(@class, "sizecompare")]/li[@class="sz_phone"]')
		if len(sz_phone) > 0:
			item["size_images"] = sz_phone[0].xpath('.//img/@src').extract()

		return self.callnext(response)

	def parseItemBenchmarks(self, response):
		item = response.meta['item']

		phoneName = "{0} {1}".format(item["brand"], item["name"])
		
		selector = Selector(response=response)
		benchmark_topaccordeon = selector.xpath('//li[a[@class="acc_toggle" and following-sibling::div[contains(@class, "accordeon ")]]]')

		benchmarks = []
		for i in range(len(benchmark_topaccordeon)):
			accordeon = benchmark_topaccordeon[i]
			
			bench = {}
			bench["title"] = (accordeon.xpath('.//a/span[@class="title"]//text()').extract())[0].strip()
			bench["data"] = []

			if i == 0 or i == 1 or i == 4:
				table = accordeon.xpath('.//table[contains(@class, "benchmark_table")]')
				if table:
					tb_header = table.xpath('.//thead/tr/th[descendant::*]')
					
					phones = table.xpath('.//tbody/tr')
					for phone in phones:
						name = (phone.xpath('.//th//text()').extract())[0].strip()
						if name == phoneName:
							tb_benchmark = phone.xpath('.//td[@class="benchmark_tb"]')
					
							for header, benchmark in zip(tb_header, tb_benchmark):
								score = benchmark.xpath('.//strong/text()').extract()
								score_des = benchmark.xpath('.//span/text()').extract()

								title = header.xpath('.//*[self::span[contains(@class,"title")] | self::a[contains(@class,"title")]]/text()').extract()
								title_des = header.xpath('.//span[@class="wichisbetter"]//text()').extract()

								bench["data"].append({"title": title[0].strip() if len(title) > 0 else "", \
											"title_des": title_des[0].strip() if len(title_des) > 0 else "", \
											"score": score[0].strip() if len(score) > 0 else "" , \
											"score_des": score_des[0].strip() if len(score_des) > 0 else ""})
			elif i == 3 or i == 5:
				charts = accordeon.xpath('.//table/tr')
				for chart in charts:
					ch_header = chart.xpath('.//td[1]')
					ch_benchmark = chart.xpath('.//td[2]')

					title = ch_header.xpath('.//div[contains(@class,"name")]/text()').extract()
					title_des = ch_header.xpath('.//span[@class="wichisbetter"]//text()').extract()

					phones = ch_benchmark.xpath('.//div[@class="score"]')
					for phone in phones:
						name = (phone.xpath('.//span[contains(@class, "bar")]//text()').extract())[0].strip()
						if name == phoneName:
							score = (phone.xpath('.//span[contains(@class, "stext")]/text()').extract())
							bench["data"].append({"title": title[0].strip() if len(title) > 0 else "",\
										"title_des": title_des[0].strip() if len(title_des) > 0 else "", \
										"score": score[0].strip() if len(score) > 0 else "", "score_des": ""})
							break
			elif i == 6:
				titles = ["", "Battery Life", "", "Charging Time"]
				tables = accordeon.xpath('.//table')
				for i in range(len(tables)):
					if i == 0 or i == 2:
						continue
					
					table = tables[i]
					tb_benchmark = table.xpath('.//tr')
					for benchmark in tb_benchmark:
						name = (benchmark.xpath('.//div[@class="name"]//text()').extract())[0].strip()
						if name == phoneName:
							score = (benchmark.xpath('.//span[contains(@class, "stext")]/text()').extract())
							score_des = (benchmark.xpath('.//span[contains(@class, "stext")]/span/text()').extract())

							bench["data"].append({"score": score[0].strip() if len(score) > 0 else "", \
												"score_des": score_des[0].strip() if len(score_des) > 0 else "", \
												"title" : titles[i]})
							break



			benchmarks.append(bench)
		
		item["benchmarks"] = benchmarks

		return self.callnext(response)

	def parseItemVideos(self, response):
		item = response.meta['item']
		
		selector = Selector(response=response)
		video_nodes = selector.xpath('//*[@id="yt-thumbs"]/div')

		yt_videos = []
		for node in video_nodes:
			yt_id = node.xpath('.//a[contains(@class, "yt_show")]/@vid').extract()
			title = node.xpath('.//a[contains(@class, "yt_show")]/@title').extract()
			thumbnail = node.xpath('.//img/@src').extract()

			yt_videos.append({'yt_id': yt_id[0] if len(yt_id) > 0 else "", \
							'title': title[0] if len(title) > 0 else "", \
							'thumbnail': thumbnail[0] if len(thumbnail) > 0 else ""})

		item["yt_videos"] = yt_videos

		return self.callnext(response)