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
    img_full_url = add_host(img_src_url)
    response = requests.get(img_full_url)
    img_relative_path = f"{repo_name}/{urllib.parse.urlparse(img_full_url).path[1:]}"
    os.makedirs(os.path.dirname(img_relative_path), exist_ok=True)
    with open(img_relative_path, "wb") as f:
        f.write(response.content)
    return "/" + img_relative_path


def get_profile(member_id: int):
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
        if key != "SNS":
            result[key] = dl.find_all("dd")[0].get_text()
        else:
            result["SNS"] = {}
            for a in dl.find_all("dd")[0].children:
                result["SNS"][a.get_text()] = a.get("href")

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
            articles_url_list.append(add_host(a.get("href")))
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
    data = {}
    soup = BeautifulSoup(requests.get(url).content, "lxml")
    data["title"] = soup.find_all("h1", class_="bd--hd__ttl f--head a--tx js-tdi")[
        0
    ].get_text()

    data["time"] = soup.find_all("p", class_="bd--hd__date a--tx js-tdi")[0].get_text()

    data["url"] = url

    content = soup.find_all("div", class_="bd--edit")[0]
    img_list = content.find_all("img")
    for img in img_list:
        # print(img)
        # # https://www.nogizaka46.com/s/n46/diary/detail/100646 empty img no src
        if img.get("src"):
            img["src"] = download_image_return_path(img.get("src"), repo_name)

    data["content"] = str(content)

    return data


def main(member_id: int):
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
        time.sleep(random.randint(1, 3))
    with open(f"{result['repo_name']}/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)


main(48012)  # Hayakawa Seira
