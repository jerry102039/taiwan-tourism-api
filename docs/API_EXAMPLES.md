# API 實測範例

> 由 `python client/api_client.py --record docs/API_EXAMPLES.md` 對 `http://127.0.0.1:8000` 實際執行後自動產生。
> 長字串與超過 3 筆的陣列已截斷以便閱讀。寫入操作皆帶有 Header `X-API-Key: ntub-iot-2026`。

| # | 說明 | Method | Path | Status |
|---|---|---|---|---|
| 1 | [查詢景點列表（分頁）](#1) | `GET` | `/api/v1/attractions?page=1&page_size=3` | 200 |
| 2 | [多條件篩選：臺北市的宗教廟宇類景點，依名稱排序](#2) | `GET` | `/api/v1/attractions?city=臺北&category_id=4&sort=name&page_size=3` | 200 |
| 3 | [關鍵字搜尋：老街](#3) | `GET` | `/api/v1/attractions?q=老街&page_size=3` | 200 |
| 4 | [取得單一景點詳細資料](#4) | `GET` | `/api/v1/attractions/Attraction_345040000G_000001` | 200 |
| 5 | [查詢北商大附近 1 公里內的景點](#5) | `GET` | `/api/v1/attractions/nearby?lat=25.0421&lon=121.5253&radius_km=1&limit=3` | 200 |
| 6 | [查詢不存在的景點（錯誤處理）](#6) | `GET` | `/api/v1/attractions/Attraction_NOT_EXIST` | 404 |
| 7 | [未帶 API Key 新增景點（驗證失敗）](#7) | `POST` | `/api/v1/attractions` | 401 |
| 8 | [新增景點](#8) | `POST` | `/api/v1/attractions` | 201 |
| 9 | [重複新增相同 ID（衝突）](#9) | `POST` | `/api/v1/attractions` | 409 |
| 10 | [新增景點但縣市代碼不存在（驗證失敗）](#10) | `POST` | `/api/v1/attractions` | 422 |
| 11 | [部分更新景點 (PATCH)](#11) | `PATCH` | `/api/v1/attractions/Attraction_DEMO_0001` | 200 |
| 12 | [整筆更新景點 (PUT)](#12) | `PUT` | `/api/v1/attractions/Attraction_DEMO_0001` | 200 |
| 13 | [列出景點圖片](#13) | `GET` | `/api/v1/attractions/Attraction_DEMO_0001/images` | 200 |
| 14 | [新增景點圖片](#14) | `POST` | `/api/v1/attractions/Attraction_DEMO_0001/images` | 201 |
| 15 | [取得單張圖片](#15) | `GET` | `/api/v1/attractions/Attraction_DEMO_0001/images/10726` | 200 |
| 16 | [部分更新圖片](#16) | `PATCH` | `/api/v1/attractions/Attraction_DEMO_0001/images/10726` | 200 |
| 17 | [整筆更新圖片](#17) | `PUT` | `/api/v1/attractions/Attraction_DEMO_0001/images/10726` | 200 |
| 18 | [刪除圖片](#18) | `DELETE` | `/api/v1/attractions/Attraction_DEMO_0001/images/10726` | 204 |
| 19 | [為景點新增評論（巢狀路徑）](#19) | `POST` | `/api/v1/attractions/Attraction_DEMO_0001/reviews` | 201 |
| 20 | [新增評論（扁平路徑）](#20) | `POST` | `/api/v1/reviews` | 201 |
| 21 | [新增評論但評分超出範圍（驗證失敗）](#21) | `POST` | `/api/v1/reviews` | 422 |
| 22 | [查詢某景點的評論](#22) | `GET` | `/api/v1/attractions/Attraction_DEMO_0001/reviews` | 200 |
| 23 | [查詢 4 星以上的評論](#23) | `GET` | `/api/v1/reviews?min_rating=4&page_size=5` | 200 |
| 24 | [取得單一評論](#24) | `GET` | `/api/v1/reviews/1` | 200 |
| 25 | [部分更新評論](#25) | `PATCH` | `/api/v1/reviews/2` | 200 |
| 26 | [整筆更新評論](#26) | `PUT` | `/api/v1/reviews/2` | 200 |
| 27 | [景點詳細資料（含平均評分）](#27) | `GET` | `/api/v1/attractions/Attraction_DEMO_0001` | 200 |
| 28 | [評價最高的景點](#28) | `GET` | `/api/v1/stats/top-rated?limit=3` | 200 |
| 29 | [建立行程（同時加入行程項目）](#29) | `POST` | `/api/v1/trips` | 201 |
| 30 | [行程加入景點](#30) | `POST` | `/api/v1/trips/1/items` | 201 |
| 31 | [列出行程項目](#31) | `GET` | `/api/v1/trips/1/items` | 200 |
| 32 | [取得單一行程項目](#32) | `GET` | `/api/v1/trips/1/items/2` | 200 |
| 33 | [部分更新行程項目](#33) | `PATCH` | `/api/v1/trips/1/items/2` | 200 |
| 34 | [整筆更新行程項目](#34) | `PUT` | `/api/v1/trips/1/items/2` | 200 |
| 35 | [部分更新行程](#35) | `PATCH` | `/api/v1/trips/1` | 200 |
| 36 | [行程日期錯誤（驗證失敗）](#36) | `PATCH` | `/api/v1/trips/1` | 422 |
| 37 | [取得行程（含項目）](#37) | `GET` | `/api/v1/trips/1` | 200 |
| 38 | [列出行程](#38) | `GET` | `/api/v1/trips?owner=小明` | 200 |
| 39 | [刪除行程項目](#39) | `DELETE` | `/api/v1/trips/1/items/2` | 204 |
| 40 | [整筆更新行程 (PUT)](#40) | `PUT` | `/api/v1/trips/1` | 200 |
| 41 | [刪除行程](#41) | `DELETE` | `/api/v1/trips/1` | 204 |
| 42 | [列出景點類型](#42) | `GET` | `/api/v1/categories?page_size=5` | 200 |
| 43 | [取得單一景點類型](#43) | `GET` | `/api/v1/categories/16` | 200 |
| 44 | [新增景點類型](#44) | `POST` | `/api/v1/categories` | 201 |
| 45 | [部分更新景點類型](#45) | `PATCH` | `/api/v1/categories/900` | 200 |
| 46 | [整筆更新景點類型](#46) | `PUT` | `/api/v1/categories/900` | 200 |
| 47 | [刪除景點類型](#47) | `DELETE` | `/api/v1/categories/900` | 204 |
| 48 | [列出縣市](#48) | `GET` | `/api/v1/cities?page_size=5` | 200 |
| 49 | [取得單一縣市](#49) | `GET` | `/api/v1/cities/63000` | 200 |
| 50 | [列出臺北市的行政區](#50) | `GET` | `/api/v1/cities/63000/towns` | 200 |
| 51 | [新增縣市](#51) | `POST` | `/api/v1/cities` | 201 |
| 52 | [新增鄉鎮市區](#52) | `POST` | `/api/v1/towns` | 201 |
| 53 | [查詢鄉鎮市區（依縣市）](#53) | `GET` | `/api/v1/towns?city_code=99001` | 200 |
| 54 | [取得單一鄉鎮市區](#54) | `GET` | `/api/v1/towns/99001010` | 200 |
| 55 | [部分更新鄉鎮市區](#55) | `PATCH` | `/api/v1/towns/99001010` | 200 |
| 56 | [整筆更新鄉鎮市區](#56) | `PUT` | `/api/v1/towns/99001010` | 200 |
| 57 | [更新縣市 (PUT)](#57) | `PUT` | `/api/v1/cities/99001` | 200 |
| 58 | [刪除仍有景點的縣市（衝突）](#58) | `DELETE` | `/api/v1/cities/63000` | 409 |
| 59 | [刪除鄉鎮市區](#59) | `DELETE` | `/api/v1/towns/99001010` | 204 |
| 60 | [刪除縣市](#60) | `DELETE` | `/api/v1/cities/99001` | 204 |
| 61 | [資料總覽](#61) | `GET` | `/api/v1/stats/overview` | 200 |
| 62 | [各縣市景點數](#62) | `GET` | `/api/v1/stats/cities` | 200 |
| 63 | [各類型景點數](#63) | `GET` | `/api/v1/stats/categories` | 200 |
| 64 | [刪除景點（連同評論一併刪除）](#64) | `DELETE` | `/api/v1/attractions/Attraction_DEMO_0001` | 204 |
| 65 | [確認景點已刪除](#65) | `GET` | `/api/v1/attractions/Attraction_DEMO_0001` | 404 |
| 66 | [確認評論已連帶刪除](#66) | `GET` | `/api/v1/reviews/1` | 404 |

<a id="1"></a>
## 1. 查詢景點列表（分頁）

**Request**

```http
GET /api/v1/attractions?page=1&page_size=3
```

**Response** — Status Code: `200`

```json
{
  "total": 6226,
  "page": 1,
  "page_size": 3,
  "pages": 2076,
  "items": [
    {
      "id": "Attraction_345040000G_000001",
      "name": "太平山國家森林遊樂區",
      "city": {
        "code": "10002",
        "name": "宜蘭縣"
      },
      "town": {
        "code": "10002110",
        "name": "大同鄉"
      },
      "categories": [
        {
          "id": 16,
          "name": "森林遊樂區類"
        }
      ],
      "latitude": 24.5574676798311,
      "longitude": 121.49949962026885,
      "is_free": false,
      "service_status": 1,
      "cover_image": "https://recreation.forest.gov.tw/Files/Forest/RA/photo/album/0100001/01_%E5%A4%AA%E5%B9%B3%E5%B1%B1%E5%9C%8B%E5%AE%B6%E6…"
    },
    {
      "id": "Attraction_345040000G_000002",
      "name": "滿月圓國家森林遊樂區",
      "city": {
        "code": "65000",
        "name": "新北市"
      },
      "town": {
        "code": "65000090",
        "name": "三峽區"
      },
      "categories": [
        {
          "id": 16,
          "name": "森林遊樂區類"
        }
      ],
      "latitude": 24.830781104172626,
      "longitude": 121.44458529554898,
      "is_free": false,
      "service_status": 1,
      "cover_image": "https://recreation.forest.gov.tw/Files/Forest/RA/photo/album/0200001/DSCN1261.jpg"
    },
    {
      "id": "Attraction_345040000G_000003",
      "name": "內洞國家森林遊樂區",
      "city": {
        "code": "65000",
        "name": "新北市"
      },
      "town": {
        "code": "65000290",
        "name": "烏來區"
      },
      "categories": [
        {
          "id": 16,
          "name": "森林遊樂區類"
        }
      ],
      "latitude": 24.834425607300727,
      "longitude": 121.5261399307585,
      "is_free": false,
      "service_status": 1,
      "cover_image": "https://recreation.forest.gov.tw/Files/Forest/RA/photo/album/0200002/DSCN9298.jpg"
    }
  ]
}
```

<a id="2"></a>
## 2. 多條件篩選：臺北市的宗教廟宇類景點，依名稱排序

**Request**

```http
GET /api/v1/attractions?city=臺北&category_id=4&sort=name&page_size=3
```

**Response** — Status Code: `200`

```json
{
  "total": 52,
  "page": 1,
  "page_size": 3,
  "pages": 18,
  "items": [
    {
      "id": "Attraction_379000000A_002666",
      "name": "佛光山台北道場",
      "city": {
        "code": "63000",
        "name": "臺北市"
      },
      "town": {
        "code": "63000020",
        "name": "信義區"
      },
      "categories": [
        {
          "id": 1,
          "name": "文化類"
        },
        {
          "id": 4,
          "name": "宗教廟宇類"
        },
        {
          "id": 12,
          "name": "遊憩類"
        },
        "...（其餘 1 筆省略）"
      ],
      "latitude": 25.048453,
      "longitude": 121.579119,
      "is_free": false,
      "service_status": 1,
      "cover_image": "https://www.travel.taipei/content/images/attractions/574221/640x480_attractions-image-ahoh1bqumuuitjqzn0-cna.jpg"
    },
    {
      "id": "Attraction_379000000A_000066",
      "name": "北投普濟寺",
      "city": {
        "code": "63000",
        "name": "臺北市"
      },
      "town": {
        "code": "63000120",
        "name": "北投區"
      },
      "categories": [
        {
          "id": 1,
          "name": "文化類"
        },
        {
          "id": 4,
          "name": "宗教廟宇類"
        },
        {
          "id": 12,
          "name": "遊憩類"
        }
      ],
      "latitude": 25.13593,
      "longitude": 121.51126,
      "is_free": false,
      "service_status": 1,
      "cover_image": "https://www.travel.taipei/content/images/attractions/63921/640x480_attractions-image-leihkwo83uwnkvlxeweprw.jpg"
    },
    {
      "id": "Attraction_379000000A_000070",
      "name": "台北天后宮",
      "city": {
        "code": "63000",
        "name": "臺北市"
      },
      "town": {
        "code": "63000070",
        "name": "萬華區"
      },
      "categories": [
        {
          "id": 1,
          "name": "文化類"
        },
        {
          "id": 4,
          "name": "宗教廟宇類"
        },
        {
          "id": 12,
          "name": "遊憩類"
        }
      ],
      "latitude": 25.042798,
      "longitude": 121.506321,
      "is_free": false,
      "service_status": 1,
      "cover_image": "https://www.travel.taipei/content/images/attractions/574163/640x480_attractions-image-6cy88tn6v0gsnrkfztt5ua.jpg"
    }
  ]
}
```

<a id="3"></a>
## 3. 關鍵字搜尋：老街

**Request**

```http
GET /api/v1/attractions?q=老街&page_size=3
```

**Response** — Status Code: `200`

```json
{
  "total": 222,
  "page": 1,
  "page_size": 3,
  "pages": 74,
  "items": [
    {
      "id": "Attraction_371020000A_000458",
      "name": "明遺老街",
      "city": {
        "code": "09020",
        "name": "金門縣"
      },
      "town": {
        "code": "09020010",
        "name": "金城鎮"
      },
      "categories": [
        {
          "id": 3,
          "name": "文化資產類"
        }
      ],
      "latitude": 24.40359,
      "longitude": 118.30875,
      "is_free": false,
      "service_status": 1,
      "cover_image": "https://kinmen.travel/image/10182/640x480"
    },
    {
      "id": "Attraction_371020000A_000823",
      "name": "迴向殿",
      "city": {
        "code": "09020",
        "name": "金門縣"
      },
      "town": {
        "code": "09020010",
        "name": "金城鎮"
      },
      "categories": [
        {
          "id": 4,
          "name": "宗教廟宇類"
        }
      ],
      "latitude": 24.40408,
      "longitude": 118.30951,
      "is_free": false,
      "service_status": 1,
      "cover_image": "https://kinmen.travel/image/2475/640x480"
    },
    {
      "id": "Attraction_371020000A_001397",
      "name": "金東電影院",
      "city": {
        "code": "09020",
        "name": "金門縣"
      },
      "town": {
        "code": "09020020",
        "name": "金沙鎮"
      },
      "categories": [
        {
          "id": 1,
          "name": "文化類"
        }
      ],
      "latitude": 24.47894,
      "longitude": 118.42741,
      "is_free": false,
      "service_status": 1,
      "cover_image": "https://kinmen.travel/image/18514/640x480"
    }
  ]
}
```

<a id="4"></a>
## 4. 取得單一景點詳細資料

**Request**

```http
GET /api/v1/attractions/Attraction_345040000G_000001
```

**Response** — Status Code: `200`

```json
{
  "id": "Attraction_345040000G_000001",
  "name": "太平山國家森林遊樂區",
  "description": "蹦蹦車、溫泉、高山湖泊、巨木森林與國寶山毛櫸，鋪成了太平山國家森林遊樂區超過百年歷史的綿長軌跡。  太平山舊稱「眠腦」，是泰雅族語「鬱鬱蒼蒼」之意。1914年，日本人先做了資源調查，1915年決議開發。《台灣日日新報》在1936年7月28日…",
  "alternate_names": [],
  "latitude": 24.5574676798311,
  "longitude": 121.49949962026885,
  "city": {
    "code": "10002",
    "name": "宜蘭縣"
  },
  "town": {
    "code": "10002110",
    "name": "大同鄉"
  },
  "zip_code": "267",
  "street_address": "太平巷58之1號",
  "full_address": "267宜蘭縣大同鄉太平巷58之1號",
  "telephones": [
    "(03)9770766",
    "(03)9809619",
    "(03)9809805",
    "...（其餘 5 筆省略）"
  ],
  "website_url": "https://recreation.forest.gov.tw/Forest/RA?typ_id=0100001",
  "service_time_info": null,
  "traffic_info": "［開車前往］從台北出發（經宜蘭交流道）：台北→國道5號→宜蘭(交流道)→省道台7線→省道台7甲線(3.7K)→宜專1線→土場→鳩之澤→太平山。［開車前往］從台北出發（經羅東交流道）：台北→國道5號→羅東(交流道)→省道台7丙線→省道台7線→…",
  "parking_info": "大型車：100元。小型車：100元。機車：20元。",
  "fee_info": null,
  "service_status": 1,
  "service_status_label": "正常營運",
  "is_public_access": true,
  "is_free": false,
  "visit_duration": null,
  "assets_class": null,
  "assets_class_label": null,
  "tags": [
    "賞楓",
    "雲海",
    "檜木原始林",
    "...（其餘 6 筆省略）"
  ],
  "remarks": null,
  "categories": [
    {
      "id": 16,
      "name": "森林遊樂區類"
    }
  ],
  "images": [
    {
      "id": 1,
      "attraction_id": "Attraction_345040000G_000001",
      "url": "https://recreation.forest.gov.tw/Files/Forest/RA/photo/album/0100001/01_%E5%A4%AA%E5%B9%B3%E5%B1%B1%E5%9C%8B%E5%AE%B6%E6…",
      "name": "翠峰湖日出",
      "description": "照片提供｜宜蘭分署"
    },
    {
      "id": 2,
      "attraction_id": "Attraction_345040000G_000001",
      "url": "https://recreation.forest.gov.tw/Files/Forest/RA/photo/album/0100001/02_BASE_01.jpg",
      "name": "雲海",
      "description": "照片提供｜宜蘭分署"
    },
    {
      "id": 3,
      "attraction_id": "Attraction_345040000G_000001",
      "url": "https://recreation.forest.gov.tw/Files/Forest/RA/photo/album/0100001/03_P176-177.jpg",
      "name": "瀑布",
      "description": "照片提供｜宜蘭分署"
    },
    "...（其餘 13 筆省略）"
  ],
  "review_count": 0,
  "average_rating": null,
  "source_update_time": "2026-09-26T12:20:18+08:00",
  "created_at": "2026-09-26T10:32:27",
  "updated_at": "2026-09-26T10:32:27"
}
```

<a id="5"></a>
## 5. 查詢北商大附近 1 公里內的景點

**Request**

```http
GET /api/v1/attractions/nearby?lat=25.0421&lon=121.5253&radius_km=1&limit=3
```

**Response** — Status Code: `200`

```json
[
  {
    "id": "Attraction_379000000A_003686",
    "name": "李國鼎故居",
    "city": {
      "code": "63000",
      "name": "臺北市"
    },
    "town": {
      "code": "63000050",
      "name": "中正區"
    },
    "categories": [
      {
        "id": 1,
        "name": "文化類"
      },
      {
        "id": 3,
        "name": "文化資產類"
      },
      {
        "id": 12,
        "name": "遊憩類"
      },
      "...（其餘 2 筆省略）"
    ],
    "latitude": 25.040642,
    "longitude": 121.527671,
    "is_free": false,
    "service_status": 1,
    "cover_image": "https://www.travel.taipei/content/images/attractions/376106/640x480_attractions-image-a39x3och7uo12aj5pmctwa.jpg",
    "distance_km": 0.289
  },
  {
    "id": "Attraction_379000000A_002216",
    "name": "臺灣文學基地",
    "city": {
      "code": "63000",
      "name": "臺北市"
    },
    "town": {
      "code": "63000050",
      "name": "中正區"
    },
    "categories": [
      {
        "id": 1,
        "name": "文化類"
      },
      {
        "id": 3,
        "name": "文化資產類"
      },
      {
        "id": 5,
        "name": "藝術類"
      },
      "...（其餘 2 筆省略）"
    ],
    "latitude": 25.041151,
    "longitude": 121.528486,
    "is_free": false,
    "service_status": 1,
    "cover_image": "https://www.travel.taipei/content/images/attractions/193197/640x480_attractions-image-vweoivjazkwwjfrdqjfgdw.jpg",
    "distance_km": 0.338
  },
  {
    "id": "Attraction_379000000A_000240",
    "name": "蒲添生雕塑紀念館",
    "city": {
      "code": "63000",
      "name": "臺北市"
    },
    "town": {
      "code": "63000050",
      "name": "中正區"
    },
    "categories": [
      {
        "id": 1,
        "name": "文化類"
      },
      {
        "id": 3,
        "name": "文化資產類"
      },
      {
        "id": 5,
        "name": "藝術類"
      },
      "...（其餘 2 筆省略）"
    ],
    "latitude": 25.045543,
    "longitude": 121.524675,
    "is_free": false,
    "service_status": 1,
    "cover_image": "https://www.travel.taipei/content/images/attractions/65004/640x480_attractions-image-skkzulnvauggnyilq73fvw.jpg",
    "distance_km": 0.388
  }
]
```

<a id="6"></a>
## 6. 查詢不存在的景點（錯誤處理）

**Request**

```http
GET /api/v1/attractions/Attraction_NOT_EXIST
```

**Response** — Status Code: `404`

```json
{
  "detail": "Attraction 'Attraction_NOT_EXIST' 不存在"
}
```

<a id="7"></a>
## 7. 未帶 API Key 新增景點（驗證失敗）

**Request**

```http
POST /api/v1/attractions
Content-Type: application/json

{
  "id": "Attraction_DEMO_0001",
  "name": "國立臺北商業大學",
  "description": "位於臺北市中正區的商業大學，鄰近華山文創園區。",
  "latitude": 25.0421,
  "longitude": 121.5253,
  "city_code": "63000",
  "town_code": "63000050",
  "zip_code": "100",
  "street_address": "濟南路一段321號",
  "telephones": [
    "(02)2322-6050"
  ],
  "website_url": "https://www.ntub.edu.tw",
  "is_free": true,
  "tags": [
    "校園",
    "學習"
  ],
  "category_ids": [
    1,
    12
  ]
}
```

**Response** — Status Code: `401`

```json
{
  "detail": "缺少 X-API-Key header"
}
```

<a id="8"></a>
## 8. 新增景點

**Request**

```http
POST /api/v1/attractions
Content-Type: application/json

{
  "id": "Attraction_DEMO_0001",
  "name": "國立臺北商業大學",
  "description": "位於臺北市中正區的商業大學，鄰近華山文創園區。",
  "latitude": 25.0421,
  "longitude": 121.5253,
  "city_code": "63000",
  "town_code": "63000050",
  "zip_code": "100",
  "street_address": "濟南路一段321號",
  "telephones": [
    "(02)2322-6050"
  ],
  "website_url": "https://www.ntub.edu.tw",
  "is_free": true,
  "tags": [
    "校園",
    "學習"
  ],
  "category_ids": [
    1,
    12
  ]
}
```

**Response** — Status Code: `201`

```json
{
  "id": "Attraction_DEMO_0001",
  "name": "國立臺北商業大學",
  "description": "位於臺北市中正區的商業大學，鄰近華山文創園區。",
  "alternate_names": [],
  "latitude": 25.0421,
  "longitude": 121.5253,
  "city": {
    "code": "63000",
    "name": "臺北市"
  },
  "town": {
    "code": "63000050",
    "name": "中正區"
  },
  "zip_code": "100",
  "street_address": "濟南路一段321號",
  "full_address": "100臺北市中正區濟南路一段321號",
  "telephones": [
    "(02)2322-6050"
  ],
  "website_url": "https://www.ntub.edu.tw",
  "service_time_info": null,
  "traffic_info": null,
  "parking_info": null,
  "fee_info": null,
  "service_status": 1,
  "service_status_label": "正常營運",
  "is_public_access": true,
  "is_free": true,
  "visit_duration": null,
  "assets_class": null,
  "assets_class_label": null,
  "tags": [
    "校園",
    "學習"
  ],
  "remarks": null,
  "categories": [
    {
      "id": 1,
      "name": "文化類"
    },
    {
      "id": 12,
      "name": "遊憩類"
    }
  ],
  "images": [],
  "review_count": 0,
  "average_rating": null,
  "source_update_time": null,
  "created_at": "2026-09-26T10:32:30",
  "updated_at": "2026-09-26T10:32:30"
}
```

<a id="9"></a>
## 9. 重複新增相同 ID（衝突）

**Request**

```http
POST /api/v1/attractions
Content-Type: application/json

{
  "id": "Attraction_DEMO_0001",
  "name": "國立臺北商業大學",
  "description": "位於臺北市中正區的商業大學，鄰近華山文創園區。",
  "latitude": 25.0421,
  "longitude": 121.5253,
  "city_code": "63000",
  "town_code": "63000050",
  "zip_code": "100",
  "street_address": "濟南路一段321號",
  "telephones": [
    "(02)2322-6050"
  ],
  "website_url": "https://www.ntub.edu.tw",
  "is_free": true,
  "tags": [
    "校園",
    "學習"
  ],
  "category_ids": [
    1,
    12
  ]
}
```

**Response** — Status Code: `409`

```json
{
  "detail": "Attraction 'Attraction_DEMO_0001' 已存在"
}
```

<a id="10"></a>
## 10. 新增景點但縣市代碼不存在（驗證失敗）

**Request**

```http
POST /api/v1/attractions
Content-Type: application/json

{
  "name": "錯誤資料",
  "city_code": "00000"
}
```

**Response** — Status Code: `422`

```json
{
  "detail": "City '00000' 不存在"
}
```

<a id="11"></a>
## 11. 部分更新景點 (PATCH)

**Request**

```http
PATCH /api/v1/attractions/Attraction_DEMO_0001
Content-Type: application/json

{
  "visit_duration": 90,
  "tags": [
    "校園",
    "學習",
    "資訊"
  ]
}
```

**Response** — Status Code: `200`

```json
{
  "id": "Attraction_DEMO_0001",
  "name": "國立臺北商業大學",
  "description": "位於臺北市中正區的商業大學，鄰近華山文創園區。",
  "alternate_names": [],
  "latitude": 25.0421,
  "longitude": 121.5253,
  "city": {
    "code": "63000",
    "name": "臺北市"
  },
  "town": {
    "code": "63000050",
    "name": "中正區"
  },
  "zip_code": "100",
  "street_address": "濟南路一段321號",
  "full_address": "100臺北市中正區濟南路一段321號",
  "telephones": [
    "(02)2322-6050"
  ],
  "website_url": "https://www.ntub.edu.tw",
  "service_time_info": null,
  "traffic_info": null,
  "parking_info": null,
  "fee_info": null,
  "service_status": 1,
  "service_status_label": "正常營運",
  "is_public_access": true,
  "is_free": true,
  "visit_duration": 90,
  "assets_class": null,
  "assets_class_label": null,
  "tags": [
    "校園",
    "學習",
    "資訊"
  ],
  "remarks": null,
  "categories": [
    {
      "id": 1,
      "name": "文化類"
    },
    {
      "id": 12,
      "name": "遊憩類"
    }
  ],
  "images": [],
  "review_count": 0,
  "average_rating": null,
  "source_update_time": null,
  "created_at": "2026-09-26T10:32:30",
  "updated_at": "2026-09-26T10:32:30"
}
```

<a id="12"></a>
## 12. 整筆更新景點 (PUT)

**Request**

```http
PUT /api/v1/attractions/Attraction_DEMO_0001
Content-Type: application/json

{
  "name": "國立臺北商業大學（臺北校區）",
  "description": "位於臺北市中正區的商業大學，鄰近華山文創園區。",
  "latitude": 25.0421,
  "longitude": 121.5253,
  "city_code": "63000",
  "town_code": "63000050",
  "zip_code": "100",
  "street_address": "濟南路一段321號",
  "telephones": [
    "(02)2322-6050"
  ],
  "website_url": "https://www.ntub.edu.tw",
  "is_free": true,
  "tags": [
    "校園",
    "學習"
  ],
  "category_ids": [
    1,
    12
  ],
  "service_time_info": "週一至週五 08:00-22:00"
}
```

**Response** — Status Code: `200`

```json
{
  "id": "Attraction_DEMO_0001",
  "name": "國立臺北商業大學（臺北校區）",
  "description": "位於臺北市中正區的商業大學，鄰近華山文創園區。",
  "alternate_names": [],
  "latitude": 25.0421,
  "longitude": 121.5253,
  "city": {
    "code": "63000",
    "name": "臺北市"
  },
  "town": {
    "code": "63000050",
    "name": "中正區"
  },
  "zip_code": "100",
  "street_address": "濟南路一段321號",
  "full_address": "100臺北市中正區濟南路一段321號",
  "telephones": [
    "(02)2322-6050"
  ],
  "website_url": "https://www.ntub.edu.tw",
  "service_time_info": "週一至週五 08:00-22:00",
  "traffic_info": null,
  "parking_info": null,
  "fee_info": null,
  "service_status": 1,
  "service_status_label": "正常營運",
  "is_public_access": true,
  "is_free": true,
  "visit_duration": null,
  "assets_class": null,
  "assets_class_label": null,
  "tags": [
    "校園",
    "學習"
  ],
  "remarks": null,
  "categories": [
    {
      "id": 1,
      "name": "文化類"
    },
    {
      "id": 12,
      "name": "遊憩類"
    }
  ],
  "images": [],
  "review_count": 0,
  "average_rating": null,
  "source_update_time": null,
  "created_at": "2026-09-26T10:32:30",
  "updated_at": "2026-09-26T10:32:30"
}
```

<a id="13"></a>
## 13. 列出景點圖片

**Request**

```http
GET /api/v1/attractions/Attraction_DEMO_0001/images
```

**Response** — Status Code: `200`

```json
[]
```

<a id="14"></a>
## 14. 新增景點圖片

**Request**

```http
POST /api/v1/attractions/Attraction_DEMO_0001/images
Content-Type: application/json

{
  "url": "https://www.ntub.edu.tw/images/campus.jpg",
  "name": "校門口"
}
```

**Response** — Status Code: `201`

```json
{
  "id": 10726,
  "attraction_id": "Attraction_DEMO_0001",
  "url": "https://www.ntub.edu.tw/images/campus.jpg",
  "name": "校門口",
  "description": null
}
```

<a id="15"></a>
## 15. 取得單張圖片

**Request**

```http
GET /api/v1/attractions/Attraction_DEMO_0001/images/10726
```

**Response** — Status Code: `200`

```json
{
  "id": 10726,
  "attraction_id": "Attraction_DEMO_0001",
  "url": "https://www.ntub.edu.tw/images/campus.jpg",
  "name": "校門口",
  "description": null
}
```

<a id="16"></a>
## 16. 部分更新圖片

**Request**

```http
PATCH /api/v1/attractions/Attraction_DEMO_0001/images/10726
Content-Type: application/json

{
  "description": "照片提供：學生"
}
```

**Response** — Status Code: `200`

```json
{
  "id": 10726,
  "attraction_id": "Attraction_DEMO_0001",
  "url": "https://www.ntub.edu.tw/images/campus.jpg",
  "name": "校門口",
  "description": "照片提供：學生"
}
```

<a id="17"></a>
## 17. 整筆更新圖片

**Request**

```http
PUT /api/v1/attractions/Attraction_DEMO_0001/images/10726
Content-Type: application/json

{
  "url": "https://www.ntub.edu.tw/images/campus2.jpg",
  "name": "校園"
}
```

**Response** — Status Code: `200`

```json
{
  "id": 10726,
  "attraction_id": "Attraction_DEMO_0001",
  "url": "https://www.ntub.edu.tw/images/campus2.jpg",
  "name": "校園",
  "description": null
}
```

<a id="18"></a>
## 18. 刪除圖片

**Request**

```http
DELETE /api/v1/attractions/Attraction_DEMO_0001/images/10726
```

**Response** — Status Code: `204`

（無內容）

<a id="19"></a>
## 19. 為景點新增評論（巢狀路徑）

**Request**

```http
POST /api/v1/attractions/Attraction_DEMO_0001/reviews
Content-Type: application/json

{
  "author": "小明",
  "rating": 5,
  "title": "很棒的學校",
  "content": "交通方便，環境舒適。",
  "visit_date": "2026-09-20"
}
```

**Response** — Status Code: `201`

```json
{
  "id": 1,
  "attraction_id": "Attraction_DEMO_0001",
  "attraction_name": "國立臺北商業大學（臺北校區）",
  "author": "小明",
  "rating": 5,
  "title": "很棒的學校",
  "content": "交通方便，環境舒適。",
  "visit_date": "2026-09-20",
  "created_at": "2026-09-26T10:32:31",
  "updated_at": "2026-09-26T10:32:31"
}
```

<a id="20"></a>
## 20. 新增評論（扁平路徑）

**Request**

```http
POST /api/v1/reviews
Content-Type: application/json

{
  "attraction_id": "Attraction_DEMO_0001",
  "author": "小華",
  "rating": 4,
  "title": "還不錯"
}
```

**Response** — Status Code: `201`

```json
{
  "id": 2,
  "attraction_id": "Attraction_DEMO_0001",
  "attraction_name": "國立臺北商業大學（臺北校區）",
  "author": "小華",
  "rating": 4,
  "title": "還不錯",
  "content": null,
  "visit_date": null,
  "created_at": "2026-09-26T10:32:31",
  "updated_at": "2026-09-26T10:32:31"
}
```

<a id="21"></a>
## 21. 新增評論但評分超出範圍（驗證失敗）

**Request**

```http
POST /api/v1/reviews
Content-Type: application/json

{
  "attraction_id": "Attraction_DEMO_0001",
  "author": "x",
  "rating": 6
}
```

**Response** — Status Code: `422`

```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": [
        "body",
        "rating"
      ],
      "msg": "Input should be less than or equal to 5",
      "input": 6,
      "ctx": {
        "le": 5
      }
    }
  ]
}
```

<a id="22"></a>
## 22. 查詢某景點的評論

**Request**

```http
GET /api/v1/attractions/Attraction_DEMO_0001/reviews
```

**Response** — Status Code: `200`

```json
{
  "total": 2,
  "page": 1,
  "page_size": 20,
  "pages": 1,
  "items": [
    {
      "id": 2,
      "attraction_id": "Attraction_DEMO_0001",
      "attraction_name": "國立臺北商業大學（臺北校區）",
      "author": "小華",
      "rating": 4,
      "title": "還不錯",
      "content": null,
      "visit_date": null,
      "created_at": "2026-09-26T10:32:31",
      "updated_at": "2026-09-26T10:32:31"
    },
    {
      "id": 1,
      "attraction_id": "Attraction_DEMO_0001",
      "attraction_name": "國立臺北商業大學（臺北校區）",
      "author": "小明",
      "rating": 5,
      "title": "很棒的學校",
      "content": "交通方便，環境舒適。",
      "visit_date": "2026-09-20",
      "created_at": "2026-09-26T10:32:31",
      "updated_at": "2026-09-26T10:32:31"
    }
  ]
}
```

<a id="23"></a>
## 23. 查詢 4 星以上的評論

**Request**

```http
GET /api/v1/reviews?min_rating=4&page_size=5
```

**Response** — Status Code: `200`

```json
{
  "total": 2,
  "page": 1,
  "page_size": 5,
  "pages": 1,
  "items": [
    {
      "id": 2,
      "attraction_id": "Attraction_DEMO_0001",
      "attraction_name": "國立臺北商業大學（臺北校區）",
      "author": "小華",
      "rating": 4,
      "title": "還不錯",
      "content": null,
      "visit_date": null,
      "created_at": "2026-09-26T10:32:31",
      "updated_at": "2026-09-26T10:32:31"
    },
    {
      "id": 1,
      "attraction_id": "Attraction_DEMO_0001",
      "attraction_name": "國立臺北商業大學（臺北校區）",
      "author": "小明",
      "rating": 5,
      "title": "很棒的學校",
      "content": "交通方便，環境舒適。",
      "visit_date": "2026-09-20",
      "created_at": "2026-09-26T10:32:31",
      "updated_at": "2026-09-26T10:32:31"
    }
  ]
}
```

<a id="24"></a>
## 24. 取得單一評論

**Request**

```http
GET /api/v1/reviews/1
```

**Response** — Status Code: `200`

```json
{
  "id": 1,
  "attraction_id": "Attraction_DEMO_0001",
  "attraction_name": "國立臺北商業大學（臺北校區）",
  "author": "小明",
  "rating": 5,
  "title": "很棒的學校",
  "content": "交通方便，環境舒適。",
  "visit_date": "2026-09-20",
  "created_at": "2026-09-26T10:32:31",
  "updated_at": "2026-09-26T10:32:31"
}
```

<a id="25"></a>
## 25. 部分更新評論

**Request**

```http
PATCH /api/v1/reviews/2
Content-Type: application/json

{
  "rating": 3,
  "content": "人有點多"
}
```

**Response** — Status Code: `200`

```json
{
  "id": 2,
  "attraction_id": "Attraction_DEMO_0001",
  "attraction_name": "國立臺北商業大學（臺北校區）",
  "author": "小華",
  "rating": 3,
  "title": "還不錯",
  "content": "人有點多",
  "visit_date": null,
  "created_at": "2026-09-26T10:32:31",
  "updated_at": "2026-09-26T10:32:31"
}
```

<a id="26"></a>
## 26. 整筆更新評論

**Request**

```http
PUT /api/v1/reviews/2
Content-Type: application/json

{
  "author": "小華",
  "rating": 4,
  "title": "改觀了"
}
```

**Response** — Status Code: `200`

```json
{
  "id": 2,
  "attraction_id": "Attraction_DEMO_0001",
  "attraction_name": "國立臺北商業大學（臺北校區）",
  "author": "小華",
  "rating": 4,
  "title": "改觀了",
  "content": null,
  "visit_date": null,
  "created_at": "2026-09-26T10:32:31",
  "updated_at": "2026-09-26T10:32:31"
}
```

<a id="27"></a>
## 27. 景點詳細資料（含平均評分）

**Request**

```http
GET /api/v1/attractions/Attraction_DEMO_0001
```

**Response** — Status Code: `200`

```json
{
  "id": "Attraction_DEMO_0001",
  "name": "國立臺北商業大學（臺北校區）",
  "description": "位於臺北市中正區的商業大學，鄰近華山文創園區。",
  "alternate_names": [],
  "latitude": 25.0421,
  "longitude": 121.5253,
  "city": {
    "code": "63000",
    "name": "臺北市"
  },
  "town": {
    "code": "63000050",
    "name": "中正區"
  },
  "zip_code": "100",
  "street_address": "濟南路一段321號",
  "full_address": "100臺北市中正區濟南路一段321號",
  "telephones": [
    "(02)2322-6050"
  ],
  "website_url": "https://www.ntub.edu.tw",
  "service_time_info": "週一至週五 08:00-22:00",
  "traffic_info": null,
  "parking_info": null,
  "fee_info": null,
  "service_status": 1,
  "service_status_label": "正常營運",
  "is_public_access": true,
  "is_free": true,
  "visit_duration": null,
  "assets_class": null,
  "assets_class_label": null,
  "tags": [
    "校園",
    "學習"
  ],
  "remarks": null,
  "categories": [
    {
      "id": 1,
      "name": "文化類"
    },
    {
      "id": 12,
      "name": "遊憩類"
    }
  ],
  "images": [],
  "review_count": 2,
  "average_rating": 4.5,
  "source_update_time": null,
  "created_at": "2026-09-26T10:32:30",
  "updated_at": "2026-09-26T10:32:30"
}
```

<a id="28"></a>
## 28. 評價最高的景點

**Request**

```http
GET /api/v1/stats/top-rated?limit=3
```

**Response** — Status Code: `200`

```json
[
  {
    "id": "Attraction_DEMO_0001",
    "name": "國立臺北商業大學（臺北校區）",
    "review_count": 2,
    "average_rating": 4.5
  }
]
```

<a id="29"></a>
## 29. 建立行程（同時加入行程項目）

**Request**

```http
POST /api/v1/trips
Content-Type: application/json

{
  "title": "臺北一日遊",
  "owner": "小明",
  "start_date": "2026-10-10",
  "end_date": "2026-10-10",
  "items": [
    {
      "attraction_id": "Attraction_DEMO_0001",
      "day": 1,
      "sequence": 1,
      "note": "上午集合"
    }
  ]
}
```

**Response** — Status Code: `201`

```json
{
  "id": 1,
  "title": "臺北一日遊",
  "description": null,
  "owner": "小明",
  "start_date": "2026-10-10",
  "end_date": "2026-10-10",
  "item_count": 1,
  "items": [
    {
      "id": 1,
      "trip_id": 1,
      "day": 1,
      "sequence": 1,
      "note": "上午集合",
      "attraction": {
        "id": "Attraction_DEMO_0001",
        "name": "國立臺北商業大學（臺北校區）",
        "city": {
          "code": "63000",
          "name": "臺北市"
        },
        "town": {
          "code": "63000050",
          "name": "中正區"
        },
        "categories": [
          {
            "id": 1,
            "name": "文化類"
          },
          {
            "id": 12,
            "name": "遊憩類"
          }
        ],
        "latitude": 25.0421,
        "longitude": 121.5253,
        "is_free": true,
        "service_status": 1,
        "cover_image": null
      }
    }
  ],
  "created_at": "2026-09-26T10:32:31",
  "updated_at": "2026-09-26T10:32:31"
}
```

<a id="30"></a>
## 30. 行程加入景點

**Request**

```http
POST /api/v1/trips/1/items
Content-Type: application/json

{
  "attraction_id": "Attraction_DEMO_0001",
  "day": 1,
  "sequence": 2,
  "note": "步行前往"
}
```

**Response** — Status Code: `201`

```json
{
  "id": 2,
  "trip_id": 1,
  "day": 1,
  "sequence": 2,
  "note": "步行前往",
  "attraction": {
    "id": "Attraction_DEMO_0001",
    "name": "國立臺北商業大學（臺北校區）",
    "city": {
      "code": "63000",
      "name": "臺北市"
    },
    "town": {
      "code": "63000050",
      "name": "中正區"
    },
    "categories": [
      {
        "id": 1,
        "name": "文化類"
      },
      {
        "id": 12,
        "name": "遊憩類"
      }
    ],
    "latitude": 25.0421,
    "longitude": 121.5253,
    "is_free": true,
    "service_status": 1,
    "cover_image": null
  }
}
```

<a id="31"></a>
## 31. 列出行程項目

**Request**

```http
GET /api/v1/trips/1/items
```

**Response** — Status Code: `200`

```json
[
  {
    "id": 1,
    "trip_id": 1,
    "day": 1,
    "sequence": 1,
    "note": "上午集合",
    "attraction": {
      "id": "Attraction_DEMO_0001",
      "name": "國立臺北商業大學（臺北校區）",
      "city": {
        "code": "63000",
        "name": "臺北市"
      },
      "town": {
        "code": "63000050",
        "name": "中正區"
      },
      "categories": [
        {
          "id": 1,
          "name": "文化類"
        },
        {
          "id": 12,
          "name": "遊憩類"
        }
      ],
      "latitude": 25.0421,
      "longitude": 121.5253,
      "is_free": true,
      "service_status": 1,
      "cover_image": null
    }
  },
  {
    "id": 2,
    "trip_id": 1,
    "day": 1,
    "sequence": 2,
    "note": "步行前往",
    "attraction": {
      "id": "Attraction_DEMO_0001",
      "name": "國立臺北商業大學（臺北校區）",
      "city": {
        "code": "63000",
        "name": "臺北市"
      },
      "town": {
        "code": "63000050",
        "name": "中正區"
      },
      "categories": [
        {
          "id": 1,
          "name": "文化類"
        },
        {
          "id": 12,
          "name": "遊憩類"
        }
      ],
      "latitude": 25.0421,
      "longitude": 121.5253,
      "is_free": true,
      "service_status": 1,
      "cover_image": null
    }
  }
]
```

<a id="32"></a>
## 32. 取得單一行程項目

**Request**

```http
GET /api/v1/trips/1/items/2
```

**Response** — Status Code: `200`

```json
{
  "id": 2,
  "trip_id": 1,
  "day": 1,
  "sequence": 2,
  "note": "步行前往",
  "attraction": {
    "id": "Attraction_DEMO_0001",
    "name": "國立臺北商業大學（臺北校區）",
    "city": {
      "code": "63000",
      "name": "臺北市"
    },
    "town": {
      "code": "63000050",
      "name": "中正區"
    },
    "categories": [
      {
        "id": 1,
        "name": "文化類"
      },
      {
        "id": 12,
        "name": "遊憩類"
      }
    ],
    "latitude": 25.0421,
    "longitude": 121.5253,
    "is_free": true,
    "service_status": 1,
    "cover_image": null
  }
}
```

<a id="33"></a>
## 33. 部分更新行程項目

**Request**

```http
PATCH /api/v1/trips/1/items/2
Content-Type: application/json

{
  "note": "午餐後前往"
}
```

**Response** — Status Code: `200`

```json
{
  "id": 2,
  "trip_id": 1,
  "day": 1,
  "sequence": 2,
  "note": "午餐後前往",
  "attraction": {
    "id": "Attraction_DEMO_0001",
    "name": "國立臺北商業大學（臺北校區）",
    "city": {
      "code": "63000",
      "name": "臺北市"
    },
    "town": {
      "code": "63000050",
      "name": "中正區"
    },
    "categories": [
      {
        "id": 1,
        "name": "文化類"
      },
      {
        "id": 12,
        "name": "遊憩類"
      }
    ],
    "latitude": 25.0421,
    "longitude": 121.5253,
    "is_free": true,
    "service_status": 1,
    "cover_image": null
  }
}
```

<a id="34"></a>
## 34. 整筆更新行程項目

**Request**

```http
PUT /api/v1/trips/1/items/2
Content-Type: application/json

{
  "attraction_id": "Attraction_DEMO_0001",
  "day": 1,
  "sequence": 3
}
```

**Response** — Status Code: `200`

```json
{
  "id": 2,
  "trip_id": 1,
  "day": 1,
  "sequence": 3,
  "note": null,
  "attraction": {
    "id": "Attraction_DEMO_0001",
    "name": "國立臺北商業大學（臺北校區）",
    "city": {
      "code": "63000",
      "name": "臺北市"
    },
    "town": {
      "code": "63000050",
      "name": "中正區"
    },
    "categories": [
      {
        "id": 1,
        "name": "文化類"
      },
      {
        "id": 12,
        "name": "遊憩類"
      }
    ],
    "latitude": 25.0421,
    "longitude": 121.5253,
    "is_free": true,
    "service_status": 1,
    "cover_image": null
  }
}
```

<a id="35"></a>
## 35. 部分更新行程

**Request**

```http
PATCH /api/v1/trips/1
Content-Type: application/json

{
  "description": "北商大周邊散步"
}
```

**Response** — Status Code: `200`

```json
{
  "id": 1,
  "title": "臺北一日遊",
  "description": "北商大周邊散步",
  "owner": "小明",
  "start_date": "2026-10-10",
  "end_date": "2026-10-10",
  "item_count": 2,
  "items": [
    {
      "id": 1,
      "trip_id": 1,
      "day": 1,
      "sequence": 1,
      "note": "上午集合",
      "attraction": {
        "id": "Attraction_DEMO_0001",
        "name": "國立臺北商業大學（臺北校區）",
        "city": {
          "code": "63000",
          "name": "臺北市"
        },
        "town": {
          "code": "63000050",
          "name": "中正區"
        },
        "categories": [
          {
            "id": 1,
            "name": "文化類"
          },
          {
            "id": 12,
            "name": "遊憩類"
          }
        ],
        "latitude": 25.0421,
        "longitude": 121.5253,
        "is_free": true,
        "service_status": 1,
        "cover_image": null
      }
    },
    {
      "id": 2,
      "trip_id": 1,
      "day": 1,
      "sequence": 3,
      "note": null,
      "attraction": {
        "id": "Attraction_DEMO_0001",
        "name": "國立臺北商業大學（臺北校區）",
        "city": {
          "code": "63000",
          "name": "臺北市"
        },
        "town": {
          "code": "63000050",
          "name": "中正區"
        },
        "categories": [
          {
            "id": 1,
            "name": "文化類"
          },
          {
            "id": 12,
            "name": "遊憩類"
          }
        ],
        "latitude": 25.0421,
        "longitude": 121.5253,
        "is_free": true,
        "service_status": 1,
        "cover_image": null
      }
    }
  ],
  "created_at": "2026-09-26T10:32:31",
  "updated_at": "2026-09-26T10:32:31"
}
```

<a id="36"></a>
## 36. 行程日期錯誤（驗證失敗）

**Request**

```http
PATCH /api/v1/trips/1
Content-Type: application/json

{
  "end_date": "2026-10-01"
}
```

**Response** — Status Code: `422`

```json
{
  "detail": "end_date 不可早於 start_date"
}
```

<a id="37"></a>
## 37. 取得行程（含項目）

**Request**

```http
GET /api/v1/trips/1
```

**Response** — Status Code: `200`

```json
{
  "id": 1,
  "title": "臺北一日遊",
  "description": "北商大周邊散步",
  "owner": "小明",
  "start_date": "2026-10-10",
  "end_date": "2026-10-10",
  "item_count": 2,
  "items": [
    {
      "id": 1,
      "trip_id": 1,
      "day": 1,
      "sequence": 1,
      "note": "上午集合",
      "attraction": {
        "id": "Attraction_DEMO_0001",
        "name": "國立臺北商業大學（臺北校區）",
        "city": {
          "code": "63000",
          "name": "臺北市"
        },
        "town": {
          "code": "63000050",
          "name": "中正區"
        },
        "categories": [
          {
            "id": 1,
            "name": "文化類"
          },
          {
            "id": 12,
            "name": "遊憩類"
          }
        ],
        "latitude": 25.0421,
        "longitude": 121.5253,
        "is_free": true,
        "service_status": 1,
        "cover_image": null
      }
    },
    {
      "id": 2,
      "trip_id": 1,
      "day": 1,
      "sequence": 3,
      "note": null,
      "attraction": {
        "id": "Attraction_DEMO_0001",
        "name": "國立臺北商業大學（臺北校區）",
        "city": {
          "code": "63000",
          "name": "臺北市"
        },
        "town": {
          "code": "63000050",
          "name": "中正區"
        },
        "categories": [
          {
            "id": 1,
            "name": "文化類"
          },
          {
            "id": 12,
            "name": "遊憩類"
          }
        ],
        "latitude": 25.0421,
        "longitude": 121.5253,
        "is_free": true,
        "service_status": 1,
        "cover_image": null
      }
    }
  ],
  "created_at": "2026-09-26T10:32:31",
  "updated_at": "2026-09-26T10:32:31"
}
```

<a id="38"></a>
## 38. 列出行程

**Request**

```http
GET /api/v1/trips?owner=小明
```

**Response** — Status Code: `200`

```json
{
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1,
  "items": [
    {
      "id": 1,
      "title": "臺北一日遊",
      "owner": "小明",
      "start_date": "2026-10-10",
      "end_date": "2026-10-10",
      "item_count": 2
    }
  ]
}
```

<a id="39"></a>
## 39. 刪除行程項目

**Request**

```http
DELETE /api/v1/trips/1/items/2
```

**Response** — Status Code: `204`

（無內容）

<a id="40"></a>
## 40. 整筆更新行程 (PUT)

**Request**

```http
PUT /api/v1/trips/1
Content-Type: application/json

{
  "title": "臺北半日遊",
  "owner": "小明",
  "items": []
}
```

**Response** — Status Code: `200`

```json
{
  "id": 1,
  "title": "臺北半日遊",
  "description": null,
  "owner": "小明",
  "start_date": null,
  "end_date": null,
  "item_count": 0,
  "items": [],
  "created_at": "2026-09-26T10:32:31",
  "updated_at": "2026-09-26T10:32:31"
}
```

<a id="41"></a>
## 41. 刪除行程

**Request**

```http
DELETE /api/v1/trips/1
```

**Response** — Status Code: `204`

（無內容）

<a id="42"></a>
## 42. 列出景點類型

**Request**

```http
GET /api/v1/categories?page_size=5
```

**Response** — Status Code: `200`

```json
{
  "total": 28,
  "page": 1,
  "page_size": 5,
  "pages": 6,
  "items": [
    {
      "id": 1,
      "name": "文化類",
      "description": "提供旅客文化相關內涵之場域。",
      "attraction_count": 1865
    },
    {
      "id": 2,
      "name": "生態類",
      "description": "提供旅客生態相關內涵之場域。",
      "attraction_count": 891
    },
    {
      "id": 3,
      "name": "文化資產類",
      "description": "古蹟、歷史建築、紀念建築、聚落建築群、考古遺址、史蹟、古物、文化景觀、自然地景等。",
      "attraction_count": 777
    },
    "...（其餘 2 筆省略）"
  ]
}
```

<a id="43"></a>
## 43. 取得單一景點類型

**Request**

```http
GET /api/v1/categories/16
```

**Response** — Status Code: `200`

```json
{
  "id": 16,
  "name": "森林遊樂區類",
  "description": "太平山、阿里山、墾丁、知本等國家森林遊樂區。",
  "attraction_count": 47
}
```

<a id="44"></a>
## 44. 新增景點類型

**Request**

```http
POST /api/v1/categories
Content-Type: application/json

{
  "id": 900,
  "name": "校園類",
  "description": "大專院校校園"
}
```

**Response** — Status Code: `201`

```json
{
  "id": 900,
  "name": "校園類",
  "description": "大專院校校園",
  "attraction_count": 0
}
```

<a id="45"></a>
## 45. 部分更新景點類型

**Request**

```http
PATCH /api/v1/categories/900
Content-Type: application/json

{
  "description": "大學與技職校園"
}
```

**Response** — Status Code: `200`

```json
{
  "id": 900,
  "name": "校園類",
  "description": "大學與技職校園",
  "attraction_count": 0
}
```

<a id="46"></a>
## 46. 整筆更新景點類型

**Request**

```http
PUT /api/v1/categories/900
Content-Type: application/json

{
  "name": "學校校園類",
  "description": "各級學校"
}
```

**Response** — Status Code: `200`

```json
{
  "id": 900,
  "name": "學校校園類",
  "description": "各級學校",
  "attraction_count": 0
}
```

<a id="47"></a>
## 47. 刪除景點類型

**Request**

```http
DELETE /api/v1/categories/900
```

**Response** — Status Code: `204`

（無內容）

<a id="48"></a>
## 48. 列出縣市

**Request**

```http
GET /api/v1/cities?page_size=5
```

**Response** — Status Code: `200`

```json
{
  "total": 22,
  "page": 1,
  "page_size": 5,
  "pages": 5,
  "items": [
    {
      "code": "09007",
      "name": "連江縣",
      "town_count": 4,
      "attraction_count": 84
    },
    {
      "code": "09020",
      "name": "金門縣",
      "town_count": 5,
      "attraction_count": 224
    },
    {
      "code": "10002",
      "name": "宜蘭縣",
      "town_count": 12,
      "attraction_count": 173
    },
    "...（其餘 2 筆省略）"
  ]
}
```

<a id="49"></a>
## 49. 取得單一縣市

**Request**

```http
GET /api/v1/cities/63000
```

**Response** — Status Code: `200`

```json
{
  "code": "63000",
  "name": "臺北市",
  "town_count": 12,
  "attraction_count": 433
}
```

<a id="50"></a>
## 50. 列出臺北市的行政區

**Request**

```http
GET /api/v1/cities/63000/towns
```

**Response** — Status Code: `200`

```json
[
  {
    "code": "63000010",
    "name": "松山區",
    "city_code": "63000",
    "city_name": "臺北市",
    "attraction_count": 14
  },
  {
    "code": "63000020",
    "name": "信義區",
    "city_code": "63000",
    "city_name": "臺北市",
    "attraction_count": 27
  },
  {
    "code": "63000030",
    "name": "大安區",
    "city_code": "63000",
    "city_name": "臺北市",
    "attraction_count": 29
  },
  "...（其餘 9 筆省略）"
]
```

<a id="51"></a>
## 51. 新增縣市

**Request**

```http
POST /api/v1/cities
Content-Type: application/json

{
  "code": "99001",
  "name": "示範市"
}
```

**Response** — Status Code: `201`

```json
{
  "code": "99001",
  "name": "示範市",
  "town_count": 0,
  "attraction_count": 0
}
```

<a id="52"></a>
## 52. 新增鄉鎮市區

**Request**

```http
POST /api/v1/towns
Content-Type: application/json

{
  "code": "99001010",
  "name": "示範區",
  "city_code": "99001"
}
```

**Response** — Status Code: `201`

```json
{
  "code": "99001010",
  "name": "示範區",
  "city_code": "99001",
  "city_name": "示範市",
  "attraction_count": 0
}
```

<a id="53"></a>
## 53. 查詢鄉鎮市區（依縣市）

**Request**

```http
GET /api/v1/towns?city_code=99001
```

**Response** — Status Code: `200`

```json
{
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1,
  "items": [
    {
      "code": "99001010",
      "name": "示範區",
      "city_code": "99001",
      "city_name": "示範市",
      "attraction_count": 0
    }
  ]
}
```

<a id="54"></a>
## 54. 取得單一鄉鎮市區

**Request**

```http
GET /api/v1/towns/99001010
```

**Response** — Status Code: `200`

```json
{
  "code": "99001010",
  "name": "示範區",
  "city_code": "99001",
  "city_name": "示範市",
  "attraction_count": 0
}
```

<a id="55"></a>
## 55. 部分更新鄉鎮市區

**Request**

```http
PATCH /api/v1/towns/99001010
Content-Type: application/json

{
  "name": "示範新區"
}
```

**Response** — Status Code: `200`

```json
{
  "code": "99001010",
  "name": "示範新區",
  "city_code": "99001",
  "city_name": "示範市",
  "attraction_count": 0
}
```

<a id="56"></a>
## 56. 整筆更新鄉鎮市區

**Request**

```http
PUT /api/v1/towns/99001010
Content-Type: application/json

{
  "code": "99001010",
  "name": "示範東區",
  "city_code": "99001"
}
```

**Response** — Status Code: `200`

```json
{
  "code": "99001010",
  "name": "示範東區",
  "city_code": "99001",
  "city_name": "示範市",
  "attraction_count": 0
}
```

<a id="57"></a>
## 57. 更新縣市 (PUT)

**Request**

```http
PUT /api/v1/cities/99001
Content-Type: application/json

{
  "name": "示範新市"
}
```

**Response** — Status Code: `200`

```json
{
  "code": "99001",
  "name": "示範新市",
  "town_count": 1,
  "attraction_count": 0
}
```

<a id="58"></a>
## 58. 刪除仍有景點的縣市（衝突）

**Request**

```http
DELETE /api/v1/cities/63000
```

**Response** — Status Code: `409`

```json
{
  "detail": "仍有 433 個景點位於 臺北市，如要刪除請加上 ?force=true"
}
```

<a id="59"></a>
## 59. 刪除鄉鎮市區

**Request**

```http
DELETE /api/v1/towns/99001010
```

**Response** — Status Code: `204`

（無內容）

<a id="60"></a>
## 60. 刪除縣市

**Request**

```http
DELETE /api/v1/cities/99001
```

**Response** — Status Code: `204`

（無內容）

<a id="61"></a>
## 61. 資料總覽

**Request**

```http
GET /api/v1/stats/overview
```

**Response** — Status Code: `200`

```json
{
  "attractions": 6227,
  "free_attractions": 271,
  "attractions_with_images": 6226,
  "cities": 22,
  "towns": 348,
  "categories": 28,
  "images": 10725,
  "reviews": 2,
  "trips": 0,
  "by_service_status": [
    {
      "key": "0",
      "name": "永久停止",
      "count": 82
    },
    {
      "key": "1",
      "name": "正常營運",
      "count": 6065
    },
    {
      "key": "3",
      "name": "暫時停止營運",
      "count": 80
    }
  ],
  "data_source": "交通部觀光署 景點 - 觀光資訊資料庫 (https://data.gov.tw/dataset/7777)",
  "data_update_time": "2026-09-26T14:30:03+08:00"
}
```

<a id="62"></a>
## 62. 各縣市景點數

**Request**

```http
GET /api/v1/stats/cities
```

**Response** — Status Code: `200`

```json
[
  {
    "key": "65000",
    "name": "新北市",
    "count": 661
  },
  {
    "key": "67000",
    "name": "臺南市",
    "count": 545
  },
  {
    "key": "10004",
    "name": "新竹縣",
    "count": 509
  },
  "...（其餘 19 筆省略）"
]
```

<a id="63"></a>
## 63. 各類型景點數

**Request**

```http
GET /api/v1/stats/categories
```

**Response** — Status Code: `200`

```json
[
  {
    "key": "1",
    "name": "文化類",
    "count": 1865
  },
  {
    "key": "12",
    "name": "遊憩類",
    "count": 1696
  },
  {
    "key": "2",
    "name": "生態類",
    "count": 891
  },
  "...（其餘 25 筆省略）"
]
```

<a id="64"></a>
## 64. 刪除景點（連同評論一併刪除）

**Request**

```http
DELETE /api/v1/attractions/Attraction_DEMO_0001
```

**Response** — Status Code: `204`

（無內容）

<a id="65"></a>
## 65. 確認景點已刪除

**Request**

```http
GET /api/v1/attractions/Attraction_DEMO_0001
```

**Response** — Status Code: `404`

```json
{
  "detail": "Attraction 'Attraction_DEMO_0001' 不存在"
}
```

<a id="66"></a>
## 66. 確認評論已連帶刪除

**Request**

```http
GET /api/v1/reviews/1
```

**Response** — Status Code: `404`

```json
{
  "detail": "Review '1' 不存在"
}
```
