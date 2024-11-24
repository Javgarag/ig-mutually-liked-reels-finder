import json, requests, time
import handlers.webdriver as instagramWeb
import igbloks.scripts.parser as bloksParser
from seleniumwire.utils import decode as sw_decode

def extract_media_ids(entry, media_ids=None):
    if media_ids == None:
        media_ids = {}

    if isinstance(entry, list):
        if entry[0] == "bk.action.map.Make":
            keys = entry[1]
            values = entry[2]
            for i in range(len(keys)):
                if keys[i] == "media_id":
                    media_ids[values[i]] = values[i+1]
                else:
                    extract_media_ids(values[i], media_ids)
        elif entry[0] == "bk.action.array.Make":
            for e in entry[1:]:
                extract_media_ids(e, media_ids)
        else:
            for e in entry:
                extract_media_ids(e, media_ids)
    return media_ids

def make_request(method, url, headers, params={}, data={}):
    """In order for a request to succesfully 200, it needs headers, form data and POST parameters."""
    if method == "POST":
        r = requests.post(url, headers=headers, params=params, data=data)
    elif method == "GET":
        r = requests.get(url, headers=headers)

    r_decoded = sw_decode(r.content, r.headers.get("Content-Encoding", "identity")).decode("utf8")
    if r_decoded.startswith('for (;;);'): # Instagram returns a JSON disguised as JS.
        r_decoded = r_decoded[len('for (;;);'):]

    return json.loads(r_decoded)

instagramWeb.login(use_cookies=True)
headers, params, data = instagramWeb.get_request_info()

# liked_media's on_bind, around line 1234, contains the first few, most recent, 15 interactions. It's the only exception to the chain.
liked_media = make_request(
    "POST",
    "https://www.instagram.com/async/wbloks/fetch/",
    headers, 
    {
        "appid" : "com.instagram.privacy.activity_center.liked_media_screen",
        "type" : "action",
        "__bkv" : params["__bkv"]
    },
    data
)
action_liked_media = bloksParser.deserialize(liked_media["payload"]["layout"]["bloks_payload"]["tree"]["bk.components.screen.Wrapper"]["content"]["bk.components.Flexbox"]["children"][2]["bk.components.Flexbox"]["children"][0]["bk.components.Flexbox"]["children"][0]["bk.components.Collection"]["children"][0]["bk.components.Flexbox"]["_style"]["collection"]["on_appear"])
on_bind_liked_media = bloksParser.deserialize(liked_media["payload"]["layout"]["bloks_payload"]["tree"]["bk.components.screen.Wrapper"]["content"]["bk.components.Flexbox"]["children"][2]["bk.components.Flexbox"]["children"][0]["bk.components.Flexbox"]["children"][0]["bk.components.Collection"]["children"][1]["bk.components.Flexbox"]["on_bind"])
media_ids = extract_media_ids(on_bind_liked_media)

# Do first request outside loop, all following inside (we need that initial cursor badly)
first_liked_next_data = data
first_liked_next_data["params"] = json.dumps({
    "page_size" : 15,
    "activity_center_params" : action_liked_media[2][2][2],
    "cursor" : action_liked_media[2][2][3],
    "container_id" : action_liked_media[2][2][4],
    "element_id" : action_liked_media[2][2][5]
})

liked_next = make_request(
    "POST",
    "https://www.instagram.com/async/wbloks/fetch/",
    headers, 
    {
        "appid" : "com.instagram.privacy.activity_center.liked_next",
        "type" : "action",
        "__bkv" : params["__bkv"]
    },
    first_liked_next_data
)
async_action_liked_next = bloksParser.deserialize(liked_next["payload"]["layout"]["bloks_payload"]["embedded_payloads"][0]["payload"]["layout"]["bloks_payload"]["tree"]["bk.components.internal.Merge"]["children"][0]["bk.components.Flexbox"]["_style"]["collection"]["on_appear"])
on_bind_liked_next = bloksParser.deserialize(liked_next["payload"]["layout"]["bloks_payload"]["embedded_payloads"][0]["payload"]["layout"]["bloks_payload"]["tree"]["bk.components.internal.Merge"]["children"][1]["bk.components.Flexbox"]["on_bind"])
media_ids = extract_media_ids(on_bind_liked_next, media_ids)

try:
    while True:
        print("Current amount of reels retrieved: " + str(len(media_ids)))

        liked_next_data = first_liked_next_data
        liked_next_data["params"] = json.dumps({
            "page_size" : async_action_liked_next[2][2][1],
            "activity_center_params" : async_action_liked_next[2][2][2],
            "cursor" : async_action_liked_next[2][2][3],
            "container_id" : async_action_liked_next[2][2][4],
            "element_id" : async_action_liked_next[2][2][5]
        })

        liked_next = make_request(
            "POST",
            "https://www.instagram.com/async/wbloks/fetch/",
            headers, 
            {
                "appid" : "com.instagram.privacy.activity_center.liked_next",
                "type" : "action",
                "__bkv" : params["__bkv"]
            },
            liked_next_data
        )
        on_bind_liked_next = bloksParser.deserialize(liked_next["payload"]["layout"]["bloks_payload"]["embedded_payloads"][0]["payload"]["layout"]["bloks_payload"]["tree"]["bk.components.internal.Merge"]["children"][1]["bk.components.Flexbox"]["on_bind"])
        media_ids = extract_media_ids(on_bind_liked_next, media_ids)

        # This WILL throw if it is the last request, since there will be no more reels after it.
        async_action_liked_next = bloksParser.deserialize(liked_next["payload"]["layout"]["bloks_payload"]["embedded_payloads"][0]["payload"]["layout"]["bloks_payload"]["tree"]["bk.components.internal.Merge"]["children"][0]["bk.components.Flexbox"]["_style"]["collection"]["on_appear"])

        # Instagram rate-limits after 200 requests in an hour... Yes, you'll have to leave this running for a while.
        time.sleep(19)
        
except Exception as e:
    print(e)
    with open("all_media_ids.txt", "w") as file:
        file.write(json.dumps(media_ids))
with open("all_media_ids.txt", "w") as file:
    file.write(json.dumps(media_ids))

# Now, get friend likers. Then, organize into a neat list. This is much easier as the response is sent in direct JSON.

liked_media = {}
for media_id in sorted(media_ids):#media_ids):
    i = i + 1
    media_code = media_ids[media_id]
    try:
        likers = make_request(
            "GET",
            "https://www.instagram.com/api/v1/media/" + media_id.split("_")[0] + "/likers/",
            headers,
        )
        print("Request #" + str(i))

        for user in likers["users"]:
            if user["friendship_status"]["following"] == True and user["friendship_status"]["followed_by"] == True:
                if not (media_code in liked_media):
                    liked_media[media_code] = []

                liked_media[media_code].append(user["username"])
                print("Friend added")
            else:
                break
        
        # Instagram rate-limits after 200 requests in an hour... Yes, you'll have to leave this running for a while.
        time.sleep(19)

    except Exception as e: # 302
        print("Request #" + str(i) + " failed. Writing...")

with open("FINAL_MATCHED_REELS.txt", "w") as file:
    json.dump(liked_media, file, indent=4)