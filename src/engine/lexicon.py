"""
Audience-need lexicon for Pakistani footwear comments (English, Roman Urdu, Urdu).

Each need has regular expressions. A comment can match several needs; the first
match in NEED_ORDER becomes its main need. Roman Urdu has no fixed spelling, so
patterns cover common variants (kitne / kitny / kitnay, kahan / kaha / kidhar ...).
"""
import re

NEED_PATTERNS = {
    # post-purchase problems come first: they matter most to the brand
    "complaint": [
        r"\b(worst|fraud|scam|cheat|fake|ghatiya|bakwas|bekar|bekaar|kharab|ghtia|ghatia|bura|buri)\b",
        r"\b(refund|return policy|exchange nahi|exchange nhi|paise wapas|paisay wapas|complain\w*)\b",
        r"\b(toot|tut|phat|fat) (gaya|gya|gayi|gyi|gye)\b", r"\b(still waiting|not received|nahi mila|nhi mila|no reply|reply nhi|reply nahi)\b",
        r"\b(order|ordered).{0,40}\b(days|din|weeks?)\b", r"\bpehli dafa\b.*\b(gir|toot|tut)",
        r"قیمت زیادہ|خراب|بیکار",
    ],
    "price": [
        r"\b(price|prices|pric|prise|qeemat|qimat|keemat|kimat|rate|rates|cost)\b",
        r"\bkitn[eaiy]\w* (ki|ka|ke|k)\b", r"\bkitn[eaiy]\w* (rs|rupe|rupay|rupees|ka hai|ki hai)\b",
        r"\bhow much\b", r"\b(rs\.?|pkr)\s?\d", r"\b\d{3,5}\s?(rs|pkr|rupees|rupay)\b",
        r"\b(mehnga|mehenga|mehngi|mehengi|expensive|sasta|sasti|cheap price|affordable|budget)\b",
        r"قیمت|پرائس|کتنے کی|کتنے کا",
    ],
    "availability": [
        r"\b(available|availible|avail|in stock|stock|out of stock|restock)\b",
        r"\b(location|address|adress|adreass|branch|branches|outlet|store|shop) ?(\?|plz|please|pls|send|batain|bta|kahan|kaha|kidhar|where|in)?",
        r"\b(kahan|kaha|kidhar|kidr|kha|where) (se|sy|say|milega|milegi|mile|milay|hai|ha|hy|hay|is|can|to)\b",
        r"\b(ye|yeh|yah|ya) (kahan|kaha|kha|kidhar) (hai|ha|hy|hay|he)\b", r"\bwhich (area|city|branch|mall)\b",
        r"\b(mil|mill?)(ega|egi|ygi|yga|ta|ti|e|ay|y) ?(ga|gi)?\b.*\b(karachi|lahore|islamabad|pindi|rawalpindi|multan|faisalabad|peshawar|quetta|hyderabad|sialkot|gujranwala)\b",
        r"\b(karachi|lahore|islamabad|pindi|rawalpindi|multan|faisalabad|peshawar|quetta|hyderabad|sialkot|gujranwala)\b.*\b(hai|ha|hy|branch|outlet|store|available|mil)\b",
        r"\b(is this|ye|yeh|this) .{0,20}(available|milega|milegi|mil jaye)\b",
        r"لوکیشن|ایڈریس|کہاں",
    ],
    "delivery_order": [
        r"\b(deliver\w*|courier|parcel|tracking|shipping|ship to|cod|cash on delivery)\b",
        r"\b(order|ordr|odr|oder) ?(kaise|kese|kaisay|kesy|kesekren|kis|kahan|kr|kar|krna|karna|krny|karne|krne|place|how|online)\w*",
        r"\b(how (to|can i|do i) (order|buy|purchase))\b", r"\b(online (order|buy|purchase|milega|milegi|mil|available))\b",
        r"\b(kaise|kese|kesy|kaisay) (mangwa|mangwain|order|khareed|le|lein|mil)\w*",
        r"\b(abroad|uk|usa|dubai|saudi|canada) .{0,15}(deliver|ship|order|mil)",
    ],
    "contact": [
        r"\b(whatsapp|whats app|watsapp|wtsp|contact|cntct)\b",
        r"\b(number|nmbr|no\.?|website|web site|page|link)\b.{0,12}(\?|plz|please|pls|send|do|dein|dain|den|share|kia|kya|btain|batain|bta|braden|bata)",
        r"\b(send|share|give) (me )?(your )?(number|link|details|detail|contact)\b", r"\bdetails? (plz|please|pls|send|dein|dain|chahiye)\b",
        r"\b(inbox|dm) (me|kar|kr|karo|plz|please|details)\b",
    ],
    "size_fit": [
        r"\b(size|sizes|saiz|sz|fit|fitting|tight|loose|narrow|wide|width|chota|chhota|bara|bada)\b",
        r"\b(uk|eu)? ?\b(3[5-9]|4[0-6])\b ?(size|number|no)\b", r"\b(\d{1,2}) (number|no) (ka|ki|k|ke)\b",
        r"سائز",
    ],
    "discount_sale": [
        r"\b(sale|sell?al|discount|discounts|off|% ?off|offer|deal|deals|clearance|promo|voucher|code|flat \d+|11\.11|black friday|white friday)\b",
        r"\bkab (tak|tk) .{0,15}(sale|offer|discount)\b", r"\b(sale|offer) .{0,15}(kab|kb) (tak|tk)\b", r"\bkb tk\b",
        r"سیل|ڈسکاؤنٹ",
    ],
    "quality_comfort": [
        r"\b(quality|qualty|comfort\w*|soft|durable|durability|long lasting|leather|sole|stitch\w*|material|grip|heel|cushion\w*|pain|painful|dard|aram|aaram|araam)\b",
        r"\b(pakka|pakki|mazboot|majboot|chalti|chalta|chal (rahi|rahe|raha))\b",
        r"\b(experience|tajurba|wear(ing)? (them|it|these)|paon|paoon|pair) .{0,30}\b(achha|acha|achi|good|bad|kharab|khaas|comfortable|hurt|dard)\b",
        r"کوالٹی|آرام",
    ],
    "nostalgia_ad": [
        r"\b(ad|ads|advert\w*|commercial|tvc|jingle|song|tune)\b",
        r"\b(19[89]\d|20[01]\d|2020|2021|2022|2023|2024|2025|2026)\b.{0,25}\b(watch\w*|here|anyone|who)\b",
        r"\b(anyone|who).{0,20}\b(watching|here)\b", r"\b(childhood|bachpan|nostalg\w*|memories|old days|purana|purani)\b",
        r"\b(aliz\w* shah|alizey|alizeh|kanwal|kawal|usman|adnan)\b",
    ],
    "praise_product": [
        r"\b(beautiful|nice|lovely|pretty|gorgeous|stunning|elegant|classy|stylish|decent|cute|amazing|awesome|fantastic|superb|perfect|great|best|love|loved|like|liked|wow|wao|waoo\w*|zabardast|zbrdst|zaberdast|zabardust|khubsurat|khoobsurat|pyar\w*|piyar\w*|pyari|piyari|kamal|lajawab|behtreen|behtareen)\b.{0,30}\b(shoe|shoes|joota|joote|jooty|juta|jutay|sandal\w*|chappal\w*|heel\w*|collection|design\w*|pair|boot\w*|sneaker\w*|slipper\w*|khussa|article|colou?r|style)\b",
        r"\b(shoe|shoes|joota|joote|jooty|sandal\w*|chappal\w*|heel\w*|collection|design\w*|boot\w*|sneaker\w*|article)\b.{0,25}\b(beautiful|nice|lovely|pretty|amazing|awesome|zabardast|zbrdst|khubsurat|pyar\w*|pyari|kamal|best|great|good|achi|achay|ache)\b",
        r"\b(want|need|chahiye|chahye|lena|leni|lyna|lyni|khareed\w*|buy|order kr|order kar)\b.{0,20}\b(this|ye|yeh|it|is|wala|wali|shoe|shoes|pair|ek)\b",
    ],
    "praise_content": [
        r"\b(nice|good|great|amazing|beautiful|lovely|wonderful|zabardast|zbrdst|best|very nice|helpful|informative)\b.{0,15}\b(video|vlog|sharing|share|content|editing|information|info|review|work|upload)\b",
        r"\b(thanks|thank you|thanku|thank u|shukriya|jazak\w*) for (sharing|the video|this video|info\w*)\b", r"\bkeep it up\b", r"\bnew (friend|subscriber)\b", r"\bstay connected\b",
        r"\b(like|liked|subscribe\w*|sub) (done|kar diya|kr dia|kr diya)\b",
    ],
}
NEED_ORDER = ["complaint", "price", "availability", "delivery_order", "contact", "size_fit",
              "discount_sale", "quality_comfort", "nostalgia_ad", "praise_product", "praise_content"]
