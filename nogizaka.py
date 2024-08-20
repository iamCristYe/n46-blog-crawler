from bs4 import BeautifulSoup
import requests
import time
import random
import json
import os
import urllib.parse

# pip install lxml
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/#the-keyword-arguments:~:text=External%20Python%20dependency-,If%20you%20can%2C%20I%20recommend%20you%20install%20and%20use%20lxml%20for%20speed.,-Note%20that%20if


def add_host(str: str) -> str:
    return urllib.parse.urljoin("https://www.nogizaka46.com/", str)


def download_image_return_path(img_src_url: str, repo_name: str) -> str:
    if img_src_url.startswith("blob"):
        return img_src_url
    if img_src_url.startswith("cid"):
        return img_src_url
    img_full_url = add_host(img_src_url)
    img_relative_path = f"{repo_name}/{urllib.parse.urlparse(img_full_url).path[1:]}"
    if os.path.exists(img_relative_path):
        print(f"File exists: {img_relative_path}")
        return "/" + img_relative_path
    os.makedirs(os.path.dirname(img_relative_path), exist_ok=True)
    fail_count = 0
    while True:
        try:
            if fail_count > 3:
                return "/" + img_relative_path

            response = requests.get(img_full_url)
            with open(img_relative_path, "wb") as f:
                f.write(response.content)
            print(f"File saved: {img_relative_path}")
            return "/" + img_relative_path
        except Exception as e:
            fail_count += 1
            print(e)
            time.sleep(random.randint(30, 60))
            pass


def get_profile(member_id: int):
    if str(member_id).startswith("40003"):
        return {
            "member_name_kanji": "運営スタッフ",
            "member_name_kana": "",
            "member_name_romaji": "staff",
            "repo_name": "staff-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/9/92/Nogizaka46_logo.png",
        }
    if str(member_id).startswith("40004"):
        return {
            "member_name_kanji": "3期生",
            "member_name_kana": "",
            "member_name_romaji": "sankisei",
            "repo_name": "sankisei-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/9/92/Nogizaka46_logo.png",
        }
    if str(member_id).startswith("40005"):
        return {
            "member_name_kanji": "4期生",
            "member_name_kana": "",
            "member_name_romaji": "yonkisei",
            "repo_name": "yonkisei-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/9/92/Nogizaka46_logo.png",
        }
    if str(member_id).startswith("40001"):
        return {
            "member_name_kanji": "新4期生",
            "member_name_kana": "",
            "member_name_romaji": "shinyonkisei",
            "repo_name": "shinyonkisei-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/9/92/Nogizaka46_logo.png",
        }
    if str(member_id).startswith("40007"):
        return {
            "member_name_kanji": "5期生",
            "member_name_kana": "",
            "member_name_romaji": "gokisei",
            "repo_name": "gokisei-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/9/92/Nogizaka46_logo.png",
        }
    result = {}
    profile_url = f"https://www.nogizaka46.com/s/n46/artist/{member_id}?ima=0826"
    soup = BeautifulSoup(requests.get(profile_url).content, "lxml")
    result["member_name_kanji"] = soup.find_all(
        "h1", class_="md--hd__ttl f--head a--tx js-tdi js-membername"
    )[0].get_text()
    result["member_name_kana"] = soup.find_all(
        "p", class_="md--hd__j f--head a--tx js-tdi"
    )[0].get_text()
    result["member_name_romaji"] = soup.find_all(
        "p", class_="md--hd__e f--head a--tx js-tdi"
    )[0].get_text()
    result["repo_name"] = (
        result["member_name_romaji"].replace(" ", "-") + "-blog-archive"
    )

    dl_list = soup.find_all("dl", class_="md--hd__data a--tx js-tdi")
    for dl in dl_list:
        key = dl.find_all("dt")[0].get_text()
        result["SNS"] = {}
        if key != "SNS":
            result[key] = dl.find_all("dd")[0].get_text()
        else:
            for a in dl.find_all("dd")[0].children:
                result["SNS"][a.get_text()] = a.get("href")
    print(result)
    result["profile_pic"] = download_image_return_path(
        soup.find_all("div", class_="md--hd__fig a--img js-pos m--fig")[0]
        .find_all("div")[0]
        .get("data-src"),
        result["repo_name"],
    )

    print(result)
    return result


def get_articles_url_list(member_id: int):
    current_page = 1
    current_url = f"https://www.nogizaka46.com/s/n46/diary/MEMBER/list?ima=5941&page=0&ct={member_id}"
    articles_url_list = []

    while True:
        soup = BeautifulSoup(requests.get(current_url).content, "lxml")
        # print(soup.prettify())
        a_list = soup.find_all("a", class_="bl--card js-pos a--op hv--thumb")
        for a in a_list:
            url_with_param = add_host(a.get("href"))
            # Parse the URL
            parsed_url = urllib.parse.urlparse(url_with_param)
            # Reconstruct the URL without the query parameters
            url_without_params = urllib.parse.urlunparse(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", "")
            )
            articles_url_list.append(url_without_params)
        print(f"{len(a_list)} results on page {current_page}.")

        next_li = soup.find_all("li", class_="next")
        if next_li:
            for a in next_li[0]:
                current_url = add_host(a.get("href"))
            current_page += 1
            # print(articles_url_list)
            # print(current_url)

            # when testing, uncomment below line to only get page 1
            # break
            time.sleep(random.randint(1, 3))
        else:
            break

    return articles_url_list


def get_blog_content(url: str, repo_name: str):
    while True:
        try:
            data = {}
            soup = BeautifulSoup(requests.get(url).content, "lxml")
            data["title"] = soup.find_all(
                "h1", class_="bd--hd__ttl f--head a--tx js-tdi"
            )[0].get_text()

            data["time"] = soup.find_all("p", class_="bd--hd__date a--tx js-tdi")[
                0
            ].get_text()

            data["url"] = url

            content = soup.find_all("div", class_="bd--edit")[0]
            img_list = content.find_all("img")
            for img in img_list:
                # Check if the img has a src attribute
                if img.get("src"):
                    # Check if the parent is an <a> tag
                    parent = img.find_parent("a")
                    # fix for staff blogs. example: https://www.nogizaka46.com/s/n46/diary/detail/22046
                    if parent and parent.get("href"):
                        # Replace img src with href of the parent <a>
                        img["src"] = download_image_return_path(
                            parent.get("href"), repo_name
                        )
                    else:
                        # If no parent <a> or no href, process the img normally
                        img["src"] = download_image_return_path(
                            img.get("src"), repo_name
                        )

            data["content"] = str(content)

            return data
        except Exception as e:
            print(e)
            time.sleep(random.randint(30, 60))
            pass


def main(member_id: int):
    import sys

    sys.setrecursionlimit(4646)
    # fix https://www.nogizaka46.com/s/n46/diary/detail/56176

    get_blog_content(
        "https://www.nogizaka46.com/s/n46/diary/detail/22046?ima=0755&cd=MEMBER",
        "test-blog",
    )

    result = {}
    profile = get_profile(member_id)
    for key in profile:
        result[key] = profile[key]

    articles_url_list = get_articles_url_list(member_id)
    result["blog"] = []

    for i in range(len(articles_url_list)):
        print(f"downloading {i+1}/{len(articles_url_list)}: {articles_url_list[i]}")
        article = get_blog_content(articles_url_list[i], result["repo_name"])
        result["blog"].append(article)
        # time.sleep(random.randint(1, 3))
    with open(f"{result['repo_name']}/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


from dotenv import load_dotenv

load_dotenv()
member_id = os.getenv("MEMBER_ID")
main(member_id)
