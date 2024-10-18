from bs4 import BeautifulSoup
import requests
import time
import random
import json
import os
import urllib.parse
from github import Github
import subprocess

# pip install lxml
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/#the-keyword-arguments:~:text=External%20Python%20dependency-,If%20you%20can%2C%20I%20recommend%20you%20install%20and%20use%20lxml%20for%20speed.,-Note%20that%20if

member_codes = [
    # ["5", "加藤 史帆"],
    # ["7", "佐々木 久美"],
    # ["8", "佐々木 美玲"],
    # ["9", "高瀬 愛奈"],
    # ["11", "東村 芽依"],
    # ["12", "金村 美玖"],
    # ["13", "河田 陽菜"],
    # ["14", "小坂 菜緒"],
    # ["15", "富田 鈴花"],
    # ["16", "丹生 明里"],
    # ["17", "濱岸 ひより"],
    # ["18", "松田 好花"],
    # ["21", "上村 ひなの"],
    # ["22", "髙橋 未来虹"],
    # ["23", "森本 茉莉"],
    # ["24", "山口 陽世"],
    ["25", "石塚 瑶季"],
    ["27", "小西 夏菜実"],
    ["28", "清水 理央"],
    ["29", "正源司 陽子"],
    ["30", "竹内 希来里"],
    ["31", "平尾 帆夏"],
    ["32", "平岡 海月"],
    ["33", "藤嶌 果歩"],
    ["34", "宮地 すみれ"],
    ["35", "山下 葉留花"],
    ["36", "渡辺 莉奈"],
]


def add_host(str: str) -> str:
    return urllib.parse.urljoin("https://www.hinatazaka46.com/", str)


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


def get_profile(member_id: str):
    result = {}

    profile_url = f"https://www.hinatazaka46.com/s/official/artist/{member_id}"
    soup = BeautifulSoup(requests.get(profile_url).content, "lxml")

    result["member_name_kana"] = (
        soup.find_all("div", class_="c-member__kana")[0].get_text().strip()
    )

    temp_en = soup.find_all("span", class_="name_en")[0].get_text()
    result["member_name_kanji"] = (
        soup.find_all("div", class_="c-member__name--info")[0]
        .get_text()
        .replace(temp_en, "")
        .strip()
    )

    for entry in member_codes:
        if member_id == entry[0]:
            result["member_name_kanji"] = entry[1]

    with open("members.json") as members_json:
        members = json.load(members_json)
        for member in members["H"]:
            if member[0] == result["member_name_kanji"]:
                result["member_name_romaji"] = member[1]
                break

    result["repo_name"] = (
        result["member_name_romaji"].lower().replace(" ", "-") + "-blog-archive"
    )

    info_table = soup.find_all("table", class_="p-member__info-table")[0]
    for i in range(5):  # 生年月日 星座 身長 出身地 血液型
        key = info_table.find_all("td")[i * 2].get_text().strip()
        result[key] = info_table.find_all("td")[i * 2 + 1].get_text().strip()

    result["SNS"] = {}
    temp_td__text_list = soup.find_all("td", class_="c-member__info-td__text")
    if len(temp_td__text_list) > 5:
        for a in temp_td__text_list[5].find_all("a"):
            if "instagram" in a.get("href"):
                result["SNS"]["Instagram"] = a.get("href")
            else:
                raise Exception

    print(result)
    result["profile_pic"] = download_image_return_path(
        soup.find_all("div", class_="c-member__thumb c-member__thumb__large")[0]
        .find_all("img")[0]
        .get("src"),
        result["repo_name"],
    )

    print(result)
    return result


