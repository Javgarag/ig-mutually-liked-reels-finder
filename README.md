# Instagram Mutually Liked Reels Finder
This Python script interacts with the Instagram blok API in a way that allows the automation of userdata recollection, such as likes. More a proof-of-concept than anything else.

Due to Instagram's 200 requests per hour rate limit, `sleep` statements of 19 seconds each are used to prevent request blocking.

# Setup
Create a `credentials.txt` file with your Instagram credentials (password) and add your username inside `handlers/webdriver.py`'s `login()` method.

Alternatively, use your browser with your logged-in account and extract Instagram's cookies, then input accordingly in `handlers/webdriver.py`'s `inject_cookies()`. 

# Blok and API Reference
## API AppIds
**com.instagram.privacy.activity_center.liked_media_screen**: Accessed once during load of the https://www.instagram.com/your_activity/interactions/likes/ page. Provides the initial cursor for future requests and the most recent 15 user interactions.

**com.instagram.privacy.activity_center.liked_next**: Accessed every couple of scroll ticks inside the HTML flexbox containing the reel squares. Returns the next 15 reels provided a cursor so Instagram knows what to return, while also providing an *AsyncActionWithDataManifest* for the next request of the same type.
## Bloks
**AsyncActionWithDataManifest**: Data structure which serves as a POST request for the browser and as a source for us, as it provides all required parameters for the next request.
