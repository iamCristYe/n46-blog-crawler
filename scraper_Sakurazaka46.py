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
    return urllib.parse.urljoin("https://sakurazaka46.com/", str)


def download_image_return_path(img_src_url: str, repo_name: str) -> str:
    # return ""
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
    result = {}
    profile_url = f"https://sakurazaka46.com/s/s46/artist/{member_id}"
    soup = BeautifulSoup(requests.get(profile_url).content, "lxml")
    result["member_name_kanji"] = soup.find_all("p", class_="name")[0].get_text()
    result["member_name_kana"] = soup.find_all("p", class_="kana")[0].get_text()
    result["member_name_romaji"] = soup.find_all("p", class_="eigo wf-a")[0].get_text()
    result["repo_name"] = (
        result["member_name_romaji"].replace(" ", "-") + "-blog-archive"
    )

    dltb = soup.find_all("dl", class_="dltb")[0]
    for i in range(5):  # 生年月日 星座 身長 出身地 血液型
        key = dltb.find_all("dt")[i].get_text()
        result[key] = dltb.find_all("dd")[i].get_text()

    result["SNS"] = {}
    if soup.find_all("dd", class_="prof-elem-sns dltb"):
        for a in soup.find_all("dd", class_="prof-elem-sns dltb")[0].children:
            # a.parent.get("class") insta
            result["SNS"][a.parent.get("class")] = a.get("href")

    print(result)
    result["profile_pic"] = download_image_return_path(
        soup.find_all("p", class_="ph")[0].find_all("img")[0].get("src"),
        result["repo_name"],
    )

    print(result)
    return result


def get_articles_url_list(member_id: int):
    current_page = 1
    current_url = f"https://sakurazaka46.com/s/s46/diary/blog/list?ct={member_id}"
    articles_url_list = []

    while True:
        soup = BeautifulSoup(requests.get(current_url).content, "lxml")
        # print(soup.prettify())
        a_list = soup.find_all("ul", class_="com-blog-part box3 fxpc")[0].find_all("a")
        for a in a_list:
            url_with_param = add_host(a.get("href"))
            # Parse the URL
            parsed_url = urllib.parse.urlparse(url_with_param)
            # Reconstruct the URL without the query parameters
            url_without_params = urllib.parse.urlunparse(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", "")
            )
            articles_url_list.append(url_without_params)
        print(f"{len(a_list)} results on page {current_page}. ({current_url})")

        next_li_div = soup.find_all("div", class_="com-pager")
        if "→" in next_li_div[-1].get_text():
            current_url = f"https://sakurazaka46.com/s/s46/diary/blog/list?ct={member_id}&page={current_page}"
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

            # https://sakurazaka46.com/s/s46/diary/detail/57724
            data["title"] = (
                soup.find_all("div", class_="inner title-wrap")[0].get_text()
                if soup.find_all("div", class_="inner title-wrap")
                else ""
            )

            data["time"] = (
                soup.find_all("article")[0]
                .find_all("p", class_="date wf-a")[-1]
                .get_text()
            )

            data["url"] = url

            content = soup.find_all("div", class_="box-article")[0]
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
    os.makedirs(result["repo_name"], exist_ok=True)
    with open(f"{result['repo_name']}/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


from dotenv import load_dotenv

load_dotenv()
member_id = os.getenv("MEMBER_ID")
main(member_id)
