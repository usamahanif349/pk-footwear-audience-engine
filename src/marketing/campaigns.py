"""
Smart suggestions: ready-to-run campaign ideas built from the engine's findings.

Each suggestion is a rule: it appears when the data in view meets its condition, and it
quotes the number that triggered it. The copy is SAMPLE copy written for a class project
(no paid AI service), in English and Roman Urdu. {brand}, {city} and {creator} are filled in.
"""

SUGGESTIONS = [
    dict(
        id="answer24", area="Customer service", title="Answer every buyer within 24 hours",
        why="{unanswered} buying questions are still waiting. Only {answered} of {brand_q} on your own posts got a reply.",
        lever="Turns comments you already have into orders. No ad spend.",
        copy_en="Thanks for asking! It's Rs. {price}, available online at {link} and in our {city} stores. Want us to check your size?",
        copy_ru="Shukriya! Qeemat Rs. {price} hai, online {link} par aur {city} ke stores mein available hai. Apna size batayein?",
        p2_angle=None, needs=("unanswered",)),
    dict(
        id="creators", area="Content", title="Partner with the creators your buyers already watch",
        why="{creator_q} buying questions appeared under creator videos. Top lead: {creator} ({creator_q_top} buyers asked).",
        lever="Creator posts get {cpk_ratio}x more comments per view than brand posts.",
        copy_en="Pinned by {brand}: prices and sizes are in the description. Order online at {link}, delivery across Pakistan.",
        copy_ru="{brand} ki taraf se: prices aur sizes description mein hain. Online order {link} par, poore Pakistan mein delivery.",
        p2_angle="delivery", needs=("creator_q",)),
    dict(
        id="prices", area="Content", title="Put prices on screen and in titles",
        why="Videos that show prices get {price_drop}% fewer price questions ({price_q} price questions so far).",
        lever="Fewer 'price?' comments, more orders. Test it on the next 5 posts.",
        copy_en="New arrivals from Rs. {price}. Every price on screen, every size in stock. Shop now at {link}.",
        copy_ru="Naye articles sirf Rs. {price} se. Har price screen par, har size stock mein. Abhi order karein: {link}.",
        p2_angle="price", needs=("price_q",)),
    dict(
        id="city", area="Promotions", title="City ads that name the branch: {city} first",
        why="{avail_q} people asked where to buy. {city} is named most ({city_n} times), then {city2}.",
        lever="Location questions are the biggest buying need. Answer them before they are asked.",
        copy_en="{brand} {city}: visit us at your nearest branch or order online at {link}. Same prices, same sizes.",
        copy_ru="{brand} {city} mein: qareebi branch par aayein ya online {link} se order karein. Wohi prices, wohi sizes.",
        p2_angle="staff", needs=("avail_q",)),
    dict(
        id="countdown", area="Promotions", title="Sale countdown posts with the end date",
        why="{deal_people} deal hunters in your audience; {until_q} comments ask when the sale starts or ends.",
        lever="A visible end date creates urgency and stops the 'sale kab tak hai?' comments.",
        copy_en="Flat 50% off ends {end_date}. Online and in stores, while stock lasts. {link}",
        copy_ru="Flat 50% off {end_date} tak. Online aur stores mein, jab tak stock hai. {link}",
        p2_angle="price", needs=("deal_people",)),
    dict(
        id="throwback", area="Campaign test", title="Throwback remake of the classic Servis ad",
        why="{buzz_pct}% of Servis comments are nostalgia and memes about its classic ad, years later.",
        lever="A/B test: throwback remake vs standard product ad, same budget, same audience.",
        copy_en="Servis. Still the shoes you grew up with. The classic is back, with the new collection.",
        copy_ru="Servis. Wohi joote jin ke saath aap baray huay. Classic wapas hai, nayi collection ke saath.",
        p2_angle="design", needs=("servis",)),
    dict(
        id="sizeguide", area="Customer service", title="Publish a size guide (EU / UK / PK)",
        why="{size_people} shoppers asked about size or fit; a wrong size is the most common exchange reason.",
        lever="Fewer returns, more confident online orders.",
        copy_en="Not sure of your size? Check our size guide at {link}. Wrong size? Exchange it free within 7 days.",
        copy_ru="Size ka pata nahi? Size guide {link} par dekhein. Size ghalat ho to 7 din mein free exchange.",
        p2_angle="size", needs=("size_people",)),
    dict(
        id="complaints", area="Customer service", title="Complaint routine: public reply, private fix, 48 hours",
        why="{unhappy} unhappy customers wrote in public (damaged pairs, refunds, late orders).",
        lever="A visible fix turns a public complaint into public proof that you care.",
        copy_en="We're sorry about this. Please send your order number by message; our team will fix it within 48 hours.",
        copy_ru="Hamein afsos hai. Apna order number message karein; hamari team 48 ghante mein masla hal karegi.",
        p2_angle="quality", needs=("unhappy",)),
]
