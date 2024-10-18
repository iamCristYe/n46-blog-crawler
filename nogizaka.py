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
    profile_url = f"https://www.nogizaka46.com/s/n46/artist/{member_id}"
    soup = BeautifulSoup(requests.get(profile_url).content, "lxml")
    result["member_name_kanji"] = soup.find_all(
        "h1", class_="md--hd__ttl f--head a--tx js-tdi js-membername"
    )[0].get_text()
    result["member_name_kana"] = soup.find_all(
        "p", class_="md--hd__j f--head a--tx js-tdi"
    )[0].get_text()
    # result["member_name_romaji"] = soup.find_all(
    #     "p", class_="md--hd__e f--head a--tx js-tdi"
    # )[0].get_text()
    with open("members.json") as members_json:
        members = json.load(members_json)
        for member in members["N"]:
            if member[0] == result["member_name_kanji"]:
                result["member_name_romaji"] = member[1]
                break

    result["repo_name"] = (
        result["member_name_romaji"].lower().replace(" ", "-") + "-blog-archive"
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


def get_articles_url_list(member_id: int, previous_blog_url_list: list):
    current_page = 1
    current_url = (
        f"https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct={member_id}"
    )
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
            # Previously crawled
            if url_without_params in previous_blog_url_list:
                return articles_url_list
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
                    img["src"] = download_image_return_path(img.get("src"), repo_name)

                    # # fix for staff blogs. example: https://www.nogizaka46.com/s/n46/diary/detail/22046
                    # if parent and parent.get("href"):
                    #     # Replace img src with href of the parent <a>
                    #     img["src"] = download_image_return_path(
                    #         parent.get("href"), repo_name
                    #     )
                    # else:
                    #     # If no parent <a> or no href, process the img normally
                    #     img["src"] = download_image_return_path(
                    #         img.get("src"), repo_name
                    #     )

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


member_code = [
    # 36749,  # 伊藤 理々杏
    # 36750,  # 岩本 蓮加
    # 36751,  # 梅澤 美波
    # 36753,  # 久保 史緒里
    # 36755,  # 佐藤 楓
    # 36756,  # 中村 麗乃
    # 36757,  # 向井 葉月
    # 36759,  # 吉田 綾乃クリスティー
    # 36760,  # 与田 祐希
    # 48006,  # 遠藤 さくら
    # 48008,  # 賀喜 遥香
    # 48010,  # 金川 紗耶
    # 48013,  # 柴田 柚菜
    # 48015,  # 田村 真佑
    # 48017,  # 筒井 あやめ
    # 48019,  # 矢久保 美緒
    # 55383,  # 黒見 明香
    # 55384,  # 佐藤 璃果
    # 55385,  # 林 瑠奈
    # 55386,  # 松尾 美佑
    # 55387,  # 弓木 奈於

    55389,  # 井上 和
    55390,  # 一ノ瀬 美空
    55391,  # 菅原 咲月
    55392,  # 小川 彩
    55393,  # 冨里 奈央
    55394,  # 奥田 いろは
    55395,  # 中西 アルノ
    55396,  # 五百城 茉央
    55397,  # 池田 瑛紗
    55400,  # 川﨑 桜
    55401,  # 岡本 姫奈
]

for code in member_code:
    update_repo(code)

# with open("Nogizaka46-member.json") as codes_json:
#     codes = json.load(codes_json)
#     for entry in codes["data"]:
#         print(f"{entry['code']} # {entry['name']}")

# 10001 # 乃木坂46
# 55401 # 岡本 姫奈
# 55400 # 川﨑 桜
# 55397 # 池田 瑛紗
# 55396 # 五百城 茉央
# 55395 # 中西 アルノ
# 55394 # 奥田 いろは
# 55393 # 冨里 奈央
# 55392 # 小川 彩
# 55391 # 菅原 咲月
# 55389 # 井上 和
# 55387 # 弓木 奈於
# 55386 # 松尾 美佑
# 55385 # 林 瑠奈
# 55384 # 佐藤 璃果
# 55383 # 黒見 明香
# 48014 # 清宮 レイ
# 48012 # 北川 悠理
# 48010 # 金川 紗耶
# 48019 # 矢久保 美緒
# 48018 # 早川 聖来
# 48009 # 掛橋 沙耶香
# 48008 # 賀喜 遥香
# 48017 # 筒井 あやめ
# 48015 # 田村 真佑
# 48013 # 柴田 柚菜
# 48006 # 遠藤 さくら
# 36760 # 与田 祐希
# 36759 # 吉田 綾乃クリスティー
# 36758 # 山下 美月
# 36757 # 向井 葉月
# 36756 # 中村 麗乃
# 36755 # 佐藤 楓
# 36754 # 阪口 珠美
# 36753 # 久保 史緒里
# 36752 # 大園 桃子
# 36751 # 梅澤 美波
# 36750 # 岩本 蓮加
# 36749 # 伊藤 理々杏
# 19634 # 相楽 伊織
# 17822 # 松井 玲奈
# 17383 # 渡辺 みり愛
# 17382 # 米徳 京花
# 17381 # 山崎 怜奈
# 17380 # 矢田 里沙子
# 17379 # 寺田 蘭世
# 17378 # 鈴木 絢音
# 17377 # 佐々木 琴子
# 17376 # 伊藤 純奈
# 17375 # 伊藤 かりん
# 17068 # 新内 眞衣
# 16454 # 北野 日奈子
# 14470 # 堀 未央奈
# 7639 # 秋元 真夏
# 284 # 和田 まあや
# 283 # 若月 佑美
# 282 # 大和 里菜
# 281 # 宮澤 成良
# 280 # 松村 沙友理
# 279 # 星野 みなみ
# 278 # 深川 麻衣
# 277 # 樋口 日奈
# 276 # 畠中 清羅
# 275 # 橋本 奈々未
# 274 # 能條 愛未
# 273 # 西野 七瀬
# 272 # 永島 聖羅
# 271 # 中元 日芽香
# 270 # 中田 花奈
# 269 # 高山 一実
# 268 # 白石 麻衣
# 267 # 桜井 玲香
# 266 # 斉藤 優里
# 265 # 斎藤 ちはる
# 264 # 齋藤 飛鳥
# 263 # 川村 真洋
# 262 # 川後 陽菜
# 261 # 柏 幸奈
# 260 # 衛藤 美彩
# 258 # 井上 小百合
# 257 # 伊藤 万理華
# 256 # 伊藤 寧々
# 255 # 市來 玲奈
# 55388 # 岩瀬 佑美子
# 254 # 生駒 里奈
# 253 # 生田 絵梨花
# 55390 # 一ノ瀬 美空
