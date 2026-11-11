"""
Reply assistant: ready-to-paste replies for each audience need, in English and Roman Urdu.

Template based (no paid AI service), so it always works. {brand} and {link} are filled
in by the dashboard. The replies are SAMPLE wording written for a class project, not
the brands' real customer-service scripts.
"""

REPLIES = {
    "price": dict(
        en="Hi! This article is Rs. {price}. You can see all prices and sizes here: {link}. Want us to check your size?",
        ru="Assalam o Alaikum! Is article ki qeemat Rs. {price} hai. Saari prices aur sizes yahan dekhein: {link}. Apna size batayein, hum check kar dete hain."),
    "availability": dict(
        en="Hi! It's available online at {link} and in our stores. Tell us your city and we'll share the nearest branch.",
        ru="Assalam o Alaikum! Ye online {link} par aur hamare stores mein available hai. Apna shehar batayein, hum qareebi branch bata dete hain."),
    "delivery_order": dict(
        en="Hi! You can order at {link} with cash on delivery. Delivery usually takes 3–5 working days across Pakistan.",
        ru="Assalam o Alaikum! Aap {link} par order kar sakte hain, cash on delivery ke saath. Delivery aam tor par 3–5 din mein poore Pakistan mein."),
    "contact": dict(
        en="Hi! For quick help, message us on WhatsApp or order directly at {link}. We reply within working hours.",
        ru="Assalam o Alaikum! Jaldi madad ke liye WhatsApp par message karein ya seedha {link} par order karein."),
    "size_fit": dict(
        en="Hi! Please check our size guide at {link}. If the size isn't right, you can exchange it easily.",
        ru="Assalam o Alaikum! Size guide {link} par dekhein. Size sahi na ho to aasaan exchange hai."),
    "discount_sale": dict(
        en="Hi! The sale runs until {end_date} online and in stores, while stock lasts. Shop at {link}.",
        ru="Assalam o Alaikum! Sale {end_date} tak online aur stores mein hai, jab tak stock hai. {link} par shop karein."),
    "quality_comfort": dict(
        en="Thank you for asking! Every pair is checked before it ships, and our soles are made for all-day wear. Details: {link}",
        ru="Shukriya! Har joota bhejne se pehle check hota hai, aur sole saare din ke aaram ke liye bana hai. Details: {link}"),
    "complaint": dict(
        en="We're sorry about this. Please send your order number by message so our team can fix it today.",
        ru="Hamein afsos hai. Apna order number message mein bhejein, hamari team aaj hi masla hal karegi."),
    "praise_product": dict(
        en="Thank you so much! 💙 Grab yours at {link} before your size sells out.",
        ru="Bohat shukriya! 💙 Apna size khatam hone se pehle {link} se order karein."),
    "nostalgia_ad": dict(
        en="We love that you still remember this one! 😄 Which classic {brand} ad should we bring back?",
        ru="Shukriya ke aap ko ye ad ab bhi yaad hai! 😄 {brand} ka konsa purana ad wapas laayein?"),
}