NEED_LABEL = {
    "complaint": "Complaint / problem", "price": "Price inquiry", "availability": "Availability / location",
    "delivery_order": "Delivery / how to order", "contact": "Contact / link request", "size_fit": "Size / fit",
    "discount_sale": "Discount / sale", "quality_comfort": "Quality / comfort", "nostalgia_ad": "Ad nostalgia / celebrity buzz",
    "praise_product": "Product praise / wants it", "praise_content": "Praise for the video",
    "general_praise": "General praise / blessing", "other": "Other / off-topic",
}
HIGH_INTENT = {"price", "availability", "delivery_order", "contact", "size_fit"}
MEDIUM_INTENT = {"discount_sale", "quality_comfort", "praise_product"}

GENERAL_PRAISE = re.compile(
    r"^\W*(very |so |too |bohat |bht |boht )?(nice|good|great|wow+|wao+\w*|beautiful|lovely|amazing|awesome|superb|zabardast|zbrdst|"
    r"zaberdast|mashallah|masha ?allah|mashaallah|ma sha allah|subhan ?allah|ameen|ameeen\w*|nyc|gud|osm|excellent|cool|cute|"
    r"perfect|fantastic|outstanding|marvelous|best|love it|loved it|like it|thanks?( you| u)?|thank you|thanku|shukriya|walaikum|"
    r"wa ?alaikum|assalam\w*|salam)\b", re.I)
QUESTION = re.compile(r"\?|\b(kya|kia|kitn\w+|kahan|kaha|kidhar|kab|kb|kon|kaun|konsa|konsi|kis|kese|kaise|kesy|"
                      r"how|where|what|when|which|can i|is it|is this|do you|does)\b|کیا|کتنے|کہاں|کب", re.I)

_COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in NEED_PATTERNS.items()}


def needs_of(text):
    """All needs a comment mentions, in priority order."""
    t = str(text)
    return [k for k in NEED_ORDER if any(p.search(t) for p in _COMPILED[k])]


def is_question(text):
    return bool(QUESTION.search(str(text)))


def is_general_praise(text):
    return bool(GENERAL_PRAISE.search(str(text)))