def get_articles_url_list(member_id: int, previous_blog_url_list: list):
    current_page = 0
    articles_url_list = []

    while True:
        current_url = f"https://www.hinatazaka46.com/s/official/diary/member/list?page={current_page}&ct={member_id}"
        soup = BeautifulSoup(requests.get(current_url).content, "lxml")
        # print(soup.prettify())
        a_list = soup.find_all("a", string="個別ページ")
        for a in a_list:
            url_with_param = add_host(a.get("href"))
            # Parse the URL
            parsed_url = urllib.parse.urlparse(url_with_param)
            # Reconstruct the URL without the query parameters
            url_without_params = urllib.parse.urlunparse(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", "")
            )
            # Previously crawled
            if url_without_params in previous_blog_url_list:
                return articles_url_list
            articles_url_list.append(url_without_params)
        print(f"{len(a_list)} results on page {current_page}.")

        next_page = soup.find_all(
            "li", class_="c-pager__item--count c-pager__item--next"
        )
        if next_page:
            current_page += 1

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
            data["title"] = (
                soup.find_all("div", class_="c-blog-article__title")[0]
                .get_text()
                .strip()
            )

            data["time"] = (
                soup.find_all("div", class_="c-blog-article__date")[0]
                .get_text()
                .strip()
            )

            data["url"] = url

            content = soup.find_all("div", class_="c-blog-article__text")[0]
            img_list = content.find_all("img")
            for img in img_list:
                # Check if the img has a src attribute
                if img.get("src"):
                    img["src"] = download_image_return_path(img.get("src"), repo_name)

            data["content"] = str(content)

            return data
        except Exception as e:
            print(e)
            time.sleep(random.randint(30, 60))
            pass


def update_repo(member_id: int):
    import sys

    sys.setrecursionlimit(4646)
    # fix https://www.nogizaka46.com/s/n46/diary/detail/56176

    result = get_profile(member_id)
    repo_name = result["repo_name"]
    # Fix profile_pic already exists leading to clone failing
    subprocess.run(["rm", "-rf", repo_name])

    # Replace with your GitHub token and organization name
    token = os.getenv("TOKEN_GITHUB")
    organization_name = "SakamichiSeries"

    g = Github(token)
    org = g.get_organization(organization_name)
    try:
        repo = org.get_repo(repo_name)
        print(f"Repository '{repo_name}' already exists.")
    except:
        # Create a new repository
        repo = org.create_repo(name=repo_name)
        print(f"Creating repository '{repo_name}'.")
    # clone_url = repo.clone_url
    clone_url = f"https://{token}@github.com/SakamichiSeries/{repo_name}.git"
    subprocess.run(["git", "clone", clone_url])
    result = get_profile(member_id)

    previous_blog_url_list = []
    if os.path.exists(repo_name + "/result.json"):
        with open(repo_name + "/result.json") as previous_json:
            previous_result = json.load(previous_json)
            for blog_entry in previous_result["blog"]:
                previous_blog_url_list.append(blog_entry["url"])
                print("Previous blog url: " + blog_entry["url"])

    articles_url_list = get_articles_url_list(member_id, previous_blog_url_list)
    result["blog"] = []

    for i in range(len(articles_url_list)):
        print(f"downloading {i+1}/{len(articles_url_list)}: {articles_url_list[i]}")
        article = get_blog_content(articles_url_list[i], result["repo_name"])
        result["blog"].append(article)
        # time.sleep(random.randint(1, 3))

    # Add back previous results:
    if os.path.exists(repo_name + "/result.json"):
        with open(repo_name + "/result.json") as previous_json:
            for blog_entry in previous_result["blog"]:
                result["blog"].append(blog_entry)

    with open(f"{result['repo_name']}/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    subprocess.run(["cp", "../.nojekyll", "."], cwd=repo_name)
    subprocess.run(
        ["git", "config", "--local", "user.name", "GitHub Action"],
        check=True,
        cwd=repo_name,
    )
    subprocess.run(
        ["git", "config", "--local", "user.email", "action@github.com"],
        check=True,
        cwd=repo_name,
    )

    # Add all changes
    subprocess.run(["git", "add", "-A"], check=True, cwd=repo_name)

    try:
        # Commit the changes
        subprocess.run(
            ["git", "commit", "-m", "Automated commit by GitHub Action"],
            check=True,
            cwd=repo_name,
        )

        # Push the changes
        subprocess.run(["git", "push"], check=True, cwd=repo_name)
    except:
        pass


for code in member_codes:
    update_repo(code[0])
